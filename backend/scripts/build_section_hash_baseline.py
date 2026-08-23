"""
Build the initial section hash baseline from the current ChromaDB state.

Run once after ingestion is complete. Subsequent runs are safe — they overwrite
with fresh values (useful after a manual re-ingest to reset the baseline).

Run from backend/:  python scripts/build_section_hash_baseline.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.section_hash_store import build_section_hashes, save

REGULATIONS = [
    "gdpr", "bdsg", "nis2", "eu_ai_act",
    "hinschg", "workplace_law", "agg", "milog",
    "lksg", "enefg", "csrd",
]

print("Building section hash baseline from ChromaDB...\n")

for reg in REGULATIONS:
    hashes = build_section_hashes(reg)
    if hashes:
        save(reg, hashes)
        print(f"  {reg:<15} {len(hashes):>4} sections hashed")
    else:
        print(f"  {reg:<15}  NOT FOUND in ChromaDB — skipping")

print("\nBaseline saved to data/section_hashes.json")
print("The scheduler will diff against this on the next daily regulation check.")
