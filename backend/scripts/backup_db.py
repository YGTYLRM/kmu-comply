"""
Back up the Supabase Postgres database via pg_dump.

Usage:
    cd backend
    python scripts/backup_db.py                  # writes data/backups/db_<timestamp>.dump
    python scripts/backup_db.py --out custom.dump

Requires the Postgres client tools (pg_dump) installed and on PATH:
    Windows: https://www.postgresql.org/download/windows/ (or `choco install postgresql`)
    macOS:   brew install postgresql
    Linux:   apt-get install postgresql-client

Requires DATABASE_URL in backend/.env. Restore with:
    pg_restore --clean --no-owner -d <DATABASE_URL> data/backups/db_<timestamp>.dump
"""
import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"


def get_connection_string() -> str:
    from config import settings
    url = settings.database_url
    if not url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    return url.replace("postgresql+asyncpg://", "postgresql://").replace("+asyncpg", "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Back up the Postgres database via pg_dump")
    parser.add_argument("--out", default=None, help="Output file path (default: data/backups/db_<timestamp>.dump)")
    args = parser.parse_args()

    if not shutil.which("pg_dump"):
        print("ERROR: pg_dump not found on PATH. Install the Postgres client tools first (see module docstring).")
        sys.exit(1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.out) if args.out else BACKUP_DIR / f"db_{timestamp}.dump"

    db_url = get_connection_string()
    print(f"Backing up database to {out_path} ...")
    result = subprocess.run(
        ["pg_dump", "--format=custom", f"--file={out_path}", db_url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: pg_dump failed:\n{result.stderr}")
        sys.exit(1)

    print(f"Backup complete: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
