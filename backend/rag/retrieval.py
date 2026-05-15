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

def retrieve(
    query: str,
    regulations: list[str],
    top_k: int = 15,
) -> list[dict]:
    """Dense semantic search across the given regulation collections.

    Returns chunks sorted by cosine similarity score descending.
    Each chunk dict has all metadata fields plus 'score' and 'collection'.
    """
    if not regulations:
        return []

    query_embedding = embed_query(query)
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

        res = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        for doc, meta, dist in zip(
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
        ):
            results.append({
                "text": doc,
                "score": round(1.0 - dist, 4),
                "collection": collection_name,
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
