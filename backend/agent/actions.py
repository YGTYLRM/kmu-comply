"""
Step 6: Report assembly and executive summary generation.
"""
import logging
from datetime import datetime, timezone
from functools import lru_cache

import anthropic

from config import settings
from models.company_profile import EnrichedCompanyProfile
from models.compliance_report import (
    ActionItem,
    ComplianceGap,
    ComplianceReport,
    RegulationApplicability,
    RegulationScore,
    RegulatoryChunk,
)
from models.enums import ComplianceStatus, Priority, Regulation
from rag.prompts import SYSTEM_PERSONA, executive_summary_prompt, PROMPT_VERSION
from agent.rule_engine import RULE_ENGINE_VERSION

logger = logging.getLogger(__name__)

_HIGH_WEIGHT = {Regulation.GDPR, Regulation.BDSG}

# Official source URLs for each regulation — used to make every gap and action traceable
_OFFICIAL_URLS: dict[str, str] = {
    "gdpr_dsgvo": "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679",
    "bdsg":       "https://www.gesetze-im-internet.de/bdsg_2018/",
    "nis2":       "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2555",
    "eu_ai_act":  "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202401689",
    "hinschg":    "https://www.gesetze-im-internet.de/hinschg/",
    "workplace_law": "https://www.gesetze-im-internet.de/arbschg/",
    "agg":        "https://www.gesetze-im-internet.de/agg/",
    "milog":      "https://www.gesetze-im-internet.de/milog/",
    "lksg":       "https://www.gesetze-im-internet.de/lksg/",
    "enefg":      "https://www.gesetze-im-internet.de/enefg/",
    "csrd":       "https://eur-lex.europa.eu/eli/dir/2022/2464/oj/eng",
}

# Optional[bool] fields grouped by when they are relevant.
# Fields are only counted if the company's profile makes them applicable.
_COMPLETENESS_GROUPS = [
    # (condition_attr_or_None, [field_names])
    (None, [                         # always relevant
        "has_privacy_policy", "has_processor_agreements", "has_data_breach_procedure",
        "has_tom_documentation", "has_data_retention_policy", "has_data_protection_training",
        "transfers_data_outside_eea", "has_consent_management",      # GDPR
        "has_gefaehrdungsbeurteilung", "has_gefaehrdungsbeurteilung_documented",
        "has_first_aid_measures", "has_employee_safety_training",    # ArbSchG
        "has_anti_discrimination_policy", "has_agc_complaints_procedure",  # AGG
        "has_working_time_records", "uses_subcontractors",           # MiLoG
    ]),
    ("is_critical_infrastructure_sector", [
        "has_information_security_policy", "has_incident_response_plan",
        "has_business_continuity_plan", "has_vulnerability_management",
        "has_mfa_implemented", "has_supply_chain_security_assessment",
        "has_security_awareness_training",
    ]),
    ("uses_ai_systems", [
        "ai_systems_are_high_risk", "has_ai_risk_assessment",
        "has_ai_usage_documentation", "has_human_oversight_procedure",
    ]),
    ("has_supply_chain_abroad", [
        "has_lksg_policy_statement", "has_supplier_code_of_conduct",
        "has_supplier_risk_assessment", "has_lksg_complaints_procedure",
    ]),
]
_HINSCHG_FIELDS = ["has_whistleblower_channel", "has_whistleblower_policy"]

# Profile fields that are directly relevant to each regulation's gap assessment.
# Used to compute per-gap confidence: unanswered fields → less confident findings.
_REG_FIELDS: dict[str, list[str]] = {
    "gdpr_dsgvo": [
        "has_privacy_policy", "has_processor_agreements", "has_data_breach_procedure",
        "has_tom_documentation", "has_data_retention_policy", "has_data_protection_training",
        "transfers_data_outside_eea", "has_consent_management",
    ],
    "bdsg": ["has_privacy_policy", "has_processor_agreements", "has_data_protection_training"],
    "nis2": [
        "has_information_security_policy", "has_incident_response_plan",
        "has_business_continuity_plan", "has_vulnerability_management",
        "has_mfa_implemented", "has_supply_chain_security_assessment",
        "has_security_awareness_training",
    ],
    "eu_ai_act": [
        "ai_systems_are_high_risk", "has_ai_risk_assessment",
        "has_ai_usage_documentation", "has_human_oversight_procedure",
    ],
    "hinschg": ["has_whistleblower_channel", "has_whistleblower_policy"],
    "workplace_law": [
        "has_gefaehrdungsbeurteilung", "has_gefaehrdungsbeurteilung_documented",
        "has_first_aid_measures", "has_employee_safety_training",
    ],
    "agg":   ["has_anti_discrimination_policy", "has_agc_complaints_procedure"],
    "milog": ["has_working_time_records", "uses_subcontractors"],
    "lksg":  [
        "has_lksg_policy_statement", "has_supplier_code_of_conduct",
        "has_supplier_risk_assessment", "has_lksg_complaints_procedure",
    ],
    "enefg": [],   # no specific optional profile fields — relies on energy consumption data
    "csrd":  [],   # no specific optional profile fields — relies on size thresholds
}


def _assign_gap_confidence(gaps: list, profile: "EnrichedCompanyProfile") -> None:
    """Set confidence and confidence_reason on each gap in-place."""
    from models.enums import ComplianceStatus as CS
    for gap in gaps:
        reg_key = gap.regulation.value
        fields  = _REG_FIELDS.get(reg_key, [])

        # CANNOT_ASSESS is always LOW — the system explicitly couldn't determine the status
        if gap.status == CS.CANNOT_ASSESS:
            gap.confidence        = "LOW"
            gap.confidence_reason = "Insufficient data — could not assess this requirement"
            continue

        if not fields:
            # Regulations with no optional profile fields are assessed from structural data only
            gap.confidence        = "HIGH"
            gap.confidence_reason = "Based on company structure data"
            continue

        unanswered = [f for f in fields if getattr(profile, f, None) is None]
        ratio      = 1 - len(unanswered) / len(fields)

        if ratio >= 0.8:
            gap.confidence        = "HIGH"
            gap.confidence_reason = "All key profile fields provided"
        elif ratio >= 0.5:
            n = len(unanswered)
            gap.confidence        = "MEDIUM"
            gap.confidence_reason = (
                f"{n} relevant field{'s' if n > 1 else ''} not provided — "
                "finding may rely on assumptions"
            )
        else:
            n = len(unanswered)
            gap.confidence        = "LOW"
            gap.confidence_reason = (
                f"{n} of {len(fields)} relevant fields not provided — "
                "verify with a complete profile"
            )


def _build_kb_versions(applicability: list) -> dict:
    """
    Build a {regulation: {fetched_at, source_file_hash, source_url}} map
    by reading chunk metadata from ChromaDB for each applicable regulation.
    Used to make reports auditable — every report records which legal version it used.
    """
    try:
        import chromadb
        from rag.ingest import CHROMA_DIR, REGULATION_COLLECTIONS, OFFICIAL_URLS
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        versions: dict = {}
        for reg_app in applicability:
            if not reg_app.applies:
                continue
            reg_key  = reg_app.regulation.value
            col_name = REGULATION_COLLECTIONS.get(reg_key)
            if not col_name:
                continue
            try:
                col     = client.get_collection(col_name)
                results = col.get(limit=1, include=["metadatas"])
                meta    = (results["metadatas"] or [{}])[0]
                versions[reg_key] = {
                    "fetched_at":       meta.get("fetched_at", "unknown"),
                    "source_file_hash": meta.get("source_file_hash", "unknown"),
                    "source_url":       OFFICIAL_URLS.get(reg_key, ""),
                }
            except Exception:
                versions[reg_key] = {"source_url": OFFICIAL_URLS.get(reg_key, "")}
        return versions
    except Exception as exc:
        logger.warning("actions: could not build KB versions: %s", exc)
        return {}


def _build_regulation_coverage(chunks: list[RegulatoryChunk]) -> dict:
    """Build per-regulation source coverage summary for display in reports.

    Returns {regulation_key: {law_chunks, guidance_chunks, total_chunks, unique_articles}}
    so users can see how well-grounded each regulation's analysis is.
    """
    coverage: dict = {}
    for chunk in chunks:
        reg_key = chunk.regulation.value
        if reg_key not in coverage:
            coverage[reg_key] = {"law_chunks": 0, "guidance_chunks": 0, "total_chunks": 0, "unique_articles": set()}
        coverage[reg_key]["total_chunks"] += 1
        coverage[reg_key]["unique_articles"].add(chunk.article_number)
        if chunk.document_type == "guidance":
            coverage[reg_key]["guidance_chunks"] += 1
        else:
            coverage[reg_key]["law_chunks"] += 1
    # Convert sets to counts for JSON serialisation
    for reg_key in coverage:
        coverage[reg_key]["unique_articles"] = len(coverage[reg_key]["unique_articles"])
    return coverage


def _stamp_source_urls(gaps: list, actions: list) -> None:
    """Add the official regulation source URL to every gap and action in-place."""
    for gap in gaps:
        gap.source_url = _OFFICIAL_URLS.get(gap.regulation.value)
    for action in actions:
        action.source_url = _OFFICIAL_URLS.get(action.regulation.value)


def _compute_completeness(profile: "EnrichedCompanyProfile") -> dict:
    relevant: list[str] = []
    for condition, fields in _COMPLETENESS_GROUPS:
        if condition is None or getattr(profile, condition, False):
            relevant.extend(fields)
    if getattr(profile, "employee_count", 0) >= 50:
        relevant.extend(_HINSCHG_FIELDS)

    unanswered = [f for f in relevant if getattr(profile, f, None) is None]
    answered   = len(relevant) - len(unanswered)
    score      = round(answered / len(relevant), 3) if relevant else 1.0

    return {
        "score":            score,
        "score_percent":    round(score * 100, 1),
        "answered":         answered,
        "relevant":         len(relevant),
        "unanswered_count": len(unanswered),
        "unanswered_fields": unanswered,
    }


@lru_cache(maxsize=1)
def _async_llm_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=settings.llm_api_key)


async def assemble_report(
    job_id: str,
    profile: EnrichedCompanyProfile,
    applicability: list[RegulationApplicability],
    chunks: list[RegulatoryChunk],
    gaps: list[ComplianceGap],
    actions: list[ActionItem],
    failures: list[str],
) -> ComplianceReport:
    """Assemble all pipeline outputs into a final ComplianceReport."""
    _assign_gap_confidence(gaps, profile)
    _stamp_source_urls(gaps, actions)
    kb_versions   = _build_kb_versions(applicability)
    reg_coverage  = _build_regulation_coverage(chunks)
    reg_scores    = _compute_scores(applicability, gaps)
    overall       = _weighted_score(reg_scores)
    critical      = _critical_findings(actions, gaps)
    completeness  = _compute_completeness(profile)
    applicable_count = sum(1 for a in applicability if a.applies)

    summary = await _executive_summary(
        profile.company_name,
        applicable_count,
        len(applicability),
        overall,
        critical,
        failures,
    )

    return ComplianceReport(
        job_id=job_id,
        company_name=profile.company_name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        applicable_regulations=applicability,
        inferred_characteristics=profile.inferred_characteristics,
        inferred_assumptions=getattr(profile, "inferred_assumptions", []),
        missing_optional_fields=profile.missing_optional_fields,
        validation_warnings=profile.validation_warnings,
        retrieved_chunks=chunks,
        gap_analysis=gaps,
        action_plan=actions,
        regulation_scores=reg_scores,
        overall_score_percent=overall,
        executive_summary=summary,
        requires_manual_review=list(failures),
        profile_completeness=completeness,
        knowledge_base_versions=kb_versions,
        regulation_coverage=reg_coverage,
        rule_engine_version=RULE_ENGINE_VERSION,
        prompt_version=PROMPT_VERSION,
    )


def _compute_scores(
    applicability: list[RegulationApplicability],
    gaps: list[ComplianceGap],
) -> list[RegulationScore]:
    scores = []
    for reg_app in applicability:
        if not reg_app.applies:
            continue
        # Always include applicable regulations, even with zero gap items — a
        # regulation with total_requirements=0 signals "no findings returned"
        # (failed/incomplete analysis), not "not applicable". Silently
        # omitting it here is indistinguishable from a clean bill of health,
        # the exact failure mode already fixed for gap analysis/action plan
        # truncation (see run_gap_analysis's max_tokens handling) — the score
        # breakdown must not reintroduce it.
        reg_gaps = [g for g in gaps if g.regulation == reg_app.regulation]
        total = len(reg_gaps)
        compliant     = sum(1 for g in reg_gaps if g.status == ComplianceStatus.COMPLIANT)
        partial       = sum(1 for g in reg_gaps if g.status == ComplianceStatus.PARTIALLY_COMPLIANT)
        non_compliant = sum(1 for g in reg_gaps if g.status == ComplianceStatus.NON_COMPLIANT)
        cannot        = sum(1 for g in reg_gaps if g.status == ComplianceStatus.CANNOT_ASSESS)

        # Compliance score: excludes CANNOT_ASSESS — unknown is not half-compliant
        assessed = compliant + partial + non_compliant
        score = round((compliant * 100 + partial * 50) / assessed, 1) if assessed else 0.0

        # Assessment completeness: proportion of items that could be assessed.
        # total=0 means nothing was assessed at all — 0%, not 100%.
        completeness = round(assessed / total * 100, 1) if total else 0.0

        scores.append(RegulationScore(
            regulation=reg_app.regulation,
            total_requirements=total,
            compliant=compliant,
            partially_compliant=partial,
            non_compliant=non_compliant,
            cannot_assess=cannot,
            score_percent=score,
            assessment_completeness_percent=completeness,
        ))
    return scores


def _weighted_score(reg_scores: list[RegulationScore]) -> float:
    """GDPR and BDSG weighted 1.5x — highest legal exposure for German SMEs."""
    total_weight = 0.0
    weighted_sum = 0.0
    for s in reg_scores:
        if s.total_requirements == 0:
            continue  # no findings returned — exclude, don't count as 0% compliant
        w = 1.5 if s.regulation in _HIGH_WEIGHT else 1.0
        weighted_sum += s.score_percent * w
        total_weight += w
    return round(weighted_sum / total_weight, 1) if total_weight else 0.0


def _critical_findings(
    actions: list[ActionItem],
    gaps: list[ComplianceGap],
) -> list[str]:
    findings: list[str] = []
    for a in actions:
        if a.priority in (Priority.CRITICAL, Priority.HIGH):
            findings.append(a.action[:200])
        if len(findings) >= 3:
            return findings
    for g in gaps:
        if g.status == ComplianceStatus.NON_COMPLIANT and g.deficiency_description:
            findings.append(g.deficiency_description[:200])
        if len(findings) >= 3:
            break
    return findings


async def _executive_summary(
    company_name: str,
    applicable_count: int,
    total_regs: int,
    overall_score: float,
    critical_findings: list[str],
    failures: list[str],
) -> str:
    import asyncio
    fallback = (
        f"Compliance assessment for {company_name} completed. "
        f"{applicable_count} of {total_regs} regulations apply. "
        f"Overall compliance score: {overall_score:.1f}%."
    )
    if not settings.llm_api_key:
        return fallback

    prompt = executive_summary_prompt(
        company_name, applicable_count, total_regs, overall_score, critical_findings
    )
    last_exc: Exception | None = None
    max_attempts = settings.llm_max_retries + 1
    for attempt in range(max_attempts):
        try:
            resp = await _async_llm_client().messages.create(
                model=settings.llm_model,
                max_tokens=1024,
                temperature=0,
                system=SYSTEM_PERSONA,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip()
        except anthropic.APIError as exc:
            logger.warning("actions: summary API error attempt %d/%d: %s", attempt + 1, max_attempts, exc)
            last_exc = exc
        except Exception as exc:
            logger.warning("actions: summary error attempt %d/%d: %s", attempt + 1, max_attempts, exc)
            last_exc = exc
        if attempt < max_attempts - 1:
            await asyncio.sleep(2 ** attempt)

    logger.error("actions: summary failed after retries (%s), using fallback", last_exc)
    failures.append("executive_summary")
    return fallback
