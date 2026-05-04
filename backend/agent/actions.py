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
from rag.prompts import SYSTEM_PERSONA, executive_summary_prompt

logger = logging.getLogger(__name__)

_HIGH_WEIGHT = {Regulation.GDPR, Regulation.BDSG}


@lru_cache(maxsize=1)
def _llm_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.llm_api_key)


def assemble_report(
    job_id: str,
    profile: EnrichedCompanyProfile,
    applicability: list[RegulationApplicability],
    chunks: list[RegulatoryChunk],
    gaps: list[ComplianceGap],
    actions: list[ActionItem],
    failures: list[str],
) -> ComplianceReport:
    """Assemble all pipeline outputs into a final ComplianceReport."""
    reg_scores = _compute_scores(applicability, gaps)
    overall = _weighted_score(reg_scores)
    critical = _critical_findings(actions, gaps)
    applicable_count = sum(1 for a in applicability if a.applies)

    summary = _executive_summary(
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
        missing_optional_fields=profile.missing_optional_fields,
        validation_warnings=profile.validation_warnings,
        retrieved_chunks=chunks,
        gap_analysis=gaps,
        action_plan=actions,
        regulation_scores=reg_scores,
        overall_score_percent=overall,
        executive_summary=summary,
        requires_manual_review=list(failures),
    )


def _compute_scores(
    applicability: list[RegulationApplicability],
    gaps: list[ComplianceGap],
) -> list[RegulationScore]:
    scores = []
    for reg_app in applicability:
        if not reg_app.applies:
            continue
        reg_gaps = [g for g in gaps if g.regulation == reg_app.regulation]
        if not reg_gaps:
            continue
        total = len(reg_gaps)
        compliant = sum(1 for g in reg_gaps if g.status == ComplianceStatus.COMPLIANT)
        partial = sum(1 for g in reg_gaps if g.status == ComplianceStatus.PARTIALLY_COMPLIANT)
        non_compliant = sum(1 for g in reg_gaps if g.status == ComplianceStatus.NON_COMPLIANT)
        cannot = sum(1 for g in reg_gaps if g.status == ComplianceStatus.CANNOT_ASSESS)
        score = round((compliant * 100 + partial * 50 + cannot * 50) / total, 1)
        scores.append(RegulationScore(
            regulation=reg_app.regulation,
            total_requirements=total,
            compliant=compliant,
            partially_compliant=partial,
            non_compliant=non_compliant,
            cannot_assess=cannot,
            score_percent=score,
        ))
    return scores


def _weighted_score(reg_scores: list[RegulationScore]) -> float:
    """GDPR and BDSG weighted 1.5x — highest legal exposure for German SMEs."""
    total_weight = 0.0
    weighted_sum = 0.0
    for s in reg_scores:
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


def _executive_summary(
    company_name: str,
    applicable_count: int,
    total_regs: int,
    overall_score: float,
    critical_findings: list[str],
    failures: list[str],
) -> str:
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
    for attempt in range(settings.llm_max_retries + 1):
        try:
            resp = _llm_client().messages.create(
                model=settings.llm_model,
                max_tokens=512,
                temperature=0,
                system=SYSTEM_PERSONA,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip()
        except anthropic.APIError as exc:
            logger.warning("actions: summary API error attempt %d: %s", attempt + 1, exc)
            last_exc = exc
        except Exception as exc:
            logger.warning("actions: summary error attempt %d: %s", attempt + 1, exc)
            last_exc = exc

    logger.error("actions: summary failed after retries (%s), using fallback", last_exc)
    failures.append("executive_summary")
    return fallback
