"""
Ingests company-uploaded documents into a per-job ChromaDB collection.

The collection name is  job_<full-job-id>  — the full UUID, not a truncated
prefix, so two jobs can never collide onto the same collection and leak each
other's documents. It is deleted automatically when the job expires
(JobManager.clear_job_docs).
"""
from __future__ import annotations

import logging
import re
import threading
from pathlib import Path

import chromadb
import pdfplumber

from rag.embeddings import embed_passages
from rag.ingest import CHROMA_DIR

logger = logging.getLogger(__name__)

_MAX_CHUNK_CHARS = 1_200
_MIN_CHUNK_CHARS = 60

# SQLite (embedded ChromaDB) is single-writer. Serialize writes when not using
# the HTTP server, otherwise concurrent jobs corrupt the database.
_chroma_write_lock = threading.Semaphore(1)


def collection_name(job_id: str) -> str:
    return f"job_{job_id}"


def ingest_company_documents(job_id: str, session_id: str) -> int:
    """
    Decrypt, extract, chunk, embed, and index company documents for a job.
    Returns the number of chunks indexed (0 if no files).

    Files are read via document_store.read_file() which decrypts them in memory —
    plaintext bytes never touch disk outside of the temp store.
    """
    from services.document_store import document_store
    enc_paths = document_store.list_files(session_id)
    if not enc_paths:
        return 0

    from rag.ingest import _chroma_client
    col_name   = collection_name(job_id)
    collection = _chroma_client().get_or_create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine"},
    )

    total = 0
    for enc_path in enc_paths:
        # Derive the original filename by stripping the .enc suffix
        original_name = enc_path.stem  # e.g. "policy.pdf"
        try:
            plaintext = document_store.read_file(session_id, original_name)
            text = _extract_bytes(plaintext, original_name)

            # Secondary injection check on extracted text (catches PDF-encoded injections)
            from services.injection_guard import classify_document_for_injection
            is_safe, reason = classify_document_for_injection(text, source_name=original_name)
            if not is_safe:
                logger.warning("company_ingest: blocked %s from RAG pipeline: %s", original_name, reason)
                continue

            chunks = _chunk(text, original_name)
            if not chunks:
                continue

            texts = [c["text"] for c in chunks]
            embeddings = embed_passages(texts)
            ids = [f"{col_name}_{Path(original_name).stem}_{i}" for i in range(len(chunks))]
            from config import settings
            _lock = _chroma_write_lock if not settings.chroma_server_url else None
            if _lock:
                _lock.acquire()
            try:
                collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=[c["metadata"] for c in chunks],
                )
            finally:
                if _lock:
                    _lock.release()
            logger.info("company doc %s: %d chunks", original_name, len(chunks))
            total += len(chunks)
        except Exception as exc:
            logger.warning("company doc %s: skipped (%s)", original_name, exc)

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

def _extract_bytes(content: bytes, filename: str) -> str:
    """Extract text from decrypted file bytes without touching disk."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        import io
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n\n".join(p.strip() for p in pages if p.strip())
    return content.decode("utf-8", errors="replace")


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
