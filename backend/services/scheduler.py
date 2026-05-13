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
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None

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
    For each changed regulation, queue a re-assessment for every company
    that had that regulation apply to them in their last report.
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

    # Queue re-assessments for affected companies
    from services.db_service import get_companies_for_regulation
    for reg_name in changed:
        try:
            companies = await get_companies_for_regulation(reg_name)
            logger.info("scheduler: %s changed — queuing %d companies", reg_name, len(companies))
            for c in companies:
                asyncio.create_task(
                    _run_scheduled_analysis(c, triggered_by="reg_change", reason=f"{reg_name} updated")
                )
        except Exception as exc:
            logger.error("scheduler: error processing regulation %s: %s", reg_name, exc)


# ── Monthly re-assessment ─────────────────────────────────────────────────────

async def monthly_reassessment() -> None:
    """
    Find all companies whose last report is older than 30 days
    and queue a fresh analysis for each one.
    """
    logger.info("scheduler: running monthly re-assessment check")
    try:
        from services.db_service import get_all_companies_due_for_reassessment
        companies = await get_all_companies_due_for_reassessment(interval_days=30)
        logger.info("scheduler: %d companies due for re-assessment", len(companies))
        for c in companies:
            asyncio.create_task(
                _run_scheduled_analysis(c, triggered_by="scheduled", reason="monthly cycle")
            )
    except Exception as exc:
        logger.error("scheduler: monthly re-assessment error: %s", exc)


# ── Shared analysis runner ────────────────────────────────────────────────────

async def _run_scheduled_analysis(company: dict, triggered_by: str, reason: str) -> None:
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

        # Queue notification (Phase 10 will send the actual email)
        await _queue_notification(user_id, company["user_email"], company_name, report, triggered_by)

    except Exception as exc:
        logger.error("scheduler: analysis failed for %s: %s", company_name, exc)


async def _queue_notification(
    user_id: str,
    user_email: str,
    company_name: str,
    report,
    triggered_by: str,
) -> None:
    """Save a notification record to the DB. Phase 10 will handle email delivery."""
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
            db.add(Notification(
                user_id=user_id,
                type=triggered_by,
                title=title,
                message=message,
            ))
            await db.commit()
        logger.info("scheduler: notification queued for %s", user_email)
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

    _scheduler.start()
    logger.info("scheduler: started — regulation check at 03:00 UTC, re-assessments at 04:00 UTC")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler: stopped")
