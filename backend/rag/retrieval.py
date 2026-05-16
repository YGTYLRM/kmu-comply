"""
RAG retrieval module.

  retrieve(query, regulations, top_k=15)  — dense semantic search across collections
  deduplicate(chunks)                      — one chunk per (regulation, article_number)
  rerank(query, chunks, top_n=20)          — LLM-based relevance reranking
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache

import anthropic
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


@lru_cache(maxsize=1)
def _llm_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.llm_api_key)


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


def rerank(query: str, chunks: list[dict], top_n: int = 20) -> list[dict]:
    """LLM-based reranking. Falls back to score order if the API call fails."""
    if not chunks:
        return []
    if not settings.llm_api_key:
        logger.debug("rerank: no LLM API key set, skipping rerank")
        return chunks[:top_n]

    summaries = []
    for i, c in enumerate(chunks):
        preview = (c.get("text") or "")[:300].replace("\n", " ")
        summaries.append(
            f"[{i}] {c.get('regulation','')} {c.get('article_number','')} "
            f"— {c.get('title','')}\n{preview}"
        )

    prompt = (
        "You are a regulatory compliance expert. "
        "Rank the following legal document excerpts by relevance to the query below.\n\n"
        f"Query: {query}\n\n"
        + "\n\n".join(summaries)
        + f"\n\nReturn ONLY a JSON array of the {top_n} most relevant indices "
        "in order from most to least relevant. Example: [3, 0, 7, ...]"
    )

    try:
        response = _llm_client().messages.create(
            model=settings.llm_model,
            max_tokens=512,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        m = re.search(r"\[[\d,\s]+\]", raw)
        if not m:
            logger.warning("rerank: unexpected LLM response format: %s", raw[:80])
            return chunks[:top_n]

        indices: list[int] = json.loads(m.group())
        reranked: list[dict] = []
        used: set[int] = set()
        for idx in indices:
            if isinstance(idx, int) and 0 <= idx < len(chunks) and idx not in used:
                reranked.append(chunks[idx])
                used.add(idx)
            if len(reranked) >= top_n:
                break
        for i, chunk in enumerate(chunks):
            if i not in used and len(reranked) < top_n:
                reranked.append(chunk)
        return reranked

    except Exception as exc:
        logger.warning("rerank: LLM call failed (%s), using score order", exc)
        return chunks[:top_n]
