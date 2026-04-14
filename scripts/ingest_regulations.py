"""
Regulatory document ingestion script.

Usage:
  python scripts/ingest_regulations.py --regulation gdpr

Chunks each document at the article/paragraph level and indexes into ChromaDB.
Implemented in Phase 2.
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest regulatory documents into ChromaDB.")
    parser.add_argument("--regulation", choices=["gdpr", "lksg", "enefg", "csrd", "bdsg", "all"], required=True)
    parser.add_argument("--source", default=None)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    print(f"[ingest] not yet implemented. regulation={args.regulation}")
    sys.exit(0)


if __name__ == "__main__":
    main()
