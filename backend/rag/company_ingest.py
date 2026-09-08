"""
Ingests company-uploaded documents into a per-job ChromaDB collection.

The collection name is  job_<full-job-id>  — the full UUID, not a truncated
prefix, so two jobs can never collide onto the same collection and leak each
other's documents. It is deleted automatically when the job expires
(JobManager.clear_job_docs).

Chunk text is encrypted at rest (Fernet, same key/helper as document_store.py)
in both ChromaDB's documents field and pgvector's company_doc_chunks.content —
the original uploaded file was already encrypted at rest, but the chunked
text derived from it for RAG was being stored in plaintext in both vector
stores until this was found during a GDPR self-audit. Embeddings are still
computed on the plaintext (semantic search needs that); only the stored text
payload is encrypted. Decrypted transparently in retrieve_company_docs, with
a fallback to treat undecryptable values as legacy plaintext chunks ingested
before this was added, rather than erroring on them.
"""
from __future__ import annotations

import logging
import re
import threading
from pathlib import Path

import pdfplumber

from rag.embeddings import embed_passages

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
            embeddings = embed_passages(texts)  # computed on plaintext — semantic search needs this
            from services.document_store import _fernet
            encrypted_texts = [_fernet().encrypt(t.encode()).decode() for t in texts]
            ids = [f"{col_name}_{Path(original_name).stem}_{i}" for i in range(len(chunks))]
            from config import settings
            _lock = _chroma_write_lock if not settings.chroma_server_url else None
            if _lock:
                _lock.acquire()
            try:
                collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=encrypted_texts,
                    metadatas=[c["metadata"] for c in chunks],
                )
            finally:
                if _lock:
                    _lock.release()
            logger.info("company doc %s: %d chunks", original_name, len(chunks))
            total += len(chunks)
            encrypted_chunks = [
                {"text": et, "metadata": c["metadata"]} for et, c in zip(encrypted_texts, chunks)
            ]
            _upsert_pgvector_company_chunks(job_id, original_name, encrypted_chunks, embeddings)
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
    reads company_doc_chunks yet. `chunks[i]["text"]` is expected to already
    be Fernet-encrypted by the caller — this function just stores whatever
    text it's given, same as the ChromaDB write. A plain insert (no upsert) is correct here:
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
    DATABASE_URL isn't configured. Never raises.

    Unlike the write side (_upsert_pgvector_company_chunks, only ever reached
    via loop.run_in_executor from compliance_agent.py, so it's always in a
    thread with no running loop), delete_company_docs below is called
    directly from *already-async* contexts — job_manager.py's periodic
    cleanup loop, and routes/companies.py's account-deletion endpoint — where
    a plain asyncio.run() raises "cannot be called from a running event
    loop". Found via a live self-audit test of account deletion, not by
    inspection: the isolated dual-write verification script in Session 31
    only ever ran outside any event loop, so it never exercised this path.
    Detect which situation applies and dispatch accordingly instead of
    assuming one or the other.
    """
    from config import settings
    if not settings.database_url:
        return
    import asyncio
    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_delete_pgvector_company_chunks_async(job_id))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(asyncio.run, _delete_pgvector_company_chunks_async(job_id)).result()
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
    """Company-doc retrieval entry point — dispatches to pgvector or ChromaDB,
    mirroring agent/planning.py::retrieve()'s dispatch logic for static
    regulations exactly (same settings.pgvector_retrieval_enabled flag, same
    PGVECTOR_KILL_SWITCH_FILE check, same "no DATABASE_URL configured" chroma
    fallback for local dev). One kill switch governs both retrieval paths —
    if pgvector is degraded, it's degraded for both, so there's no reason for
    two independent flags."""
    from config import settings, PGVECTOR_KILL_SWITCH_FILE
    if PGVECTOR_KILL_SWITCH_FILE.exists():
        return _retrieve_company_docs_chroma(job_id, query, top_k)
    if settings.pgvector_retrieval_enabled and settings.database_url:
        return retrieve_company_docs_pgvector(job_id, query, top_k)
    return _retrieve_company_docs_chroma(job_id, query, top_k)


def _retrieve_company_docs_chroma(job_id: str, query: str, top_k: int = 8) -> list[dict]:
    """
    Query the per-job company document collection in ChromaDB.
    Returns an empty list if the collection does not exist.
    """
    col_name = collection_name(job_id)
    try:
        from rag.ingest import _chroma_client
        client = _chroma_client()
        existing = {c.name for c in client.list_collections()}
        if col_name not in existing:
            return []

        collection = client.get_collection(col_name)
        if collection.count() == 0:
            return []

        from rag.embeddings import embed_query
        query_embedding = embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        from services.document_store import _fernet
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            try:
                text = _fernet().decrypt(doc.encode()).decode()
            except Exception:
                # Legacy chunk ingested before encryption was added — stored
                # as plaintext, so decryption fails; use it as-is rather than
                # dropping the chunk or erroring the whole retrieval.
                text = doc
            chunks.append({
                "text": text,
                "source": meta.get("source_file", "uploaded document"),
                "score": 1 - dist,
            })
        return chunks
    except Exception as exc:
        logger.warning("company doc retrieval failed for job %s: %s", job_id, exc)
        return []


def retrieve_company_docs_pgvector(job_id: str, query: str, top_k: int = 8) -> list[dict]:
    """pgvector-backed mirror of _retrieve_company_docs_chroma — same dict
    shape, same decrypt-with-legacy-fallback behavior. Only the raw ANN fetch
    differs (SQL cosine-distance query against company_doc_chunks instead of
    ChromaDB's collection.query()), mirroring rag/retrieval.py::retrieve_pgvector's
    pattern for static regulations. Reuses that module's persistent background-
    loop-thread + shared engine (rag.retrieval._get_loop_thread/_get_pg_engine)
    rather than a fresh asyncio.run() per call or a second connection pool —
    both are generic "run an async pg query from sync code" helpers, not
    specific to RegulationChunk."""
    try:
        from rag.embeddings import embed_query
        from rag.retrieval import _get_loop_thread
        from services.document_store import _fernet

        query_embedding = embed_query(query)
        rows = _get_loop_thread().run(_pg_query_company_docs_one(job_id, query_embedding, top_k))
        if not rows:
            return []

        chunks = []
        for row in rows:
            try:
                text = _fernet().decrypt(row["content"].encode()).decode()
            except Exception:
                text = row["content"]  # legacy plaintext chunk, see _retrieve_company_docs_chroma
            meta = row["metadata_extra"] or {}
            chunks.append({
                "text": text,
                "source": meta.get("source_file", "uploaded document"),
                "score": 1 - row["distance"],
            })
        return chunks
    except Exception as exc:
        logger.warning("company doc retrieval (pgvector) failed for job %s: %s", job_id, exc)
        return []


async def _pg_query_company_docs_one(job_id: str, query_embedding: list[float], top_k: int) -> list[dict]:
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import AsyncSession
    from db.models import CompanyDocChunk
    from rag.retrieval import _get_pg_engine

    engine = await _get_pg_engine()
    async with AsyncSession(engine) as db:
        count = (await db.execute(
            select(func.count()).where(CompanyDocChunk.job_id == job_id)
        )).scalar_one()
        if count == 0:
            return []
        k = min(top_k, count)

        distance = CompanyDocChunk.embedding.cosine_distance(query_embedding)
        stmt = (
            select(CompanyDocChunk, distance.label("distance"))
            .where(CompanyDocChunk.job_id == job_id)
            .order_by(distance)
            .limit(k)
        )
        rows = (await db.execute(stmt)).all()

    return [
        {"content": chunk.content, "metadata_extra": chunk.metadata_extra, "distance": dist}
        for chunk, dist in rows
    ]


def delete_company_docs(job_id: str) -> None:
    col_name = collection_name(job_id)
    try:
        from rag.ingest import _chroma_client
        client = _chroma_client()
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
