"""
Chunk quality inspector.

Samples N random chunks per regulation collection and prints them
for manual review. Checks for: encoding issues, empty chunks,
very short chunks, broken section markers, missing metadata.

Run from backend/:  python scripts/inspect_chunks.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
SAMPLE_N = 5

COLLECTIONS = [
    "gdpr_dsgvo", "bdsg", "nis2", "eu_ai_act",
    "hinschg", "workplace_law", "agg", "milog",
    "lksg", "enefg", "csrd",
]

WARN_SHORT = 100   # chars — suspiciously short chunk
WARN_LONG  = 8000  # chars — suspiciously long chunk (probably not split)


def check_chunk(text: str, meta: dict) -> list[str]:
    issues = []
    if len(text) < WARN_SHORT:
        issues.append(f"VERY SHORT ({len(text)} chars)")
    if len(text) > WARN_LONG:
        issues.append(f"VERY LONG ({len(text)} chars) — may need splitting")
    if "�" in text:
        issues.append("ENCODING ERROR (replacement char found)")
    if text.count("\n\n\n") > 3:
        issues.append("EXCESSIVE BLANK LINES")
    if not any(c.isalpha() for c in text):
        issues.append("NO ALPHABETIC CONTENT")
    return issues


def main():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    existing = {c.name for c in client.list_collections()}

    summary: dict[str, dict] = {}

    for col_name in COLLECTIONS:
        print(f"\n{'='*70}")
        print(f"  COLLECTION: {col_name}")
        print(f"{'='*70}")

        if col_name not in existing:
            print("  !! NOT FOUND IN CHROMADB")
            summary[col_name] = {"status": "MISSING", "count": 0, "issues": 0}
            continue

        col = client.get_collection(col_name)
        total = col.count()
        print(f"  Total chunks: {total}")

        if total == 0:
            print("  !! EMPTY COLLECTION")
            summary[col_name] = {"status": "EMPTY", "count": 0, "issues": 0}
            continue

        # Sample random IDs
        all_results = col.get(limit=total, include=["documents", "metadatas"])
        ids = all_results["ids"]
        docs = all_results["documents"]
        metas = all_results["metadatas"]

        indices = random.sample(range(len(ids)), min(SAMPLE_N, len(ids)))
        issue_count = 0

        for idx in indices:
            text = docs[idx] or ""
            meta = metas[idx] or {}
            issues = check_chunk(text, meta)
            if issues:
                issue_count += 1

            print(f"\n  --- Chunk {idx+1}/{total} ---")
            print(f"  ID       : {ids[idx]}")
            print(f"  Metadata : {meta}")
            print(f"  Length   : {len(text)} chars")
            if issues:
                print(f"  ISSUES   : {', '.join(issues)}")
            print(f"  Text preview (first 400 chars):")
            print("  " + text[:400].replace("\n", "\n  "))
            if len(text) > 400:
                print(f"  ... [{len(text)-400} more chars]")

        summary[col_name] = {
            "status": "OK" if issue_count == 0 else "ISSUES",
            "count": total,
            "issues": issue_count,
        }

    # Summary table
    print(f"\n\n{'='*70}")
    print("  SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Collection':<20} {'Status':<10} {'Chunks':>7}  {'Sampled Issues':>14}")
    print(f"  {'-'*20} {'-'*10} {'-'*7}  {'-'*14}")
    for col_name, info in summary.items():
        flag = "!!" if info["status"] != "OK" else "  "
        print(f"  {flag} {col_name:<18} {info['status']:<10} {info['count']:>7}  {info['issues']:>14}/{SAMPLE_N}")


if __name__ == "__main__":
    random.seed(42)
    main()
