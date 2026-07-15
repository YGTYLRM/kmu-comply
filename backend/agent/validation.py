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

_PRIMARY_NUM_RE = re.compile(r"(\d+)")


def _norm_article(s: str) -> str:
    """Extract the primary article/section number for comparison.

    "Art. 32(1)(a)" → "32", "§ 5" → "5", "Art. 9(1)" → "9".
    The goal is to catch completely hallucinated numbers (e.g. "Art. 99" when
    only Arts. 5-38 were retrieved) without false-matching across articles
    (e.g. "Art. 3" should not validate "Art. 32").
    """
    m = _PRIMARY_NUM_RE.search(s)
    return m.group(1) if m else ""


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

        # Check if the primary article number matches any retrieved article.
        # Exact match on the leading number (e.g. "32" == "32") so that
        # Art. 3 doesn't falsely validate Art. 32.
        matched = any(
            norm == known_art
            for known_art in known
            if known_art
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


_WHITESPACE_RE = re.compile(r"\s+")

# Ellipsis markers the LLM may use to elide text inside a quote
_ELLIPSIS_RE = re.compile(r"\.{3}|…|\[\.\.\.\]|\[…\]")

# Fragments shorter than this are too generic to prove the quote came from the
# chunk ("muss", "Art. 5") — they are skipped during verification.
_MIN_QUOTE_FRAGMENT_CHARS = 15


def _normalize_quote(text: str) -> str:
    """Normalize text for quote-in-chunk comparison: collapse whitespace,
    casefold, and strip surrounding quotation marks."""
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text.strip('"\'„“”‚‘’«»').casefold()


def _quote_found_in_chunks(quote: str, chunk_texts: list[str]) -> bool:
    """True if every substantial fragment of the quote appears verbatim
    (whitespace/case-normalized) in at least one chunk text.

    Quotes may contain ellipses ("..." / "…") to elide text — each fragment
    between ellipses is checked independently. Fragments under
    _MIN_QUOTE_FRAGMENT_CHARS are skipped as too generic to verify.
    """
    normalized_chunks = [_normalize_quote(t) for t in chunk_texts]
    fragments = [
        _normalize_quote(f)
        for f in _ELLIPSIS_RE.split(quote)
    ]
    fragments = [f for f in fragments if len(f) >= _MIN_QUOTE_FRAGMENT_CHARS]
    if not fragments:
        # Nothing substantial enough to verify — treat as unverifiable, not as a lie
        return True
    return all(
        any(frag in chunk for chunk in normalized_chunks)
        for frag in fragments
    )


def check_evidence_quotes(
    gaps: list[ComplianceGap],
    chunks: list[RegulatoryChunk] | None = None,
) -> list[str]:
    """Verify evidence_quote integrity on VERIFIED/HIGH-confidence gaps.

    Two checks:
    1. HIGH-confidence gaps without an evidence_quote → downgrade to MEDIUM.
       A VERIFIED finding claims to be backed by a retrieved chunk; if the LLM
       cannot quote the chunk, the finding is suspect.
    2. When chunks are provided: gaps WITH an evidence_quote whose quote does
       not appear verbatim (whitespace/case-normalized) in any retrieved chunk
       for that regulation → downgrade to LOW. A fabricated quote is a stronger
       hallucination signal than a missing one.

    Returns a list of warning strings and downgrades confidence in-place.
    """
    # Build: regulation_value → list of chunk texts for quote lookup
    chunk_texts: dict[str, list[str]] = {}
    for chunk in chunks or []:
        chunk_texts.setdefault(chunk.regulation.value, []).append(chunk.text)

    warnings: list[str] = []
    for gap in gaps:
        if gap.status == ComplianceStatus.CANNOT_ASSESS:
            continue

        quote = getattr(gap, "evidence_quote", None)

        if gap.confidence == "HIGH" and not quote:
            msg = (
                f"missing evidence_quote: {gap.regulation.value} {gap.article_number} "
                f"is marked HIGH confidence but provides no verbatim chunk quote — "
                f"downgrading confidence to MEDIUM"
            )
            logger.warning("validation: %s", msg)
            warnings.append(msg)
            gap.confidence = "MEDIUM"
            gap.confidence_reason = (
                "No verbatim source quote provided — HIGH confidence requires "
                "a direct quotation from the retrieved regulatory text"
            )
            continue

        if quote:
            reg_texts = chunk_texts.get(gap.regulation.value)
            if not reg_texts:
                continue  # no chunks for this regulation — zero-chunks guard handles it
            if not _quote_found_in_chunks(quote, reg_texts):
                msg = (
                    f"fabricated evidence_quote: {gap.regulation.value} "
                    f"{gap.article_number} quotes text that appears in no retrieved "
                    f"chunk — downgrading confidence to LOW"
                )
                logger.warning("validation: %s", msg)
                warnings.append(msg)
                gap.confidence = "LOW"
                gap.confidence_reason = (
                    "Evidence quote not found in any retrieved regulatory text — "
                    "the quotation may be fabricated; verify manually"
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
