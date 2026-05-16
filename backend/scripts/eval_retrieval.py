"""
Retrieval evaluation script.

For each test case in data/retrieval_eval.json:
  - Embeds the question and queries ChromaDB
  - Checks whether the expected article(s) appear in top-1 and top-5 results
  - Reports per-regulation and overall accuracy

Metrics:
  top-1 accuracy   correct section is the first result
  top-5 accuracy   correct section appears in first 5 results
  miss rate        correct section not found in top 5

Run from backend/:  python scripts/eval_retrieval.py
                    python scripts/eval_retrieval.py --regulation hinschg
                    python scripts/eval_retrieval.py --verbose
"""
from __future__ import annotations

import argparse
import json
import re as _re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.retrieval import retrieve

EVAL_FILE = Path(__file__).parent.parent / "data" / "retrieval_eval.json"

def _normalise(article: str) -> str:
    """
    Normalise article numbers for fuzzy matching.

    Handles:
      § 12(1)           → § 12
      eu_ai_act Art. 11(1) → article 11
      Article 11        → article 11
      Art. 11           → article 11
      nis2 Art. 34(1)   → article 34
    """
    a = article.strip().lower()
    # Remove subsection: (1), (2a), etc.
    a = _re.sub(r'\(\d+[a-z]?\)', '', a)
    # Remove subsection suffix on § numbers: § 12a → § 12a (keep letter), but § 12(1) already stripped
    # Normalise various "Article N" formats
    a = _re.sub(r'\b(?:eu_ai_act|nis2|gdpr|csrd|hinschg|arbschg|workplace_law|lksg|enefg|bdsg|agg|milog)\s+', '', a)
    a = _re.sub(r'\bart\.?\s+', 'article ', a)
    a = a.strip()
    return a


def _article_match(retrieved_articles: list[str], expected: list[str]) -> bool:
    """True if any expected article matches any retrieved article after normalisation."""
    expected_norm  = {_normalise(e) for e in expected}
    retrieved_norm = {_normalise(r) for r in retrieved_articles}
    # Exact match after normalisation
    if expected_norm & retrieved_norm:
        return True
    # Prefix match: expected "§ 12" matches retrieved "§ 12a" or vice versa
    for exp in expected_norm:
        for ret in retrieved_norm:
            if ret.startswith(exp) or exp.startswith(ret):
                return True
    return False


def run_eval(filter_regulation: str | None = None, verbose: bool = False) -> None:
    cases = json.loads(EVAL_FILE.read_text(encoding="utf-8"))

    if filter_regulation:
        cases = [c for c in cases if c["regulation"] == filter_regulation]
        if not cases:
            print(f"No test cases found for regulation: {filter_regulation}")
            return

    print(f"\nRunning retrieval eval — {len(cases)} test cases\n")
    print(f"{'ID':<18} {'Top-1':>6} {'Top-5':>6}  Question")
    print("-" * 80)

    reg_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "top1": 0, "top5": 0})
    total = top1_total = top5_total = 0

    for case in cases:
        case_id    = case["id"]
        regulation = case["regulation"]
        collection = case["collection"]
        question   = case["question"]
        expected   = case["expected_articles"]

        chunks = retrieve(question, [collection], top_k=5)
        retrieved_articles = [c.get("article_number", "") for c in chunks]

        hit_top1 = _article_match(retrieved_articles[:1], expected)
        hit_top5 = _article_match(retrieved_articles[:5], expected)

        top1_mark = "HIT" if hit_top1 else "---"
        top5_mark = "HIT" if hit_top5 else "---"

        print(f"{case_id:<18} {top1_mark:>6} {top5_mark:>6}  {question[:55]}")

        if verbose and not hit_top5:
            print(f"  Expected : {expected}")
            print(f"  Retrieved: {retrieved_articles}")
            print()

        reg_stats[regulation]["total"]  += 1
        reg_stats[regulation]["top1"]   += int(hit_top1)
        reg_stats[regulation]["top5"]   += int(hit_top5)

        total      += 1
        top1_total += int(hit_top1)
        top5_total += int(hit_top5)

    # Per-regulation summary
    print(f"\n{'Regulation':<16} {'Cases':>6} {'Top-1 %':>9} {'Top-5 %':>9} {'Miss %':>8}")
    print("-" * 52)

    for reg in sorted(reg_stats):
        s = reg_stats[reg]
        t = s["total"]
        p1 = s["top1"] / t * 100
        p5 = s["top5"] / t * 100
        miss = (1 - s["top5"] / t) * 100
        print(f"{reg:<16} {t:>6} {p1:>8.0f}% {p5:>8.0f}% {miss:>7.0f}%")

    # Overall
    p1_all   = top1_total / total * 100 if total else 0
    p5_all   = top5_total / total * 100 if total else 0
    miss_all = (1 - top5_total / total) * 100 if total else 0

    print("-" * 52)
    print(f"{'OVERALL':<16} {total:>6} {p1_all:>8.0f}% {p5_all:>8.0f}% {miss_all:>7.0f}%")
    print()

    # Verdict
    if p5_all >= 80:
        verdict = "GOOD — retrieval quality is solid"
    elif p5_all >= 60:
        verdict = "ACCEPTABLE — some regulations need attention"
    else:
        verdict = "POOR — retrieval quality needs significant improvement"

    print(f"Verdict: {verdict}")
    print(f"Top-1: {p1_all:.0f}%  Top-5: {p5_all:.0f}%  Miss: {miss_all:.0f}%\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality")
    parser.add_argument("--regulation", "-r", help="Filter to one regulation (e.g. hinschg)")
    parser.add_argument("--verbose",    "-v", action="store_true", help="Show missed cases in detail")
    args = parser.parse_args()

    run_eval(filter_regulation=args.regulation, verbose=args.verbose)
