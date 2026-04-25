"""
Ingest regulatory documents into ChromaDB.

Usage:
  python scripts/ingest_regulations.py --regulation gdpr
  python scripts/ingest_regulations.py --regulation all --reset
  python scripts/ingest_regulations.py --regulation lksg --source path/to/dir
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Run from project root: python scripts/ingest_regulations.py
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

from backend.rag.ingest import REGULATION_COLLECTIONS, ingest_regulation  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest regulatory documents into ChromaDB.")
    parser.add_argument(
        "--regulation",
        choices=list(REGULATION_COLLECTIONS) + ["all"],
        required=True,
        help="Which regulation to ingest, or 'all' for everything.",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Override the default source directory.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the ChromaDB collection before ingesting.",
    )
    args = parser.parse_args()

    regulations = (
        list(REGULATION_COLLECTIONS)
        if args.regulation == "all"
        else [args.regulation]
    )

    total = 0
    for reg in regulations:
        print(f"\n=== {reg} ===")
        source = Path(args.source) if args.source else None
        try:
            n = ingest_regulation(reg, source_dir=source, reset=args.reset)
            print(f"  {n} chunks indexed")
            total += n
        except (FileNotFoundError, ValueError) as exc:
            print(f"  SKIPPED: {exc}")

    print(f"\nDone. Total chunks indexed: {total}")


if __name__ == "__main__":
    main()
