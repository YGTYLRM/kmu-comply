"""
Step 1: Profile validation and enrichment.

Validates a CompanyProfile, flags missing optional fields that affect compliance
assessment, and uses the LLM to infer implicit characteristics not explicitly stated.
Falls back to deterministic-only enrichment if the LLM is unavailable.
"""
import json
import logging
from functools import lru_cache

import anthropic

from config import settings
from models.company_profile import CompanyProfile, EnrichedCompanyProfile
from rag.prompts import SYSTEM_PERSONA, profile_enrichment_prompt

logger = logging.getLogger(__name__)

_OPTIONAL_FIELDS: list[tuple[str, str]] = [
    (
        "annual_revenue_eur",
        "Annual revenue not provided — CSRD and EnEfG applicability may be incomplete.",
    ),
    (
        "balance_sheet_total_eur",
        "Balance sheet total not provided — CSRD applicability may be incomplete.",
    ),
    (
        "annual_energy_consumption_mwh",
        "Energy consumption not provided — EnEfG energy management requirements cannot be fully assessed.",
    ),
]


@lru_cache(maxsize=1)
def _llm_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.llm_api_key)


def _deterministic_enrichment(
    profile: CompanyProfile,
) -> tuple[list[str], list[str]]:
    """Return (missing_fields, warnings) based on profile fields alone."""
    missing: list[str] = []
    warnings: list[str] = []
    for field, warning in _OPTIONAL_FIELDS:
        if getattr(profile, field) is None:
            missing.append(field)
            warnings.append(warning)
    return missing, warnings


def enrich_profile(profile: CompanyProfile) -> EnrichedCompanyProfile:
    """
    Enrich a validated CompanyProfile with inferred characteristics.

    Returns an EnrichedCompanyProfile. On LLM failure, returns the profile
    with deterministic-only enrichment and a warning — never raises.
    """
    missing, warnings = _deterministic_enrichment(profile)

    if not settings.llm_api_key:
        logger.warning("profiling: no LLM API key configured, returning deterministic enrichment only")
        return EnrichedCompanyProfile(
            **profile.model_dump(),
            inferred_characteristics=[],
            missing_optional_fields=missing,
            validation_warnings=warnings,
        )

    _TOOL_ENRICHMENT = {
        "name": "submit_profile_enrichment",
        "description": "Submit inferred company compliance characteristics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "inferred_characteristics": {"type": "array", "items": {"type": "string"}},
                "inferred_assumptions":     {"type": "array", "items": {"type": "string"}},
                "validation_warnings":      {"type": "array", "items": {"type": "string"}},
                "missing_optional_fields":  {"type": "array", "items": {"type": "string"}},
            },
            "required": ["inferred_characteristics","inferred_assumptions","validation_warnings","missing_optional_fields"],
        },
    }

    prompt = profile_enrichment_prompt(profile.model_dump_json(indent=2))
    last_exc: Exception | None = None

    import time
    max_attempts = settings.llm_max_retries + 1
    for attempt in range(max_attempts):
        try:
            response = _llm_client().messages.create(
                model=settings.llm_model,
                max_tokens=4096,
                temperature=0,
                system=SYSTEM_PERSONA,
                tools=[_TOOL_ENRICHMENT],
                tool_choice={"type": "tool", "name": "submit_profile_enrichment"},
                messages=[{"role": "user", "content": prompt}],
            )
            tool_block = next(
                (b for b in response.content if b.type == "tool_use"), None
            )
            if tool_block is None:
                raise ValueError("model did not return a tool_use block")
            data = tool_block.input

            llm_chars: list[str]       = data.get("inferred_characteristics", [])
            llm_assumptions: list[str] = data.get("inferred_assumptions", [])
            llm_warnings: list[str]    = data.get("validation_warnings", [])
            llm_missing: list[str]     = data.get("missing_optional_fields", [])

            merged_missing   = list(dict.fromkeys(missing + [f for f in llm_missing if f not in missing]))
            merged_warnings  = list(dict.fromkeys(warnings + [w for w in llm_warnings if w not in warnings]))

            return EnrichedCompanyProfile(
                **profile.model_dump(),
                inferred_characteristics=llm_chars,
                inferred_assumptions=llm_assumptions,
                missing_optional_fields=merged_missing,
                validation_warnings=merged_warnings,
            )

        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("profiling: parse error attempt %d/%d: %s", attempt + 1, max_attempts, exc)
            last_exc = exc
        except anthropic.APIError as exc:
            logger.warning("profiling: API error attempt %d/%d: %s", attempt + 1, max_attempts, exc)
            last_exc = exc
        except Exception as exc:
            logger.warning("profiling: unexpected error attempt %d/%d: %s", attempt + 1, max_attempts, exc)
            last_exc = exc
        if attempt < max_attempts - 1:
            time.sleep(2 ** attempt)

    logger.error("profiling: all %d attempts failed (%s), returning deterministic enrichment", max_attempts, last_exc)
    return EnrichedCompanyProfile(
        **profile.model_dump(),
        inferred_characteristics=[],
        missing_optional_fields=missing,
        validation_warnings=warnings + ["Automated profile enrichment failed — manual review recommended."],
    )
