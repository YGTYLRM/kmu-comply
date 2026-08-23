"""
Nightly backup wrapper: runs backup_db.py + backup_chroma.py, then prunes
local backups older than RETENTION_DAYS so data/backups/ doesn't grow
unbounded on local disk.

This only writes to local disk (backend/data/backups/) — it does NOT ship
anything off-host. If the machine's disk is lost, these backups are lost
too. Shipping to S3/Backblaze/etc. needs real credentials for an off-host
account, which isn't something this script can set up on its own; wire in
a real upload step here once those credentials exist.

Registered as a nightly Windows Scheduled Task ("Complio Nightly Backup",
02:00 local time) — see scripts/register_backup_task.ps1.

Usage:
    cd backend
    python scripts/backup_nightly.py
"""
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
BACKUP_DIR = BACKEND_DIR / "data" / "backups"
RETENTION_DAYS = 14


def run(script: str) -> bool:
    result = subprocess.run(
        [sys.executable, str(BACKEND_DIR / "scripts" / script)],
        cwd=str(BACKEND_DIR),
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR running {script}:\n{result.stderr}", file=sys.stderr)
        return False
    return True


def prune_old_backups() -> None:
    if not BACKUP_DIR.exists():
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    for f in BACKUP_DIR.iterdir():
        if not f.is_file():
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            print(f"Pruning old backup: {f.name}")
            f.unlink()


def main() -> None:
    print(f"=== Nightly backup started {datetime.now(timezone.utc).isoformat()} ===")
    start = time.monotonic()

    db_ok = run("backup_db.py")
    chroma_ok = run("backup_chroma.py")
    prune_old_backups()

    elapsed = time.monotonic() - start
    print(f"=== Nightly backup finished in {elapsed:.0f}s (db={'ok' if db_ok else 'FAILED'}, "
          f"chroma={'ok' if chroma_ok else 'FAILED'}) ===")

    if not (db_ok and chroma_ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
