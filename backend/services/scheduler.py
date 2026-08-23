"""
Monitoring scheduler — the core of the SaaS.

Two recurring jobs:
  1. daily_regulation_check  — detects changes in regulation texts, queues
                               re-assessments for every affected company.
  2. monthly_reassessment    — re-assesses every company whose last report
                               is older than 30 days.

Uses APScheduler with AsyncIOScheduler so it lives inside the FastAPI process
with no extra infrastructure (no Redis, no Celery) at this scale.
"""
import asyncio
import hashlib
import json
import logging
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _create_supervised_task(coro, label: str) -> "asyncio.Task":
    task = asyncio.create_task(coro)
    def _on_done(t: "asyncio.Task") -> None:
        if not t.cancelled() and t.exception():
            logger.error("scheduler: %s task crashed: %s", label, t.exception())
    task.add_done_callback(_on_done)
    return task

# Where regulation text files live
_REG_DIR = Path(__file__).parent.parent / "data" / "regulations"
_HASH_FILE = Path(__file__).parent.parent / "data" / "reg_hashes.json"


# ── Regulation change detection ───────────────────────────────────────────────

def _hash_dir(path: Path) -> str:
    """Stable hash of all text files under a regulation directory."""
    h = hashlib.sha256()
    for f in sorted(path.rglob("*.txt")):
        h.update(f.read_bytes())
    return h.hexdigest()


def _load_hashes() -> dict[str, str]:
    if _HASH_FILE.exists():
        try:
            return json.loads(_HASH_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_hashes(hashes: dict[str, str]) -> None:
    _HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    _HASH_FILE.write_text(json.dumps(hashes, indent=2), encoding="utf-8")


async def daily_regulation_check() -> None:
    """
    Compare current regulation file hashes against stored ones.
    For each changed regulation:
      1. Re-ingest the updated source files into ChromaDB
      2. Diff section hashes to find which specific articles changed
      3. Queue a re-assessment for every affected company, with section detail
    """
    logger.info("scheduler: running daily regulation check")
    if not _REG_DIR.exists():
        logger.warning("scheduler: regulation directory not found, skipping check")
        return

    old_hashes = _load_hashes()
    new_hashes: dict[str, str] = {}
    changed: list[str] = []

    for reg_dir in sorted(_REG_DIR.iterdir()):
        if not reg_dir.is_dir():
            continue
        name = reg_dir.name
        current_hash = _hash_dir(reg_dir)
        new_hashes[name] = current_hash
        if old_hashes.get(name) and old_hashes[name] != current_hash:
            changed.append(name)
            logger.info("scheduler: regulation changed: %s", name)

    _save_hashes(new_hashes)

    if not changed:
        logger.info("scheduler: no regulation changes detected")
        return

    from services.db_service import get_companies_for_regulation
    from services.section_hash_store import build_section_hashes, diff, save, summarise_diff
    from rag.ingest import ingest_regulation, REGULATION_COLLECTIONS

    for reg_name in changed:
        try:
            # Load section hashes from before re-ingestion
            from services.section_hash_store import load_all
            old_section_hashes = load_all().get(reg_name, {})

            # Re-ingest so ChromaDB reflects the updated source
            if reg_name in REGULATION_COLLECTIONS:
                logger.info("scheduler: re-ingesting %s", reg_name)
                n = ingest_regulation(reg_name, reset=True)
                logger.info("scheduler: %s re-ingested (%d chunks)", reg_name, n)

            # Compute new section hashes and diff
            new_section_hashes = build_section_hashes(reg_name)
            section_diff = diff(old_section_hashes, new_section_hashes)
            save(reg_name, new_section_hashes)

            changed_sections = section_diff["changed"] + section_diff["added"]
            summary = summarise_diff(reg_name, section_diff)
            logger.info("scheduler: %s section diff — %s", reg_name, summary)

            companies = await get_companies_for_regulation(reg_name)
            logger.info("scheduler: %s changed — queuing %d companies", reg_name, len(companies))
            for c in companies:
                _create_supervised_task(
                    _run_scheduled_analysis(
                        c,
                        triggered_by="reg_change",
                        reason=f"{reg_name} updated: {summary}",
                        changed_sections=changed_sections,
                    ),
                    label=f"reg_change:{reg_name}:{c.get('company_name','?')}",
                )
        except Exception as exc:
            logger.error("scheduler: error processing regulation %s: %s", reg_name, exc)


# ── Monthly re-assessment ─────────────────────────────────────────────────────

async def monthly_reassessment() -> None:
    """
    Find all companies due for re-assessment based on their plan interval:
      - Professional: every 7 days
      - Starter / default: every 30 days
    """
    logger.info("scheduler: running re-assessment check")
    try:
        from services.db_service import get_all_companies_due_for_reassessment
        from services.stripe_service import get_active_subscription, PLAN_CONFIG
        from config import settings

        for interval_days in sorted({7, 30}):
            companies = await get_all_companies_due_for_reassessment(interval_days=interval_days)
            for c in companies:
                # Check the user's plan interval; skip if their plan uses a different interval
                if settings.stripe_enabled:
                    sub = await get_active_subscription(c["user_id"])
                    plan_days = PLAN_CONFIG.get(sub["plan"], {}).get("reassessment_days", 30) if sub else 30
                    if plan_days != interval_days:
                        continue

                logger.info("scheduler: queuing %s (interval=%dd)", c["company_name"], interval_days)
                _create_supervised_task(
                    _run_scheduled_analysis(c, triggered_by="scheduled", reason=f"{interval_days}d cycle"),
                    label=f"scheduled:{c['company_name']}",
                )
    except Exception as exc:
        logger.error("scheduler: monthly re-assessment error: %s", exc)


# ── Shared analysis runner ────────────────────────────────────────────────────

async def _run_scheduled_analysis(
    company: dict,
    triggered_by: str,
    reason: str,
    changed_sections: list[str] | None = None,
) -> None:
    """
    Run a full analysis pipeline for a company dict as returned by db_service.
    Saves result to disk + DB and queues a notification.
    """
    company_name = company["company_name"]
    user_id      = company["user_id"]
    company_id   = company["company_id"]

    logger.info("scheduler: starting %s analysis for %s (%s)", triggered_by, company_name, reason)

    try:
        from models.company_profile import CompanyProfile
        profile = CompanyProfile(**company["profile"])
    except Exception as exc:
        logger.error("scheduler: invalid profile for %s: %s", company_name, exc)
        return

    try:
        from agent.compliance_agent import run_analysis
        import uuid

        job_id = str(uuid.uuid4())
        report = await run_analysis(job_id, profile, on_step=lambda _: None)

        # Save to disk with ownership
        from services.report_store import save as disk_save
        disk_save(report, user_id=user_id)

        # Save to DB
        from services.db_service import save_report_to_db
        await save_report_to_db(company_id, report, triggered_by=triggered_by)

        logger.info("scheduler: completed %s analysis for %s — score %.1f%%",
                    triggered_by, company_name, report.overall_score_percent)

        # Fetch previous report for delta comparison
        prev_report = None
        try:
            from db.database import AsyncSessionLocal
            from db.models import Report as ReportRow
            from sqlalchemy import select
            async with AsyncSessionLocal() as db:
                rows = (await db.execute(
                    select(ReportRow)
                    .where(ReportRow.company_id == company_id)
                    .order_by(ReportRow.created_at.desc())
                    .limit(2)
                )).scalars().all()
                if len(rows) >= 2:
                    from models.compliance_report import ComplianceReport as CR
                    raw = rows[1].raw_json
                    if raw:
                        prev_report = CR.model_validate(raw)
        except Exception:
            pass

        await _queue_notification(
            user_id, company["user_email"], company_name, report, triggered_by,
            prev_report=prev_report,
            changed_sections=changed_sections,
        )

    except Exception as exc:
        logger.error("scheduler: analysis failed for %s: %s", company_name, exc)


async def _queue_notification(
    user_id: str,
    user_email: str,
    company_name: str,
    report,
    triggered_by: str,
    prev_report=None,
    changed_sections: list[str] | None = None,
) -> None:
    """Save a notification to the DB and send the email immediately."""
    try:
        from db.database import AsyncSessionLocal
        from db.models import Notification

        if triggered_by == "scheduled":
            title   = f"Monthly compliance update: {company_name}"
            message = (
                f"Your monthly compliance screening for {company_name} is complete. "
                f"Overall score: {report.overall_score_percent:.1f}%."
            )
        else:
            title   = f"Regulation update affected {company_name}"
            message = (
                f"A regulation you're covered by has been updated. "
                f"Your screening for {company_name} has been refreshed. "
                f"Overall score: {report.overall_score_percent:.1f}%."
            )

        async with AsyncSessionLocal() as db:
            notif = Notification(
                user_id=user_id,
                type=triggered_by,
                title=title,
                message=message,
            )
            db.add(notif)
            await db.commit()
            await db.refresh(notif)
            notif_id = notif.id

        # Send email immediately
        from services.notification_service import send_notification_email
        await send_notification_email(
            notification_id=notif_id,
            user_email=user_email,
            company_name=company_name,
            report=report,
            triggered_by=triggered_by,
            prev_report=prev_report,
            changed_sections=changed_sections,
        )

    except Exception as exc:
        logger.error("scheduler: notification error: %s", exc)


# ── Lifecycle ─────────────────────────────────────────────────────────────────

def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Daily at 03:00 UTC — regulation change detection
    _scheduler.add_job(
        daily_regulation_check,
        trigger="cron",
        hour=3,
        minute=0,
        id="daily_regulation_check",
        replace_existing=True,
        max_instances=1,
    )

    # Daily at 04:00 UTC — monthly re-assessment (runs daily, skips companies not yet due)
    _scheduler.add_job(
        monthly_reassessment,
        trigger="cron",
        hour=4,
        minute=0,
        id="monthly_reassessment",
        replace_existing=True,
        max_instances=1,
    )

    # Weekly on Sunday at 02:00 UTC — fetch regulation updates from official sources
    # Creates PendingRegulationUpdate records; requires human approval before KB update
    _scheduler.add_job(
        _fetch_official_updates,
        trigger="cron",
        day_of_week="sun",
        hour=2,
        minute=0,
        id="weekly_official_fetch",
        replace_existing=True,
        max_instances=1,
    )

    # Weekly on Monday at 05:00 UTC — document ageing check
    # Alerts companies whose last report uses a KB version older than the current one
    _scheduler.add_job(
        document_ageing_check,
        trigger="cron",
        day_of_week="mon",
        hour=5,
        minute=0,
        id="document_ageing_check",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info(
        "scheduler: started — regulation check 03:00 UTC daily, "
        "re-assessments 04:00 UTC daily, official fetch 02:00 UTC Sundays, "
        "document ageing check 05:00 UTC Mondays"
    )
    return _scheduler


async def document_ageing_check() -> None:
    """
    Weekly job: alert users whose compliance knowledge base has been updated
    since their last report was generated.

    Logic:
      1. Load the current KB ingestion dates from ChromaDB metadata.
      2. For each company that has a saved report, compare report.generated_at
         against the KB fetched_at for the regulations in that report.
      3. If any regulation was re-ingested AFTER the report was generated,
         the report may be based on outdated legal text — send a notification.

    Only fires if the gap is at least 7 days (avoids spurious alerts from
    same-day ingest + report runs during onboarding).
    """
    logger.info("scheduler: running document ageing check")
    try:
        from config import settings
        if not settings.database_url:
            logger.info("scheduler: document ageing check skipped — no database")
            return

        from db.database import AsyncSessionLocal
        from db.models import Report as ReportRow, Company, Profile
        from sqlalchemy import select
        from datetime import datetime, timezone, timedelta
        import chromadb
        from rag.ingest import CHROMA_DIR, REGULATION_COLLECTIONS

        # Build current KB ingest dates from ChromaDB metadata
        kb_dates: dict[str, datetime] = {}
        try:
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            for reg_key, col_name in REGULATION_COLLECTIONS.items():
                try:
                    col = client.get_collection(col_name)
                    results = col.get(limit=1, include=["metadatas"])
                    meta = (results["metadatas"] or [{}])[0]
                    fetched_str = meta.get("fetched_at", "")
                    if fetched_str:
                        kb_dates[reg_key] = datetime.fromisoformat(
                            fetched_str.replace("Z", "+00:00")
                        )
                except Exception:
                    pass
        except Exception as exc:
            logger.warning("scheduler: ageing check could not read KB dates: %s", exc)
            return

        if not kb_dates:
            logger.info("scheduler: ageing check — no KB dates found, skipping")
            return

        stale_count = 0
        async with AsyncSessionLocal() as db:
            # Get latest report per company with user info
            reports = (await db.execute(
                select(ReportRow, Company, Profile)
                .join(Company, ReportRow.company_id == Company.id)
                .join(Profile, Company.user_id == Profile.id)
                .where(ReportRow.raw_json.isnot(None))
                .order_by(ReportRow.created_at.desc())
            )).all()

            seen_companies: set[str] = set()
            for row, company, user in reports:
                if company.id in seen_companies:
                    continue
                seen_companies.add(company.id)

                report_date = row.created_at
                if report_date.tzinfo is None:
                    report_date = report_date.replace(tzinfo=timezone.utc)

                raw = row.raw_json or {}
                kb_versions = raw.get("knowledge_base_versions", {})

                stale_regs: list[str] = []
                for reg_key, meta in kb_versions.items():
                    fetched_str = meta.get("fetched_at", "")
                    if not fetched_str or fetched_str == "unknown":
                        continue
                    try:
                        kb_fetched = datetime.fromisoformat(
                            fetched_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        continue
                    # Only alert if KB is meaningfully newer (>7 days after report)
                    gap = kb_fetched - report_date
                    if gap > timedelta(days=7):
                        stale_regs.append(reg_key)

                if stale_regs:
                    stale_count += 1
                    reg_names = ", ".join(r.upper() for r in stale_regs[:4])
                    logger.info(
                        "scheduler: company %s has stale report — %d regulation(s) updated since: %s",
                        company.name, len(stale_regs), reg_names,
                    )
                    await _queue_document_ageing_notification(
                        user_id=user.id,
                        user_email=user.email or "",
                        company_name=company.name,
                        stale_regulations=stale_regs,
                        report_date=report_date,
                    )

        logger.info("scheduler: document ageing check complete — %d company(ies) need review", stale_count)

    except Exception as exc:
        logger.error("scheduler: document ageing check failed: %s", exc)


async def _queue_document_ageing_notification(
    user_id: str,
    user_email: str,
    company_name: str,
    stale_regulations: list[str],
    report_date: str,
) -> None:
    """Create and send a document-ageing notification."""
    try:
        from db.database import AsyncSessionLocal
        from db.models import Notification

        reg_list = ", ".join(r.upper() for r in stale_regulations[:5])
        if len(stale_regulations) > 5:
            reg_list += f" and {len(stale_regulations) - 5} more"

        title = f"Your compliance report for {company_name} may be outdated"
        message = (
            f"The following regulations have been updated in the Complio knowledge base since "
            f"your last report ({report_date.strftime('%d %b %Y')}): {reg_list}. "
            f"We recommend re-running the compliance analysis to ensure your report reflects "
            f"the latest legal text. No action is required if no amendments affect your business."
        )

        async with AsyncSessionLocal() as db:
            notif = Notification(
                user_id=user_id,
                type="document_ageing",
                title=title,
                message=message,
            )
            db.add(notif)
            await db.commit()
            await db.refresh(notif)
            notif_id = notif.id

        if user_email:
            from services.notification_service import send_notification_email
            await send_notification_email(
                notification_id=notif_id,
                user_email=user_email,
                company_name=company_name,
                report=None,
                triggered_by="document_ageing",
            )
    except Exception as exc:
        logger.error("scheduler: document ageing notification failed: %s", exc)


async def _fetch_official_updates() -> None:
    """Weekly job: fetch regulations from official sources and stage any changes for review."""
    logger.info("scheduler: starting weekly official regulation fetch")
    try:
        from services.regulation_updater import fetch_and_stage_updates
        pending = await fetch_and_stage_updates()
        if pending:
            logger.info("scheduler: %d regulation(s) staged for review: %s", len(pending), pending)
        else:
            logger.info("scheduler: no regulation changes detected from official sources")
    except Exception as exc:
        logger.error("scheduler: official fetch failed: %s", exc)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler: stopped")
