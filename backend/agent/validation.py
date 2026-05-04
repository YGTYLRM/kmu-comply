"""
Step 6b: Self-validation of the assembled compliance report.

validate_report(report) returns a list of issue strings.
Empty list means the report passed all checks.
"""
import logging

from models.compliance_report import ComplianceReport
from models.enums import ComplianceStatus, Priority, Regulation

logger = logging.getLogger(__name__)

_DATA_PROTECTION_REGS = {Regulation.GDPR, Regulation.BDSG}


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
