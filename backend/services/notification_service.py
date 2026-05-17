"""
Email notification service — Phase 10.

Sends alert emails via Resend when:
  - A scheduled monthly re-assessment completes
  - A regulation change triggers a re-assessment
  - Score drops vs. previous report
  - Previously resolved gaps regress

Notifications are saved to the DB first, then this service
sends the email and marks them as sent.
"""
import logging
from datetime import datetime, timezone

from config import settings
from models.compliance_report import ComplianceReport

logger = logging.getLogger(__name__)

BASE_URL = "https://complio.app"  # update to real domain when deployed


def _score_color(score: float) -> str:
    if score >= 75:
        return "#10b981"  # emerald
    if score >= 50:
        return "#f59e0b"  # amber
    return "#ef4444"      # red


def _delta_line(current: float, previous: float | None) -> str:
    if previous is None:
        return ""
    delta = current - previous
    if delta > 0:
        return f'<span style="color:#10b981">▲ {delta:+.1f}% vs previous screening</span>'
    if delta < 0:
        return f'<span style="color:#ef4444">▼ {delta:.1f}% vs previous screening</span>'
    return '<span style="color:#94a3b8">No change vs previous screening</span>'


def _gap_summary(current_report: ComplianceReport, prev_report: ComplianceReport | None) -> tuple[int, int, int]:
    """Returns (compliant_count, partial_count, non_compliant_count) for current report."""
    statuses = [g.status.value if hasattr(g.status, "value") else str(g.status) for g in current_report.gap_analysis]
    compliant     = sum(1 for s in statuses if s == "COMPLIANT")
    partial       = sum(1 for s in statuses if s == "PARTIALLY_COMPLIANT")
    non_compliant = sum(1 for s in statuses if s == "NON_COMPLIANT")
    return compliant, partial, non_compliant


def _regressions(current_report: ComplianceReport, prev_report: ComplianceReport | None) -> list[str]:
    if not prev_report:
        return []
    prev_map = {
        f"{g.regulation}:{getattr(g, 'article_number', '')}":
        (g.status.value if hasattr(g.status, "value") else str(g.status))
        for g in prev_report.gap_analysis
    }
    _rank = {"COMPLIANT": 2, "PARTIALLY_COMPLIANT": 1, "NON_COMPLIANT": 0}
    regressions = []
    for g in current_report.gap_analysis:
        key = f"{g.regulation}:{getattr(g, 'article_number', '')}"
        prev_status = prev_map.get(key)
        curr_status = g.status.value if hasattr(g.status, "value") else str(g.status)
        if prev_status and _rank.get(curr_status, 0) < _rank.get(prev_status, 0):
            regressions.append(f"{g.regulation} — {getattr(g, 'article_number', 'unknown article')}")
    return regressions


def _build_email_html(
    company_name: str,
    report: ComplianceReport | None,
    triggered_by: str,
    prev_report: ComplianceReport | None,
    changed_sections: list[str] | None = None,
) -> tuple[str, str]:
    """Returns (subject, html_body)."""
    # Document ageing alerts have no associated report
    if triggered_by == "document_ageing" or report is None:
        subject = f"Action required: compliance report for {company_name} may be outdated"
        html = f"""<html><body style="font-family:Arial,sans-serif;background:#0f172a;color:#e2e8f0;padding:32px;">
<div style="max-width:560px;margin:0 auto;">
<h2 style="color:#60a5fa;">Compliance Update Needed</h2>
<p>The regulatory knowledge base used to generate your compliance report for
<strong>{company_name}</strong> has been updated since your last assessment.</p>
<p>We recommend re-running the compliance analysis in Complio to ensure your report
reflects the latest legal text. This is especially important if any of the updated
regulations are relevant to your business.</p>
<p style="margin-top:24px;"><a href="{BASE_URL}/dashboard"
style="background:#2563eb;color:#fff;padding:12px 24px;border-radius:6px;
text-decoration:none;font-weight:600;">Re-run Analysis</a></p>
<p style="font-size:11px;color:#64748b;margin-top:24px;">
You are receiving this because you have an active Complio account.
This is not legal advice.</p>
</div></body></html>"""
        return subject, html

    score = report.overall_score_percent
    compliant, partial, non_compliant = _gap_summary(report, prev_report)
    prev_score = prev_report.overall_score_percent if prev_report else None
    delta_html = _delta_line(score, prev_score)
    regressions = _regressions(report, prev_report)
    report_url = f"{BASE_URL}/report/{report.job_id}"

    if triggered_by == "reg_change":
        subject = f"Regulation update: your {company_name} screening has been refreshed"
        trigger_line = "A regulation you are covered by has been updated. Your screening has been automatically refreshed."
    else:
        subject = f"Monthly compliance update for {company_name}"
        trigger_line = "Your monthly compliance screening has completed."

    # Changed sections block — only shown for regulation-change notifications
    changed_sections_block = ""
    if triggered_by == "reg_change" and changed_sections:
        items = "".join(
            f'<li style="margin-bottom:4px;color:#93c5fd;font-family:monospace">{s}</li>'
            for s in changed_sections[:20]  # cap at 20 to keep email readable
        )
        overflow = f'<p style="font-size:11px;color:#475569;margin:6px 0 0">…and {len(changed_sections) - 20} more sections</p>' if len(changed_sections) > 20 else ""
        changed_sections_block = f"""
        <div style="background:rgba(37,99,235,0.08);border:1px solid rgba(37,99,235,0.25);border-radius:10px;padding:14px 18px;margin-bottom:20px">
          <p style="font-size:12px;font-weight:700;color:#60a5fa;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 8px">
            Sections that changed
          </p>
          <ul style="margin:0;padding-left:16px;font-size:13px;line-height:1.8">{items}</ul>
          {overflow}
        </div>"""

    regression_block = ""
    if regressions:
        items = "".join(f'<li style="margin-bottom:4px;color:#f87171">{r}</li>' for r in regressions)
        regression_block = f"""
        <div style="background:#450a0a;border:1px solid #7f1d1d;border-radius:10px;padding:14px 18px;margin-top:16px">
          <p style="font-size:12px;font-weight:700;color:#fca5a5;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 8px">
            Gaps that regressed
          </p>
          <ul style="margin:0;padding-left:16px;font-size:13px">{items}</ul>
        </div>"""

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#03071a;font-family:sans-serif">
  <div style="max-width:580px;margin:0 auto;padding:32px 20px">

    <!-- Header -->
    <div style="margin-bottom:28px">
      <p style="font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#2563eb;margin:0 0 6px">
        Complio — Compliance Monitor
      </p>
      <h1 style="font-size:22px;font-weight:900;color:#ffffff;margin:0;line-height:1.3">
        {company_name}
      </h1>
      <p style="font-size:14px;color:#64748b;margin:6px 0 0">{trigger_line}</p>
    </div>

    <!-- Score card -->
    <div style="background:rgba(10,22,40,0.9);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:24px;margin-bottom:20px;text-align:center">
      <p style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 8px">
        Overall compliance score
      </p>
      <p style="font-size:52px;font-weight:900;color:{_score_color(score)};margin:0;line-height:1">
        {score:.1f}<span style="font-size:28px">%</span>
      </p>
      <p style="font-size:13px;margin:10px 0 0">{delta_html}</p>
    </div>

    <!-- Gap summary -->
    <div style="display:flex;gap:12px;margin-bottom:20px">
      <div style="flex:1;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);border-radius:12px;padding:16px;text-align:center">
        <p style="font-size:28px;font-weight:900;color:#10b981;margin:0">{compliant}</p>
        <p style="font-size:11px;color:#64748b;margin:4px 0 0">Compliant</p>
      </div>
      <div style="flex:1;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);border-radius:12px;padding:16px;text-align:center">
        <p style="font-size:28px;font-weight:900;color:#f59e0b;margin:0">{partial}</p>
        <p style="font-size:11px;color:#64748b;margin:4px 0 0">Partial</p>
      </div>
      <div style="flex:1;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);border-radius:12px;padding:16px;text-align:center">
        <p style="font-size:28px;font-weight:900;color:#ef4444;margin:0">{non_compliant}</p>
        <p style="font-size:11px;color:#64748b;margin:4px 0 0">Non-compliant</p>
      </div>
    </div>

    {changed_sections_block}

    {regression_block}

    <!-- CTA -->
    <div style="text-align:center;margin:28px 0">
      <a href="{report_url}"
         style="display:inline-block;background:#2563eb;color:#ffffff;font-size:14px;font-weight:700;
                padding:14px 32px;border-radius:12px;text-decoration:none;
                box-shadow:0 0 20px rgba(37,99,235,0.4)">
        View full report →
      </a>
    </div>

    <!-- Footer -->
    <div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:20px;margin-top:8px">
      <p style="font-size:11px;color:#374151;line-height:1.6;margin:0">
        This is an automated compliance monitoring alert from Complio.
        Results are for preliminary screening only and do not constitute legal advice.
        Always verify with a qualified German attorney before taking action.
      </p>
      <p style="font-size:11px;color:#374151;margin:8px 0 0">
        © {datetime.now(timezone.utc).year} Complio
      </p>
    </div>
  </div>
</body>
</html>"""

    return subject, html


async def send_notification_email(
    notification_id: str,
    user_email: str,
    company_name: str,
    report: ComplianceReport | None,
    triggered_by: str,
    prev_report: ComplianceReport | None = None,
    changed_sections: list[str] | None = None,
) -> bool:
    """
    Send a notification email and mark the notification as sent in the DB.
    Returns True on success.
    """
    if not settings.resend_api_key:
        logger.warning("notification_service: RESEND_API_KEY not set, skipping email")
        return False

    try:
        import resend
        resend.api_key = settings.resend_api_key

        subject, html_body = _build_email_html(company_name, report, triggered_by, prev_report, changed_sections)

        resend.Emails.send({
            "from": "Complio Monitor <onboarding@resend.dev>",
            "to": [user_email],
            "subject": subject,
            "html": html_body,
        })

        # Mark as sent in DB
        from db.database import AsyncSessionLocal
        from db.models import Notification
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Notification).where(Notification.id == notification_id))
            notif = result.scalar_one_or_none()
            if notif:
                notif.read_at = datetime.now(timezone.utc)
                await db.commit()

        logger.info("notification_service: sent %s alert to %s for %s", triggered_by, user_email, company_name)
        return True

    except Exception as exc:
        logger.error("notification_service: failed to send email to %s: %s", user_email, exc)
        return False


async def get_unread_count(user_id: str) -> int:
    """Return number of unread notifications for the navbar bell."""
    from db.database import AsyncSessionLocal
    from db.models import Notification
    from sqlalchemy import select, func

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(func.count()).where(
                    Notification.user_id == user_id,
                    Notification.read_at == None,  # noqa: E711
                )
            )
            return result.scalar_one() or 0
    except Exception:
        return 0


async def get_notifications(user_id: str, limit: int = 20) -> list[dict]:
    """Return recent notifications for a user."""
    from db.database import AsyncSessionLocal
    from db.models import Notification
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
            return [
                {
                    "id": str(n.id),
                    "type": n.type,
                    "title": n.title,
                    "message": n.message,
                    "read": n.read_at is not None,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in rows
            ]
    except Exception:
        return []


async def mark_all_read(user_id: str) -> None:
    """Mark all notifications as read for a user."""
    from db.database import AsyncSessionLocal
    from db.models import Notification
    from sqlalchemy import update

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at == None)  # noqa: E711
            .values(read_at=datetime.now(timezone.utc))
        )
        await db.commit()
