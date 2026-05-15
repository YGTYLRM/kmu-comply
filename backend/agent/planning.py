"""
Steps 2-5 of the analysis pipeline.

  determine_applicability(profile)                     — Step 2: threshold check
  retrieve_regulatory_context(profile, applicability)  — Step 3: RAG per regulation
  run_gap_analysis(profile, chunks, failures)          — Step 4: LLM gap analysis
  generate_action_plan(profile, gaps, failures)        — Step 5: LLM action plan
"""
import json
import logging
from functools import lru_cache

import anthropic

from config import settings
from models.company_profile import EnrichedCompanyProfile
from models.compliance_report import (
    ActionItem,
    ComplianceGap,
    RegulationApplicability,
    RegulatoryChunk,
)
from models.enums import ComplianceStatus, ObligationType, Priority, Regulation
from rag.company_ingest import retrieve_company_docs
from rag.prompts import SYSTEM_PERSONA, action_plan_prompt, gap_analysis_prompt
from rag.retrieval import deduplicate, retrieve
from services.threshold_engine import determine_applicable_regulations

logger = logging.getLogger(__name__)

_PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}


@lru_cache(maxsize=1)
def _llm_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.llm_api_key)


# ── Step 2 ────────────────────────────────────────────────────────────────────

def determine_applicability(
    profile: EnrichedCompanyProfile,
) -> list[RegulationApplicability]:
    """Deterministic regulation applicability — never delegates to an LLM."""
    return determine_applicable_regulations(profile)


# ── Step 3 ────────────────────────────────────────────────────────────────────

def retrieve_regulatory_context(
    profile: EnrichedCompanyProfile,
    applicability: list[RegulationApplicability],
) -> list[RegulatoryChunk]:
    """RAG retrieval for each applicable regulation, deduplicated and capped per-regulation.

    Each applicable regulation is retrieved and capped independently so that
    no single regulation can crowd out others during a global rerank step.
    """
    applicable = [a for a in applicability if a.applies]
    if not applicable:
        return []

    all_chunks: list[RegulatoryChunk] = []

    for reg_app in applicable:
        reg_key = reg_app.regulation.value
        query = _build_query(profile, reg_app.regulation)
        raw = retrieve(query, [reg_key], top_k=15)

        if len(raw) < 5:
            broader = f"{reg_key} compliance obligations requirements Germany SME"
            raw = retrieve(broader, [reg_key], top_k=15)
            if len(raw) < 5:
                logger.warning(
                    "step 3: only %d chunks for %s after retry (expected >= 5)",
                    len(raw), reg_key,
                )

        deduped = deduplicate(raw)
        top = deduped[:5]
        all_chunks.extend(_to_models(top))
        logger.debug("step 3: %s — %d chunks selected", reg_key, len(top))

    return all_chunks


# ── Step 4 ────────────────────────────────────────────────────────────────────

def run_gap_analysis(
    profile: EnrichedCompanyProfile,
    chunks: list[RegulatoryChunk],
    failures: list[str],
    job_id: str = "",
) -> list[ComplianceGap]:
    """LLM gap analysis, processed per regulation. Includes company doc evidence when available."""
    by_reg: dict[str, list[RegulatoryChunk]] = {}
    for chunk in chunks:
        by_reg.setdefault(chunk.regulation.value, []).append(chunk)

    profile_json = profile.model_dump_json(indent=2)
    all_gaps: list[ComplianceGap] = []

    for reg_key, reg_chunks in by_reg.items():
        chunks_json = _chunks_to_json(reg_chunks)

        # Retrieve company doc evidence for this regulation
        company_docs_json = ""
        if job_id:
            query = _build_query(profile, _reg_from_key(reg_key))
            doc_chunks = retrieve_company_docs(job_id, query, top_k=6)
            if doc_chunks:
                company_docs_json = _doc_chunks_to_json(doc_chunks)

        prompt = gap_analysis_prompt(
            profile_json, chunks_json, company_docs_json,
            inferred_assumptions=getattr(profile, "inferred_assumptions", []),
        )
        gaps = _llm_call(prompt, _parse_gaps, f"gap_analysis:{reg_key}", failures)
        all_gaps.extend(gaps)

    return all_gaps


# ── Step 5 ────────────────────────────────────────────────────────────────────

def generate_action_plan(
    profile: EnrichedCompanyProfile,
    gaps: list[ComplianceGap],
    failures: list[str],
) -> list[ActionItem]:
    """LLM action plan for every NON_COMPLIANT and PARTIALLY_COMPLIANT gap."""
    actionable = [
        g for g in gaps
        if g.status in (ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT)
    ]
    if not actionable:
        return []

    profile_json = profile.model_dump_json(indent=2)
    gaps_json = json.dumps([g.model_dump() for g in actionable], indent=2, default=str)
    prompt = action_plan_prompt(profile_json, gaps_json)
    actions = _llm_call(prompt, _parse_actions, "action_plan", failures, max_tokens=8192)

    return sorted(actions, key=lambda a: _PRIORITY_ORDER.get(a.priority, 4))


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_query(profile: EnrichedCompanyProfile, regulation: Regulation) -> str:
    base = f"{profile.industry} company {profile.employee_count} employees Germany"
    if regulation == Regulation.GDPR:
        extras = []
        if profile.processes_special_category_data:
            extras.append("special category data Art. 9")
        if not profile.has_processing_records:
            extras.append("records of processing activities Art. 30")
        if not profile.has_dpo:
            extras.append("data protection officer")
        return f"GDPR DSGVO compliance obligations {base} {' '.join(extras)}"
    if regulation == Regulation.LKSG:
        countries = (
            ", ".join(profile.supply_chain_countries[:5])
            if profile.supply_chain_countries
            else "abroad"
        )
        return f"LkSG supply chain due diligence {base} suppliers {countries}"
    if regulation == Regulation.ENEFG:
        energy = (
            f"{profile.annual_energy_consumption_mwh} MWh"
            if profile.annual_energy_consumption_mwh
            else ""
        )
        return f"EnEfG energy efficiency audit management {base} {energy}"
    if regulation == Regulation.CSRD:
        return f"CSRD sustainability reporting ESG disclosure {base}"
    if regulation == Regulation.BDSG:
        return f"BDSG Bundesdatenschutzgesetz data protection {base}"
    if regulation == Regulation.NIS2:
        entity = "besonders wichtige Einrichtung" if profile.employee_count >= 250 else "wichtige Einrichtung"
        return f"NIS2 BSIG cybersecurity risk management incident reporting {entity} {base}"
    if regulation == Regulation.AI_ACT:
        return f"EU AI Act high-risk AI system deployer transparency human oversight obligations {base}"
    if regulation == Regulation.HINSCHG:
        return f"HinSchG Hinweisgeberschutzgesetz whistleblower internal reporting channel {base}"
    if regulation == Regulation.ARBSCHG:
        return (
            f"ArbSchG ArbZG MuSchG JArbSchG BUrlG BBiG AEntG workplace law "
            f"Gefaehrdungsbeurteilung risk assessment working time employee protection {base}"
        )
    if regulation == Regulation.AGG:
        return f"AGG Gleichbehandlung anti-discrimination employer obligations complaints {base}"
    if regulation == Regulation.MILOG:
        return f"MiLoG Mindestlohn minimum wage documentation working time records {base}"
    return f"{regulation.value} compliance obligations {base}"


_REG_ALIASES: dict[str, str] = {
    "gdpr": "gdpr_dsgvo",  # ChromaDB metadata uses short key; enum uses full key
}


def _to_models(chunks: list[dict]) -> list[RegulatoryChunk]:
    result = []
    for c in chunks:
        try:
            raw_applicable = c.get("applicable_to", [])
            if isinstance(raw_applicable, str):
                try:
                    raw_applicable = json.loads(raw_applicable)
                except json.JSONDecodeError:
                    raw_applicable = [raw_applicable] if raw_applicable else []

            reg_val = c.get("regulation", "")
            reg_val = _REG_ALIASES.get(reg_val, reg_val)

            # Normalise ObligationType: fall back to MUST for unknown values
            ob_raw = c.get("obligation_type", ObligationType.MUST.value)
            try:
                ob_type = ObligationType(ob_raw)
            except ValueError:
                ob_type = ObligationType.MUST

            result.append(RegulatoryChunk(
                regulation=Regulation(reg_val),
                article_number=c.get("article_number", ""),
                title=c.get("title", ""),
                text=c.get("text", ""),
                obligation_type=ob_type,
                applicable_to=raw_applicable,
                threshold=c.get("threshold"),
                source_url=c.get("source_url"),
                document_type=c.get("document_type", "law"),
            ))
        except Exception as exc:
            logger.warning("could not parse retrieval chunk: %s", exc)
    return result


def _reg_from_key(reg_key: str) -> Regulation:
    try:
        return Regulation(reg_key)
    except ValueError:
        return Regulation.GDPR  # safe fallback


def _doc_chunks_to_json(chunks: list[dict]) -> str:
    from rag.prompts import _sanitize
    parts = []
    for c in chunks:
        safe_text   = _sanitize(c.get("text", ""), max_len=800)
        safe_source = _sanitize(c.get("source", "uploaded document"), max_len=100)
        parts.append(
            f"[Level 3 — Company document (evidence only, not legal authority) | "
            f"Source: {safe_source}]\n{safe_text}"
        )
    return "\n\n---\n\n".join(parts)


_SOURCE_AUTHORITY: dict[str, str] = {
    "law":      "Level 1 — Official law text (binding)",
    "guidance": "Level 2 — Regulatory guidance (authoritative interpretation)",
}


def _chunks_to_json(chunks: list[RegulatoryChunk]) -> str:
    return json.dumps(
        [
            {
                "source_authority": _SOURCE_AUTHORITY.get(c.document_type, "Level 1 — Official law text (binding)"),
                "regulation": c.regulation.value,
                "article_number": c.article_number,
                "title": c.title,
                "text": c.text[:2000],
                "obligation_type": c.obligation_type.value,
                "threshold": c.threshold,
            }
            for c in chunks
        ],
        indent=2,
    )


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that some models wrap JSON in."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop opening fence line and closing fence line
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[start:end]).strip()
    return text


def _llm_call(
    prompt: str,
    parse_fn,
    step_name: str,
    failures: list[str],
    max_tokens: int = 4096,
) -> list:
    import time
    if not settings.llm_api_key:
        logger.warning("%s: no LLM API key configured, skipping", step_name)
        failures.append(step_name)
        return []

    last_exc: Exception | None = None
    max_attempts = settings.llm_max_retries + 1  # default: 5 total (4 retries)
    for attempt in range(max_attempts):
        try:
            response = _llm_client().messages.create(
                model=settings.llm_model,
                max_tokens=max_tokens,
                temperature=0,
                system=SYSTEM_PERSONA,
                messages=[{"role": "user", "content": prompt}],
            )
            return parse_fn(_strip_fences(response.content[0].text))
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("%s: parse error attempt %d/%d: %s", step_name, attempt + 1, max_attempts, exc)
            last_exc = exc
        except anthropic.APIError as exc:
            logger.warning("%s: API error attempt %d/%d: %s", step_name, attempt + 1, max_attempts, exc)
            last_exc = exc
        except Exception as exc:
            logger.warning("%s: unexpected error attempt %d/%d: %s", step_name, attempt + 1, max_attempts, exc)
            last_exc = exc

        if attempt < max_attempts - 1:
            backoff = 2 ** attempt  # 1s, 2s, 4s, 8s
            logger.info("%s: retrying in %ds", step_name, backoff)
            time.sleep(backoff)

    logger.error("%s: all %d attempts failed (%s)", step_name, max_attempts, last_exc)
    failures.append(step_name)
    return []


def _parse_gaps(text: str) -> list[ComplianceGap]:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError(f"expected JSON array, got {type(data).__name__}")
    return [
        ComplianceGap(
            regulation=Regulation(item["regulation"]),
            article_number=item["article_number"],
            article_title=item["article_title"],
            status=ComplianceStatus(item["status"]),
            evidence=item["evidence"],
            deficiency_description=item.get("deficiency_description"),
        )
        for item in data
    ]


def _parse_actions(text: str) -> list[ActionItem]:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError(f"expected JSON array, got {type(data).__name__}")
    return [
        ActionItem(
            regulation=Regulation(item["regulation"]),
            article_number=item["article_number"],
            action=item["action"],
            priority=Priority(item["priority"]),
            estimated_effort=item["estimated_effort"],
            deadline=item.get("deadline"),
            dependencies=item.get("dependencies", []),
            gap_reference=item["gap_reference"],
        )
        for item in data
    ]
