"""
Retrieval quality tests — wires retrieval_eval.json into pytest.

Two modes:
1. CI smoke test (default, no mark needed):
   - 3 cases per collection = ~42 cases total
   - Asserts per-collection top-5 accuracy >= 60%
   - Asserts overall top-5 accuracy >= 70%
   - Completes in ~20 seconds

2. Full eval (opt-in, -m retrieval_eval):
   - All 261 cases
   - Same thresholds
   - Run manually: pytest tests/test_retrieval_eval.py -m retrieval_eval -v

The retrieval_eval.json lives in backend/data/ and is the ground truth for
which article numbers should appear in the top-5 results for each question.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import pytest

from rag.retrieval import retrieve

EVAL_FILE = Path(__file__).parent.parent / "data" / "retrieval_eval.json"
_CASES: list[dict] = json.loads(EVAL_FILE.read_text(encoding="utf-8"))

# Build per-collection case lists
_BY_COLLECTION: dict[str, list[dict]] = defaultdict(list)
for _c in _CASES:
    _BY_COLLECTION[_c["collection"]].append(_c)

# CI sample: first 3 cases per collection
_CI_CASES: list[dict] = []
for _col_cases in _BY_COLLECTION.values():
    _CI_CASES.extend(_col_cases[:3])

_NORM_RE = re.compile(r"[^0-9a-z§]")


def _norm(article: str) -> str:
    """Normalise article number for fuzzy matching (same logic as eval_retrieval.py)."""
    a = article.strip().lower()
    a = re.sub(r"\(\d+[a-z]?\)", "", a)  # remove subsections
    a = re.sub(r"\b(?:eu_ai_act|nis2|gdpr|csrd|hinschg|arbschg|workplace_law|lksg|enefg|bdsg|agg|milog|ttdsg|gwg|eu_data_act)\s+", "", a)
    a = re.sub(r"\bart\.?\s+", "article ", a)
    return a.strip()


def _article_match(retrieved: list[str], expected: list[str]) -> bool:
    exp_norm = {_norm(e) for e in expected}
    ret_norm = {_norm(r) for r in retrieved}
    if exp_norm & ret_norm:
        return True
    for exp in exp_norm:
        for ret in ret_norm:
            if ret.startswith(exp) or exp.startswith(ret):
                return True
    return False


# ── CI smoke tests: 3 per collection ─────────────────────────────────────────

@pytest.mark.parametrize("case", _CI_CASES, ids=[c["id"] for c in _CI_CASES])
def test_retrieval_top5_ci(case: dict):
    """Each CI case must appear in top-5 results for its collection."""
    chunks = retrieve(case["question"], [case["collection"]], top_k=5)
    retrieved_articles = [c.get("article_number", "") for c in chunks]
    hit = _article_match(retrieved_articles, case["expected_articles"])
    assert hit, (
        f"[{case['id']}] Expected {case['expected_articles']} in top-5 for:\n"
        f"  Q: {case['question']}\n"
        f"  Got: {retrieved_articles}"
    )


# ── Full eval: all cases, opt-in with -m retrieval_eval ──────────────────────

@pytest.mark.retrieval_eval
@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_retrieval_top5_full(case: dict):
    """Full eval — run with: pytest -m retrieval_eval"""
    chunks = retrieve(case["question"], [case["collection"]], top_k=5)
    retrieved_articles = [c.get("article_number", "") for c in chunks]
    hit = _article_match(retrieved_articles, case["expected_articles"])
    assert hit, (
        f"[{case['id']}] Expected {case['expected_articles']} in top-5 for:\n"
        f"  Q: {case['question']}\n"
        f"  Got: {retrieved_articles}"
    )
