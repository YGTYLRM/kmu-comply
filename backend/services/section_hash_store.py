"""
Section-level hash store.

Stores {regulation: {article_number: content_hash}} to disk so the scheduler
can report WHICH specific sections changed, not just which regulation file changed.

The content_hash values come from ChromaDB chunk metadata — stamped during ingestion
by rag/ingest.py. For multi-chunk sections the hashes are combined.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_HASH_FILE = Path(__file__).parent.parent / "data" / "section_hashes.json"


# ---------------------------------------------------------------------------
# Build from ChromaDB
# ---------------------------------------------------------------------------

def build_section_hashes(regulation: str) -> dict[str, str]:
    """
    Read all chunks for a regulation from ChromaDB and return
    {article_number: combined_content_hash}.

    For sections split into multiple chunks, chunk hashes are combined so the
    section hash changes if ANY sub-chunk changes.
    """
    try:
        import chromadb
        from rag.ingest import CHROMA_DIR, REGULATION_COLLECTIONS

        col_name = REGULATION_COLLECTIONS.get(regulation)
        if not col_name:
            return {}

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            col = client.get_collection(col_name)
        except Exception:
            return {}

        results = col.get(include=["metadatas"])
        section_hashes: dict[str, str] = {}

        for meta in results["metadatas"] or []:
            article = meta.get("article_number", "").strip()
            chunk_hash = meta.get("content_hash", "").strip()
            if not article or not chunk_hash:
                continue
            if article in section_hashes:
                # Combine hashes deterministically
                combined = section_hashes[article] + ":" + chunk_hash
                section_hashes[article] = hashlib.sha256(combined.encode()).hexdigest()[:16]
            else:
                section_hashes[article] = chunk_hash

        return section_hashes

    except Exception as exc:
        logger.warning("section_hash_store: build failed for %s: %s", regulation, exc)
        return {}


# ---------------------------------------------------------------------------
# Persist
# ---------------------------------------------------------------------------

def load_all() -> dict[str, dict[str, str]]:
    if _HASH_FILE.exists():
        try:
            return json.loads(_HASH_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save(regulation: str, hashes: dict[str, str]) -> None:
    all_hashes = load_all()
    all_hashes[regulation] = hashes
    _HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    _HASH_FILE.write_text(
        json.dumps(all_hashes, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

def diff(
    old: dict[str, str],
    new: dict[str, str],
) -> dict[str, list[str]]:
    """
    Compare two section hash maps and return which articles changed.

    Returns:
        {
            "changed": [...],   # existed before, hash different
            "added":   [...],   # new sections not in old
            "removed": [...],   # sections present in old but gone now
        }
    """
    old_keys = set(old)
    new_keys = set(new)

    changed = sorted(k for k in old_keys & new_keys if old[k] != new[k])
    added   = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)

    return {"changed": changed, "added": added, "removed": removed}


def summarise_diff(regulation: str, diff_result: dict[str, list[str]]) -> str:
    """
    Produce a short human-readable summary of what changed, e.g.:
    "§ 12, § 15 changed · § 3 added"
    """
    parts: list[str] = []
    if diff_result["changed"]:
        parts.append(", ".join(diff_result["changed"]) + " changed")
    if diff_result["added"]:
        parts.append(", ".join(diff_result["added"]) + " added")
    if diff_result["removed"]:
        parts.append(", ".join(diff_result["removed"]) + " removed")
    return " · ".join(parts) if parts else "content updated"
