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
    client = _chroma_client()
    results: list[dict] = []

    for regulation in regulations:
        collection_name = REGULATION_COLLECTIONS.get(regulation)
        if not collection_name:
            logger.warning("Unknown regulation key: %s", regulation)
            continue

        try:
            collection = client.get_collection(collection_name)
        except Exception:
            logger.warning("Collection not found: %s (not yet indexed?)", collection_name)
            continue

        count = collection.count()
        if count == 0:
            logger.warning("Empty collection: %s", collection_name)
            continue

        # Use per-collection tuned k, or caller-provided top_k
        k = top_k if top_k is not None else _COLLECTION_TOP_K.get(collection_name, _DEFAULT_TOP_K)
        # Fetch more raw results to allow BM25 re-ranking to surface additional relevant chunks
        raw_k = min(k * 3, count)

        res = collection.query(
            query_embeddings=[query_embedding],
            n_results=raw_k,
            include=["documents", "metadatas", "distances"],
        )

        for doc, meta, dist in zip(
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
        ):
            dense_score = round(1.0 - dist, 4)
            if dense_score < _SIMILARITY_FLOOR:
                continue  # drop below threshold
            bm25 = _bm25_score(query_terms, doc)
            # Combined score: 70% dense, 30% BM25
            combined = round(0.7 * dense_score + 0.3 * bm25, 4)
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
