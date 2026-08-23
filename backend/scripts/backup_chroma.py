"""
Back up the local ChromaDB persistence directory (backend/data/chroma_db).

Usage:
    cd backend
    python scripts/backup_chroma.py                 # writes data/backups/chroma_<timestamp>.tar.gz
    python scripts/backup_chroma.py --out custom.tar.gz

Restore by extracting the archive back into backend/data/chroma_db
(with the backend stopped, so nothing is writing to it mid-restore).
"""
import argparse
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"


def main() -> None:
    parser = argparse.ArgumentParser(description="Back up the ChromaDB persistence directory")
    parser.add_argument("--out", default=None, help="Output archive path (default: data/backups/chroma_<timestamp>.tar.gz)")
    args = parser.parse_args()

    if not CHROMA_DIR.exists():
        print(f"ERROR: {CHROMA_DIR} does not exist — nothing to back up.")
        sys.exit(1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.out) if args.out else BACKUP_DIR / f"chroma_{timestamp}.tar.gz"

    print(f"Archiving {CHROMA_DIR} to {out_path} ...")
    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(CHROMA_DIR, arcname="chroma_db")

    print(f"Backup complete: {out_path} ({out_path.stat().st_size / (1024 * 1024):.1f} MB)")


if __name__ == "__main__":
    main()
