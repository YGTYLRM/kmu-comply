"""
Re-ingest all regulation collections into ChromaDB from scratch.

Run from backend/:  python scripts/ingest_all.py

Use --regulation <name> to re-ingest a single collection.
Use --dry-run to show what would be ingested without writing to ChromaDB.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.ingest import ingest_regulation, DATA_DIR, REGULATION_COLLECTIONS

ALL_REGULATIONS = [
    "gdpr",
    "bdsg",
    "lksg",
    "enefg",
    "nis2",
    "eu_ai_act",
    "csrd",
    "hinschg",
    "workplace_law",
    "agg",
    "milog",
    "compliance_guides",
]


def normalize_gesetze_file(path: Path) -> bool:
    """Normalize \xa0 between section number and title. Returns True if file was changed."""
    text = path.read_text(encoding="utf-8")
    normalized = re.sub(r'(?m)(^§\s*\d+[a-z]?)\xa0', r'\1\n', text)
    if normalized != text:
        path.write_text(normalized, encoding="utf-8")
        return True
    return False


def check_source_files(regulation: str) -> int:
    folder = DATA_DIR / ("arbschg" if regulation == "workplace_law" else regulation)
    if not folder.exists():
        return 0
    return sum(1 for f in folder.iterdir() if f.suffix in (".txt", ".pdf"))


def main():
    parser = argparse.ArgumentParser(description="Re-ingest all regulations into ChromaDB")
    parser.add_argument("--regulation", help="Only re-ingest this one regulation")
    parser.add_argument("--dry-run", action="store_true", help="Show source files without ingesting")
    parser.add_argument("--no-normalize", action="store_true", help="Skip \xa0 normalization step")
    args = parser.parse_args()

    targets = [args.regulation] if args.regulation else ALL_REGULATIONS

    for reg in targets:
        if reg not in REGULATION_COLLECTIONS:
            print(f"Unknown regulation: {reg}")
            continue

        folder = DATA_DIR / ("arbschg" if reg == "workplace_law" else reg)
        file_count = check_source_files(reg)

        print(f"\n{'='*60}")
        print(f"Regulation: {reg}  |  source folder: {folder.name}  |  files: {file_count}")

        if file_count == 0:
            print("  SKIP — no source files found. Run fetch_supplementary_docs.py first.")
            continue

        # Normalize \xa0 in German law text files
        if not args.no_normalize and folder.exists():
            for f in folder.glob("*.txt"):
                changed = normalize_gesetze_file(f)
                if changed:
                    print(f"  Normalized \\xa0 in {f.name}")

        if args.dry_run:
            for f in folder.iterdir():
                if f.suffix in (".txt", ".pdf"):
                    size_kb = f.stat().st_size // 1024
                    print(f"  Would ingest: {f.name} ({size_kb}KB)")
            continue

        try:
            n = ingest_regulation(reg, reset=True)
            status = f"{n} chunks" if n > 0 else "WARNING: 0 chunks — check source files"
            print(f"  Done: {status}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if not args.dry_run:
        print(f"\n{'='*60}")
        print("Final ChromaDB counts:")
        try:
            import chromadb
            from rag.ingest import CHROMA_DIR
            from config import settings
            if settings.chroma_server_url:
                client = chromadb.HttpClient(host=settings.chroma_server_url)
            else:
                client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            for reg in targets:
                if reg not in REGULATION_COLLECTIONS:
                    continue
                coll_name = REGULATION_COLLECTIONS[reg]
                try:
                    col = client.get_collection(coll_name)
                    print(f"  {reg:<20} {col.count():>5} chunks  (collection: {coll_name})")
                except Exception:
                    print(f"  {reg:<20}     0 chunks  (not found)")
        except Exception as e:
            print(f"  Could not connect to ChromaDB: {e}")


if __name__ == "__main__":
    main()
