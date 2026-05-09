"""
Ingests company-uploaded documents into a per-job ChromaDB collection.

The collection name is  job_<first-8-chars-of-job-id>  so it stays short.
It is deleted automatically when the job expires (JobManager.clear_job_docs).
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import chromadb
import pdfplumber

from rag.embeddings import embed_passages
from rag.ingest import CHROMA_DIR

logger = logging.getLogger(__name__)

_MAX_CHUNK_CHARS = 1_200
_MIN_CHUNK_CHARS = 60


def collection_name(job_id: str) -> str:
    return f"job_{job_id[:8]}"


def ingest_company_documents(job_id: str, file_paths: list[Path]) -> int:
    """
    Extract, chunk, embed, and index company documents.
    Returns the number of chunks indexed (0 if no files).
    """
    if not file_paths:
        return 0

    col_name = collection_name(job_id)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine"},
    )

    total = 0
    for path in file_paths:
        try:
            text = _extract(path)
            chunks = _chunk(text, path.name)
            if not chunks:
                continue

            texts = [c["text"] for c in chunks]
            embeddings = embed_passages(texts)
            ids = [f"{col_name}_{path.stem}_{i}" for i in range(len(chunks))]
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=[c["metadata"] for c in chunks],
            )
            logger.info("company doc %s: %d chunks", path.name, len(chunks))
            total += len(chunks)
        except Exception as exc:
            logger.warning("company doc %s: skipped (%s)", path.name, exc)

    logger.info("job %s: %d company doc chunks indexed in %s", job_id, total, col_name)
    return total


def retrieve_company_docs(job_id: str, query: str, top_k: int = 8) -> list[dict]:
    """
    Query the per-job company document collection.
    Returns an empty list if the collection does not exist.
    """
    col_name = collection_name(job_id)
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        existing = {c.name for c in client.list_collections()}
        if col_name not in existing:
            return []

        collection = client.get_collection(col_name)
        if collection.count() == 0:
            return []

        from rag.embeddings import embed_passages
        query_embedding = embed_passages([f"query: {query}"])[0]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({
                "text": doc,
                "source": meta.get("source_file", "uploaded document"),
                "score": 1 - dist,
            })
        return chunks
    except Exception as exc:
        logger.warning("company doc retrieval failed for job %s: %s", job_id, exc)
        return []


def delete_company_docs(job_id: str) -> None:
    col_name = collection_name(job_id)
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        existing = {c.name for c in client.list_collections()}
        if col_name in existing:
            client.delete_collection(col_name)
            logger.debug("deleted company doc collection %s", col_name)
    except Exception as exc:
        logger.warning("failed to delete company doc collection %s: %s", col_name, exc)


# ── Text extraction ────────────────────────────────────────────────────────────

def _extract(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        with pdfplumber.open(str(path)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n\n".join(p.strip() for p in pages if p.strip())
    return path.read_text(encoding="utf-8", errors="replace")


# ── Chunking ───────────────────────────────────────────────────────────────────

_RE_SECTION = re.compile(
    r"(?m)^(?:§\s*\d+|Art(?:icle|ikel)?\s*\d+|\d+\.|\b[A-Z][A-Z\s]{3,40})\s*\n"
)


def _chunk(text: str, filename: str) -> list[dict]:
    """
    Split on structural markers where possible, fall back to paragraph chunks.
    Each chunk carries metadata with the source filename for citation.
    """
    # Try structural split
    boundaries = [m.start() for m in _RE_SECTION.finditer(text)]
    if len(boundaries) >= 3:
        segments = []
        for i, start in enumerate(boundaries):
            end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
            segments.append(text[start:end].strip())
    else:
        # Paragraph split
        segments = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    chunks = []
    buffer = ""
    for seg in segments:
        if len(buffer) + len(seg) < _MAX_CHUNK_CHARS:
            buffer = (buffer + "\n\n" + seg).strip()
        else:
            if len(buffer) >= _MIN_CHUNK_CHARS:
                chunks.append(_make(buffer, filename))
            buffer = seg

    if len(buffer) >= _MIN_CHUNK_CHARS:
        chunks.append(_make(buffer, filename))

    return chunks


def _make(text: str, filename: str) -> dict:
    return {
        "text": text,
        "metadata": {
            "source_file": filename,
            "document_type": "company_document",
        },
    }
