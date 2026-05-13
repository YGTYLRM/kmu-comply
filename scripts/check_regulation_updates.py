"""
Check regulation source files for changes and re-ingest any that have been updated.

How it works:
  1. Computes SHA-256 of every source file in backend/data/regulations/<reg>/
  2. Compares against checksums stored in backend/data/reg_checksums.json
  3. Re-ingests (with reset=True) any regulation whose files have changed
  4. Updates the checksum file after each successful re-ingestion

Usage:
  python scripts/check_regulation_updates.py           # check all, re-ingest changed
  python scripts/check_regulation_updates.py --dry-run # report changes only, no re-ingestion
  python scripts/check_regulation_updates.py --force   # re-ingest everything regardless

Run from the project root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from backend.rag.ingest import DATA_DIR, REGULATION_COLLECTIONS, ingest_regulation  # noqa: E402

CHECKSUM_FILE = Path(__file__).parent.parent / "backend" / "data" / "reg_checksums.json"


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _dir_checksums(regulation: str) -> dict[str, str]:
    """Return {filename: sha256} for all source files of a regulation."""
    src = DATA_DIR / regulation
    if not src.exists():
        return {}
    return {
        f.name: _file_hash(f)
        for f in sorted(src.iterdir())
        if f.suffix in (".txt", ".pdf") and not f.name.startswith(".")
    }


def _load_stored() -> dict[str, dict[str, str]]:
    if CHECKSUM_FILE.exists():
        try:
            return json.loads(CHECKSUM_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_stored(checksums: dict[str, dict[str, str]]) -> None:
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUM_FILE.write_text(json.dumps(checksums, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect and re-ingest changed regulation sources.")
    parser.add_argument("--dry-run", action="store_true", help="Report changes only, do not re-ingest")
    parser.add_argument("--force",   action="store_true", help="Re-ingest all regulations regardless of changes")
    args = parser.parse_args()

    regulations = [
        k for k in REGULATION_COLLECTIONS
        if k not in ("gdpr_dsgvo", "compliance_guides")  # aliases / secondary
    ]

    stored = _load_stored()
    changed: list[str] = []
    unchanged: list[str] = []
    missing: list[str] = []

    for reg in regulations:
        current = _dir_checksums(reg)
        if not current:
            missing.append(reg)
            continue
        if args.force or stored.get(reg) != current:
            changed.append(reg)
        else:
            unchanged.append(reg)

    logger.info("Unchanged: %s", unchanged or "none")
    logger.info("Changed:   %s", changed or "none")
    if missing:
        logger.warning("No source files found for: %s", missing)

    if not changed:
        logger.info("Nothing to re-ingest.")
        return

    if args.dry_run:
        logger.info("Dry run — skipping re-ingestion.")
        return

    for reg in changed:
        logger.info("Re-ingesting %s ...", reg)
        try:
            count = ingest_regulation(reg, reset=True)
            logger.info("  %s: %d chunks indexed", reg, count)
            stored[reg] = _dir_checksums(reg)
            _save_stored(stored)
        except Exception as exc:
            logger.error("  %s: re-ingestion failed: %s", reg, exc)

    logger.info("Done. Checksum file updated: %s", CHECKSUM_FILE)


if __name__ == "__main__":
    main()
