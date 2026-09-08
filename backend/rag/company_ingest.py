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
            _upsert_pgvector_company_chunks(job_id, original_name, chunks, embeddings)
        except Exception as exc:
            logger.warning("company doc %s: skipped (%s)", original_name, exc)

    logger.info("job %s: %d company doc chunks indexed in %s", job_id, total, col_name)
    return total


def _upsert_pgvector_company_chunks(
    job_id: str, source_file: str, chunks: list[dict], embeddings: list[list[float]],
) -> None:
    """Dual-write company-doc chunks to the pgvector-backed company_doc_chunks
    table alongside the ChromaDB write above, mirroring rag/ingest.py's
    _upsert_pgvector_chunks pattern for static regulations. Purely additive —
    ChromaDB (via retrieve_company_docs) remains the only read path; nothing
    reads company_doc_chunks yet. A plain insert (no upsert) is correct here:
    each job_id is created once per analysis run and ingest_company_documents
    is only ever called once per job, so there's no re-ingestion case to dedupe.

    No-ops if DATABASE_URL isn't configured. Never raises — a pgvector write
    failure must not affect the ChromaDB write that's actually serving
    retrieval, same rationale as the static-regulation dual-write.
    """
    from config import settings
    if not settings.database_url:
        return
    import asyncio
    try:
        asyncio.run(_upsert_pgvector_company_chunks_async(job_id, source_file, chunks, embeddings))
    except Exception as exc:
        logger.warning(
            "pgvector dual-write failed for job %s / %s (%d chunks) — skipped, ChromaDB "
            "write above already succeeded: %s", job_id, source_file, len(chunks), exc,
        )


async def _upsert_pgvector_company_chunks_async(
    job_id: str, source_file: str, chunks: list[dict], embeddings: list[list[float]],
) -> None:
    import uuid
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from config import settings
    from db.models import CompanyDocChunk

    # Dedicated short-lived engine, not db.database's module-level singleton —
    # this function is reached via asyncio.run() from a thread-pool executor
    # call (ingest_company_documents is sync, invoked through
    # loop.run_in_executor), so it gets a fresh event loop each time. Reusing
    # the app's shared engine across separate event loops hits "Event loop is
    # closed" the moment a pooled connection from a prior loop is reused —
    # same issue documented in rag/ingest.py's dual-write.
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    rows = [
        CompanyDocChunk(
            id=str(uuid.uuid4()),
            job_id=job_id,
            source_file=source_file,
            content=c["text"],
            embedding=emb,
            metadata_extra=c["metadata"],
        )
        for c, emb in zip(chunks, embeddings)
    ]

    try:
        async with AsyncSessionLocal() as db:
            db.add_all(rows)
            await db.commit()
    finally:
        await engine.dispose()


def _delete_pgvector_company_chunks(job_id: str) -> None:
    """Mirror-delete a job's pgvector-backed company-doc chunks. Matched 1:1
    with the ChromaDB delete in delete_company_docs below — writing to
    company_doc_chunks without also deleting from it on job-TTL expiry would
    leave uploaded-document content (potentially PII) in Postgres past its
    ChromaDB retention window, which is a real data-retention correctness
    issue for a product whose own job is GDPR compliance. No-ops if
    DATABASE_URL isn't configured. Never raises."""
    from config import settings
    if not settings.database_url:
        return
    import asyncio
    try:
        asyncio.run(_delete_pgvector_company_chunks_async(job_id))
    except Exception as exc:
        logger.warning("pgvector delete failed for job %s company docs: %s", job_id, exc)


async def _delete_pgvector_company_chunks_async(job_id: str) -> None:
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from config import settings
    from db.models import CompanyDocChunk

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(CompanyDocChunk).where(CompanyDocChunk.job_id == job_id))
            await db.commit()
    finally:
        await engine.dispose()


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
    _delete_pgvector_company_chunks(job_id)


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
