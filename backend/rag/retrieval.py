"""
RAG retrieval module.

  retrieve(query, regulations, top_k=15)        — dense semantic search across collections
  deduplicate(chunks)                            — one chunk per (regulation, article_number)
  rerank_cross_encoder(query, chunks, top_n=5)  — cross-encoder reranking (active path)
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache

import chromadb

from config import settings
from rag.embeddings import embed_query
from rag.ingest import CHROMA_DIR, REGULATION_COLLECTIONS

# Per-regulation top-k — tuned to collection size and legal breadth
# Broader laws (GDPR, workplace) need more chunks; narrow laws (BDSG, EnEfG) fewer
_COLLECTION_TOP_K: dict[str, int] = {
    "gdpr_dsgvo":     10,
    "bdsg":            6,
    "nis2":            8,
    "eu_ai_act":       8,
    "hinschg":         6,
    "workplace_law":   8,
    "agg":             6,
    "milog":           5,
    "lksg":            6,
    "enefg":           5,
    "csrd":            6,
    "ttdsg":            6,
    "gwg":              6,
    "eu_data_act":      6,
    "compliance_guides": 8,
}
_DEFAULT_TOP_K = 6
_SIMILARITY_FLOOR = 0.35   # drop chunks below this cosine similarity (too far from query)

# Matches a real statute citation (§ N, Art./Artikel/Article N, ESRS N) as an
# article_number value. Discursive guidance prose (BAFA/BaFin/etc.) tends to
# embed closer to natural-language questions than terse law text does —
# without this, guidance systematically outranks the correct statute article
# for ordinary "what must a company do" queries (observed worst on lksg: 5%
# top-5 accuracy in the full retrieval_eval.json baseline). This is a modest,
# additive nudge toward statute text, not an override — see STATUTE_BONUS.
# The citation marker may be preceded by a regulation-name prefix (some
# source files use subsection-level headers like "nis2 Art. 23(4)"), so we
# search rather than anchor strictly to the start of the string.
_RE_STATUTE_CITATION = re.compile(r"(?:^|\s)(§|Art(ikel|icle|\.)?)\s*\d|(?:^|\s)ESRS\s+\S")
_STATUTE_BONUS = 0.2

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------

_chroma: chromadb.PersistentClient | None = None


def _chroma_client():
    global _chroma
    if _chroma is None:
        from config import settings
        if settings.chroma_server_url:
            _chroma = chromadb.HttpClient(host=settings.chroma_server_url)
        else:
            _chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chroma


def _reset_chroma_client() -> None:
    """Force a full reconnect after a segment-reader crash (see retrieve()).

    Observed in this environment: chromadb's embedded PersistentClient keeps a
    per-process vector-segment reader cache with limited capacity. Once a
    long-lived process (a Celery worker handling many companies over its
    lifetime, each touching a different subset of the 14 regulation
    collections) has queried enough *distinct* collections, re-querying one
    queried earlier can fail with `InternalError: Error creating hnsw segment
    reader: Nothing found on disk` — permanently, for that collection, in that
    process. Recreating just the Python PersistentClient object does NOT
    recover it (the broken state lives below the Python client); only
    clearing chromadb's process-wide shared-system cache and reconnecting
    does. Verified this fully recovers the collection and holds up across
    repeated crash/reset cycles.
    """
    global _chroma
    from chromadb.api.shared_system_client import SharedSystemClient
    SharedSystemClient.clear_system_cache()
    _chroma = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _bm25_score(query_terms: list[str], text: str) -> float:
    """Simple BM25-approximation using term frequency. Returns a normalized score 0-1."""
    if not query_terms or not text:
        return 0.0
    text_lower = text.lower()
    words = text_lower.split()
    n = len(words)
    if n == 0:
        return 0.0
    k1, b, avgdl = 1.5, 0.75, 200.0
    score = 0.0
    for term in query_terms:
        tf = text_lower.count(term.lower())
        if tf == 0:
            continue
        tf_norm = tf * (k1 + 1) / (tf + k1 * (1 - b + b * n / avgdl))
        score += tf_norm
    # Normalize to 0-1 range
    return min(1.0, score / (len(query_terms) * (k1 + 1)))


def retrieve(
    query: str,
    regulations: list[str],
    top_k: int | None = None,
) -> list[dict]:
    """Hybrid retrieval: dense vector search + BM25 keyword scoring, merged and filtered.

    top_k: if None, uses per-collection tuned values from _COLLECTION_TOP_K.
    Results are filtered by _SIMILARITY_FLOOR to drop low-relevance chunks.
    Returns chunks sorted by combined score descending.
    Each chunk dict has all metadata fields plus 'score', 'dense_score',
    'bm25_score', and 'collection'.
    """
    if not regulations:
        return []

    query_embedding = embed_query(query)
    query_terms = [t for t in re.sub(r'[^\w\s]', ' ', query.lower()).split() if len(t) > 2]
    results: list[dict] = []

    for regulation in regulations:
        collection_name = REGULATION_COLLECTIONS.get(regulation)
        if not collection_name:
            logger.warning("Unknown regulation key: %s", regulation)
            continue

        client = _chroma_client()
        try:
            collection = client.get_collection(collection_name)
            count = collection.count()
        except Exception:
            logger.warning("Collection not found: %s (not yet indexed?)", collection_name)
            continue

        if count == 0:
            logger.warning("Empty collection: %s", collection_name)
            continue

        # Use per-collection tuned k, or caller-provided top_k
        k = top_k if top_k is not None else _COLLECTION_TOP_K.get(collection_name, _DEFAULT_TOP_K)
        # Fetch more raw results to allow BM25 re-ranking to surface additional relevant chunks
        raw_k = min(k * 3, count)

        try:
            res = collection.query(
                query_embeddings=[query_embedding],
                n_results=raw_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            # See _reset_chroma_client() — a stale segment-reader cache in a
            # long-lived process can break a previously-healthy collection.
            # Reconnect and retry once before giving up on this regulation.
            logger.warning(
                "retrieve: query failed for %s (%s) — resetting ChromaDB client and retrying once",
                collection_name, exc,
            )
            _reset_chroma_client()
            client = _chroma_client()
            try:
                collection = client.get_collection(collection_name)
                res = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=raw_k,
                    include=["documents", "metadatas", "distances"],
                )
            except Exception as retry_exc:
                logger.error(
                    "retrieve: %s still failing after client reset (%s), skipping",
                    collection_name, retry_exc,
                )
                continue

        for doc, meta, dist in zip(
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
        ):
            dense_score = round(1.0 - dist, 4)
            if dense_score < _SIMILARITY_FLOOR:
                continue  # drop below threshold
            bm25 = _bm25_score(query_terms, doc)
            is_statute = bool(_RE_STATUTE_CITATION.search(meta.get("article_number", "")))
            # Combined score: weights sum to 1.0 (56% dense / 24% BM25 / 20%
            # statute bonus) so the max stays in [0, 1] whether or not the
            # bonus applies — same dense:BM25 ratio as before, just rescaled
            # to make room for the bonus term.
            combined = round(
                0.56 * dense_score + 0.24 * bm25 + (_STATUTE_BONUS if is_statute else 0.0),
                4,
            )
            results.append({
                "text":        doc,
                "score":       combined,
                "dense_score": dense_score,
                "bm25_score":  bm25,
                "collection":  collection_name,
                **meta,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def deduplicate(chunks: list[dict]) -> list[dict]:
    """For each (regulation, article_number) pair keep the highest-scoring chunk."""
    best: dict[tuple, dict] = {}
    for chunk in chunks:
        key = (chunk.get("regulation", ""), chunk.get("article_number", ""))
        if key not in best or chunk["score"] > best[key]["score"]:
            best[key] = chunk
    return sorted(best.values(), key=lambda x: x["score"], reverse=True)


@lru_cache(maxsize=1)
def _cross_encoder():
    """Load a multilingual cross-encoder for reranking. Cached after first load (~30s)."""
    try:
        from sentence_transformers import CrossEncoder
        model_name = settings.reranker_model
        model = CrossEncoder(model_name, max_length=512)
        logger.info("retrieval: cross-encoder loaded: %s", model_name)
        return model
    except Exception as exc:
        logger.warning("retrieval: cross-encoder not available (%s), rerank disabled", exc)
        return None


def rerank_cross_encoder(
    query: str,
    chunks: list[dict],
    top_n: int | None = None,
) -> list[dict]:
    """Cross-encoder reranking: score each (query, passage) pair and re-sort.

    Uses a local multilingual cross-encoder (no API cost). Falls back to the
    existing dense+BM25 order if the model is unavailable.
    The cross-encoder is loaded lazily and cached — first call takes ~30s.
    """
    if not chunks:
        return chunks

    model = _cross_encoder()
    if model is None:
        return chunks[:top_n] if top_n else chunks

    pairs = [(query, c.get("text", "")[:512]) for c in chunks]
    try:
        scores = model.predict(pairs)
    except Exception as exc:
        logger.warning("retrieval: cross-encoder predict failed (%s), using score order", exc)
        return chunks[:top_n] if top_n else chunks

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    reranked = sorted(chunks, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
    return reranked[:top_n] if top_n else reranked
