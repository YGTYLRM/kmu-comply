"""
Disk-based report persistence.

Completed reports are written as JSON to data/reports/{job_id}.json.
The in-memory job cache may evict jobs after its TTL, but the report
file remains on disk indefinitely and is served from there on future requests.
"""
import json
import logging
from pathlib import Path

from models.compliance_report import ComplianceReport

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"


def save(report: ComplianceReport) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{report.job_id}.json"
    try:
        path.write_text(report.model_dump_json(), encoding="utf-8")
        logger.info("report_store: saved %s", report.job_id)
    except Exception as exc:
        logger.error("report_store: failed to save %s: %s", report.job_id, exc)


def load(job_id: str) -> ComplianceReport | None:
    path = REPORTS_DIR / f"{job_id}.json"
    if not path.exists():
        return None
    try:
        return ComplianceReport.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("report_store: failed to load %s: %s", job_id, exc)
        return None


def exists(job_id: str) -> bool:
    return (REPORTS_DIR / f"{job_id}.json").exists()


def save_profile(job_id: str, profile: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{job_id}_profile.json"
    try:
        path.write_text(json.dumps(profile), encoding="utf-8")
    except Exception as exc:
        logger.error("report_store: failed to save profile %s: %s", job_id, exc)


def load_profile(job_id: str) -> dict | None:
    path = REPORTS_DIR / f"{job_id}_profile.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("report_store: failed to load profile %s: %s", job_id, exc)
        return None


def list_recent(limit: int = 50) -> list[dict]:
    """Return summary metadata for the most recently created reports."""
    if not REPORTS_DIR.exists():
        return []
    entries = []
    paths = sorted(REPORTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in paths[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
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
