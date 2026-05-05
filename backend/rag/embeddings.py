"""
Embedding model wrapper for the RAG pipeline.

Uses intfloat/multilingual-e5-large with the required passage/query prefixes.
Model is loaded once and cached for the process lifetime.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger(__name__)

_PASSAGE_PREFIX = "passage: "
_QUERY_PREFIX = "query: "


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    logger.info("Loading embedding model: %s", settings.embedding_model)
    try:
        return SentenceTransformer(settings.embedding_model)
    except Exception:
        logger.warning(
            "Failed to load %s, falling back to %s",
            settings.embedding_model,
            settings.embedding_fallback,
        )
        return SentenceTransformer(settings.embedding_fallback)


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed a batch of document passages (adds 'passage: ' prefix)."""
    prefixed = [_PASSAGE_PREFIX + t for t in texts]
    return _get_model().encode(prefixed, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single search query (adds 'query: ' prefix)."""
    return _get_model().encode(_QUERY_PREFIX + text, normalize_embeddings=True).tolist()
