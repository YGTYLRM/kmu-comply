"""
Disk-based report persistence.

Reports are stored at data/reports/{job_id}.json.
The _user_id field inside the JSON records the owner — never return
a report to a user whose ID doesn't match.
"""
import json
import logging
from pathlib import Path

from models.compliance_report import ComplianceReport

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"

# Pattern: only actual report files, not *_profile.json side-cars
_REPORT_GLOB = "[0-9a-zA-Z]*-[0-9a-zA-Z]*.json"


def save(report: ComplianceReport, user_id: str | None = None) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{report.job_id}.json"
    try:
        data = json.loads(report.model_dump_json())
        if user_id:
            data["_user_id"] = user_id
        path.write_text(json.dumps(data), encoding="utf-8")
        logger.info("report_store: saved %s (owner=%s)", report.job_id, user_id)
    except Exception as exc:
        logger.error("report_store: failed to save %s: %s", report.job_id, exc)


def load(job_id: str) -> ComplianceReport | None:
    path = REPORTS_DIR / f"{job_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("_user_id", None)  # strip internal field before parsing
        return ComplianceReport.model_validate(data)
    except Exception as exc:
        logger.error("report_store: failed to load %s: %s", job_id, exc)
        return None


def exists(job_id: str) -> bool:
    return (REPORTS_DIR / f"{job_id}.json").exists()


def get_owner(job_id: str) -> str | None:
    """Return the user_id that owns this report, or None if unknown (legacy)."""
    path = REPORTS_DIR / f"{job_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("_user_id")
    except Exception:
        return None


def load_all_owners() -> dict[str, str]:
    """Rebuild the job_id → user_id map from disk on startup."""
    if not REPORTS_DIR.exists():
        return {}
    owners: dict[str, str] = {}
    for path in REPORTS_DIR.glob("*.json"):
        if "_profile" in path.name or "_owner" in path.name:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            uid = data.get("_user_id")
            jid = data.get("job_id")
            if uid and jid:
                owners[jid] = uid
        except Exception:
            pass
    return owners


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


def list_recent(limit: int = 50, user_id: str | None = None) -> list[dict]:
    """Return summary metadata for recent reports, scoped to user_id if given."""
    if not REPORTS_DIR.exists():
        return []
    entries = []
    # Exclude _profile.json and other side-car files
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
            # Filter: skip reports that belong to a different user
            if user_id and owner and owner != user_id:
                continue
            # Skip legacy unowned reports when user filtering is active
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
