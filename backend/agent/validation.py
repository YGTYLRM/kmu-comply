"""
Step 6b: Self-validation of the assembled compliance report.

validate_report(report) returns a list of issue strings.
Empty list means the report passed all checks.

verify_gap_citations(gaps, chunks) cross-checks LLM-generated article citations
against actually-retrieved chunks to detect hallucinated article numbers.
"""
import logging
import re

from models.compliance_report import ComplianceGap, ComplianceReport, RegulatoryChunk
from models.enums import ComplianceStatus, Priority, Regulation

logger = logging.getLogger(__name__)

_DATA_PROTECTION_REGS = {Regulation.GDPR, Regulation.BDSG}

_NORM_RE = re.compile(r"[^0-9a-z]")  # keep only digits and lowercase letters


def _norm_article(s: str) -> str:
    """Normalise an article number for loose comparison.

    "Art. 32(1)(a)" → "3210a" is intentionally lossy — the goal is to catch
    completely hallucinated numbers (e.g. "Art. 99" when only Arts. 5-38 were
    retrieved), not to validate sub-paragraph granularity.
    """
    return _NORM_RE.sub("", s.lower())


def verify_gap_citations(
    gaps: list[ComplianceGap],
    chunks: list[RegulatoryChunk],
) -> list[str]:
    """Cross-check each gap's article_number against retrieved chunks for its regulation.

    Returns a list of warning strings for suspicious (potentially hallucinated)
    citations. Each suspicious gap also has its confidence lowered to LOW in-place.

    Special cases that are always skipped:
    - CANNOT_ASSESS gaps (article_number="KB-EMPTY" or no meaningful citation)
    - Gaps where no chunks were retrieved for the regulation (KB-EMPTY path)
    """
    # Build: regulation_value → set of normalised article numbers from chunks
    chunk_articles: dict[str, set[str]] = {}
    for chunk in chunks:
        key = chunk.regulation.value
        chunk_articles.setdefault(key, set()).add(_norm_article(chunk.article_number))

    warnings: list[str] = []
    for gap in gaps:
        if gap.status == ComplianceStatus.CANNOT_ASSESS:
            continue
        reg_key = gap.regulation.value
        known = chunk_articles.get(reg_key)
        if not known:
            # No chunks retrieved — already handled by zero-chunks guard
            continue

        norm = _norm_article(gap.article_number)
        if not norm:
            continue

        # Check if this normalised number partially matches any retrieved article.
        # We do a substring match both ways to handle "3210a" ⊆ "3210a1b" etc.
        matched = any(
            norm in known_art or known_art in norm
            for known_art in known
            if known_art  # skip empty strings
        )
        if not matched:
            msg = (
                f"citation unverified: {gap.regulation.value} {gap.article_number} "
                f"was not found in retrieved chunks (retrieved: "
                f"{', '.join(sorted(chunk_articles[reg_key])[:8])})"
            )
            logger.warning("validation: %s", msg)
            warnings.append(msg)
            # Downgrade confidence on the gap so the user sees it needs review
            if gap.confidence != "LOW":
                gap.confidence = "LOW"
                gap.confidence_reason = (
                    "Article number not verified in retrieved chunks — "
                    "may be a hallucinated citation; verify manually"
                )

    return warnings


def validate_report(report: ComplianceReport) -> list[str]:
    issues: list[str] = []

    gap_keys = {
        f"{g.regulation.value}:{g.article_number}" for g in report.gap_analysis
    }
    action_refs = {a.gap_reference for a in report.action_plan}

    # Every non-compliant gap must have at least one action
    for gap in report.gap_analysis:
        if gap.status in (ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT):
            ref = f"{gap.regulation.value}:{gap.article_number}"
            if ref not in action_refs:
                issues.append(f"unresolved gap: {ref} ({gap.status.value}) has no action item")

    # No action should reference a gap that does not exist
    for action in report.action_plan:
        if action.gap_reference not in gap_keys:
            issues.append(
                f"orphan action: gap_reference '{action.gap_reference}' matches no gap"
            )

    # Data protection violations must be at least HIGH priority
    for action in report.action_plan:
        if action.regulation in _DATA_PROTECTION_REGS and action.priority == Priority.LOW:
            issues.append(
                f"priority too low: {action.regulation.value} {action.article_number} "
                f"is marked LOW — data protection violations must be HIGH or above"
            )

    # Disclaimer and summary must be present
    if not report.disclaimer:
        issues.append("missing disclaimer")
    if not report.executive_summary:
        issues.append("missing executive summary")

    for issue in issues:
        logger.warning("validation: %s", issue)

    return issues
