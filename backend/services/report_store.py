"""
Report persistence — DB is the source of truth when DATABASE_URL is set.
Disk (data/reports/) is kept as a resilience backup and for local-only mode.

Read path:  DB first → disk fallback
Write path: disk always (fast backup); DB write handled by job_manager via db_service
List path:  DB query (O(1)) → disk scan fallback
"""
import json
import logging
from pathlib import Path

from models.compliance_report import ComplianceReport

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"


_MIN_DISK_SPACE_MB = 100


def save(report: ComplianceReport, user_id: str | None = None) -> None:
    """Write report to disk as a resilience backup. DB write is handled by job_manager."""
    import shutil
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        free_mb = shutil.disk_usage(REPORTS_DIR).free / (1024 * 1024)
        if free_mb < _MIN_DISK_SPACE_MB:
            logger.error(
                "report_store: disk space critically low (%.0f MB free) — skipping disk backup for %s",
                free_mb, report.job_id,
            )
            return
    except OSError:
        pass
    path = REPORTS_DIR / f"{report.job_id}.json"
    try:
        data = json.loads(report.model_dump_json())
        if user_id:
            data["_user_id"] = user_id
        path.write_text(json.dumps(data), encoding="utf-8")
        logger.info("report_store: disk backup saved %s", report.job_id)
    except Exception as exc:
        logger.error("report_store: disk backup failed for %s: %s", report.job_id, exc)


def load(job_id: str) -> ComplianceReport | None:
    """Disk-only load — use load_async() in async contexts (avoids event-loop conflicts)."""
    return _load_from_disk(job_id)


async def load_async(job_id: str) -> ComplianceReport | None:
    """Async version of load — preferred in async contexts."""
    from config import settings
    if settings.database_url:
        try:
            raw = await _load_from_db(job_id)
            if raw:
                raw.pop("_user_id", None)
                return ComplianceReport.model_validate(raw)
        except Exception as exc:
            logger.warning("report_store: DB load failed for %s, trying disk: %s", job_id, exc)
    return _load_from_disk(job_id)


def _load_from_disk(job_id: str) -> ComplianceReport | None:
    path = REPORTS_DIR / f"{job_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("_user_id", None)
        return ComplianceReport.model_validate(data)
    except Exception as exc:
        logger.error("report_store: disk load failed for %s: %s", job_id, exc)
        return None


async def _load_from_db(job_id: str) -> dict | None:
    from services.db_service import get_report_by_job_id
    return await get_report_by_job_id(job_id)


def exists(job_id: str) -> bool:
    """Check existence — disk only (sync, called from job_manager status resolution)."""
    return (REPORTS_DIR / f"{job_id}.json").exists()


async def exists_async(job_id: str) -> bool:
    """Async existence check — DB first, disk fallback."""
    from config import settings
    if settings.database_url:
        from services.db_service import report_exists_in_db
        try:
            if await report_exists_in_db(job_id):
                return True
        except Exception:
            pass
    return (REPORTS_DIR / f"{job_id}.json").exists()


def save_profile(job_id: str, profile: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{job_id}_profile.json"
    try:
        path.write_text(json.dumps(profile), encoding="utf-8")
    except Exception as exc:
        logger.error("report_store: failed to save profile %s: %s", job_id, exc)


def load_profile(job_id: str) -> dict | None:
    """Disk-only profile load — use load_profile_async() in async contexts."""
    path = REPORTS_DIR / f"{job_id}_profile.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("report_store: failed to load profile %s: %s", job_id, exc)
        return None


async def load_profile_async(job_id: str) -> dict | None:
    """Load company profile — DB first, disk fallback."""
    from config import settings
    if settings.database_url:
        try:
            result = await _load_profile_from_db(job_id)
            if result:
                return result
        except Exception as exc:
            logger.warning("report_store: DB profile load failed for %s, trying disk: %s", job_id, exc)
    return load_profile(job_id)


async def _load_profile_from_db(job_id: str) -> dict | None:
    """Load company profile_raw from DB via the report's company_id."""
    from db.database import AsyncSessionLocal
    from db.models import Report, Company
    from sqlalchemy import select
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Company.profile_raw)
                .join(Report, Report.company_id == Company.id)
                .where(Report.job_id == job_id)
                .limit(1)
            )
            return result.scalar_one_or_none()
    except Exception:
        return None


def list_recent(limit: int = 50, user_id: str | None = None) -> list[dict]:
    """Disk-only list — use list_recent_async() in async contexts."""
    return _list_from_disk(limit=limit, user_id=user_id)


async def list_recent_async(limit: int = 50, user_id: str | None = None) -> list[dict]:
    """Async version of list_recent — preferred in async contexts."""
    from config import settings
    if settings.database_url and user_id:
        try:
            return await _list_from_db(user_id, limit)
        except Exception as exc:
            logger.warning("report_store: DB list failed, falling back to disk: %s", exc)
    return _list_from_disk(limit=limit, user_id=user_id)


async def _list_from_db(user_id: str, limit: int) -> list[dict]:
    from services.db_service import list_reports_for_user
    return await list_reports_for_user(user_id, limit=limit)


def _list_from_disk(limit: int = 50, user_id: str | None = None) -> list[dict]:
    if not REPORTS_DIR.exists():
        return []
    entries = []
    paths = sorted(
        (p for p in REPORTS_DIR.glob("*.json") if "_" not in p.stem),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in paths:
        if len(entries) >= limit:
            break
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            owner = data.get("_user_id")
            if user_id and owner and owner != user_id:
                continue
            if user_id and not owner:
                continue
            applicable = sum(1 for r in data.get("applicable_regulations", []) if r.get("applies"))
            entries.append({
                "job_id": data["job_id"],
                "company_name": data["company_name"],
                "generated_at": data["generated_at"],
                "overall_score_percent": data["overall_score_percent"],
                "applicable_regulation_count": applicable,
            })
        except Exception as exc:
            logger.warning("report_store: skipping unreadable report %s: %s", path.name, exc)
    return entries
