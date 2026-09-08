"""
Post-launch canary for the pgvector retrieval cutover (pgvector migration
Phase 4 — see config.py's pgvector_retrieval_enabled).

Runs the same CI smoke-test sample as tests/test_retrieval_eval.py (3 cases
per collection, ~42 cases) directly against retrieve_pgvector — not the
dispatching retrieve() — so this checks pgvector's actual quality regardless
of which backend is currently live. No LLM calls: retrieval-only, so this is
cheap and fast enough to run frequently.

On failure (pass rate below CI_THRESHOLD, or the run itself raising — e.g.
DATABASE_URL unreachable, pgvector down), writes a kill-switch file at
data/pgvector_kill_switch.json and logs at ERROR (a distinct Sentry event
per observability.py's event_level=WARNING config). retrieve() in
agent/planning.py checks this file on every call and forces the known-good
ChromaDB fallback while it exists — an active kill-switch, not just the
existing manual pgvector_retrieval_enabled flag.

Does NOT auto-clear the kill-switch file on a later healthy run — an
intermittent problem could otherwise flap silently between backends with
no human ever seeing it happened. Clearing it (rm data/pgvector_kill_switch.json)
is a deliberate, reviewed action once the underlying issue is understood.

Usage:
    cd backend
    python scripts/canary_check.py

Registered as a scheduled Windows Task ("Complio pgvector Canary", daily
06:00 local time) via scripts/register_canary_task.ps1 — see that script's
docstring for the same "runs on this dev machine as a stand-in" caveat that
applies to the nightly backup task until a real production host exists.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("canary")

BACKEND_DIR = Path(__file__).parent.parent
KILL_SWITCH_FILE = BACKEND_DIR / "data" / "pgvector_kill_switch.json"

# Matches tests/test_retrieval_eval.py's CI smoke-test bar exactly — this
# canary is that same gate, just run continuously against live pgvector
# instead of once in CI.
CI_THRESHOLD_PERCENT = 70.0


def _ci_sample() -> list[dict]:
    from collections import defaultdict

    eval_file = BACKEND_DIR / "data" / "retrieval_eval.json"
    cases = json.loads(eval_file.read_text(encoding="utf-8"))
    by_collection: dict[str, list[dict]] = defaultdict(list)
    for c in cases:
        by_collection[c["collection"]].append(c)
    sample: list[dict] = []
    for col_cases in by_collection.values():
        sample.extend(col_cases[:3])
    return sample


def _article_match(retrieved: list[str], expected: list[str]) -> bool:
    # Same normalisation/matching logic as tests/test_retrieval_eval.py —
    # duplicated rather than imported since that module is pytest-collected
    # (importing it here would also collect/parametrize its tests).
    import re

    def norm(article: str) -> str:
        a = article.strip().lower()
        a = re.sub(r"\(\d+[a-z]?\)", "", a)
        a = re.sub(
            r"\b(?:eu_ai_act|nis2|gdpr|csrd|hinschg|arbschg|workplace_law|"
            r"lksg|enefg|bdsg|agg|milog|ttdsg|gwg|eu_data_act)\s+", "", a,
        )
        a = re.sub(r"\bart\.?\s+", "article ", a)
        return a.strip()

    exp_norm = {norm(e) for e in expected}
    ret_norm = {norm(r) for r in retrieved}
    if exp_norm & ret_norm:
        return True
    return any(r.startswith(e) or e.startswith(r) for e in exp_norm for r in ret_norm)


def run_canary() -> tuple[bool, str]:
    """Returns (healthy, summary). Never raises — a failure to even run the
    check is itself treated as unhealthy (fail-safe: if pgvector's health
    can't be verified, don't trust it)."""
    from config import settings

    if not settings.database_url:
        return False, "DATABASE_URL not configured — cannot check pgvector at all"

    try:
        from rag.retrieval import retrieve_pgvector

        cases = _ci_sample()
        hits = 0
        for case in cases:
            chunks = retrieve_pgvector(case["question"], [case["collection"]], top_k=5)
            retrieved = [c.get("article_number", "") for c in chunks]
            if _article_match(retrieved, case["expected_articles"]):
                hits += 1

        pct = hits / len(cases) * 100 if cases else 0.0
        summary = f"{hits}/{len(cases)} cases passed ({pct:.1f}%)"
        return pct >= CI_THRESHOLD_PERCENT, summary

    except Exception as exc:
        return False, f"canary run itself failed to execute: {exc!r}"


def _write_kill_switch(reason: str) -> None:
    KILL_SWITCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    KILL_SWITCH_FILE.write_text(
        json.dumps(
            {
                "tripped_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    from observability import init_sentry
    init_sentry()  # no-ops if SENTRY_DSN unset; needed so the ERROR log below actually reaches Sentry

    healthy, summary = run_canary()

    if healthy:
        print(f"OK: {summary}")
        if KILL_SWITCH_FILE.exists():
            existing = json.loads(KILL_SWITCH_FILE.read_text(encoding="utf-8"))
            logger.warning(
                "canary is healthy again (%s) but the kill switch tripped at %s "
                "(%s) is still active — not auto-clearing it. Remove %s "
                "manually once the underlying issue is understood.",
                summary, existing.get("tripped_at"), existing.get("reason"),
                KILL_SWITCH_FILE,
            )
        return 0

    logger.error("CANARY FAILED: %s — tripping pgvector kill switch", summary)
    _write_kill_switch(summary)
    print(f"FAILED: {summary} — kill switch written to {KILL_SWITCH_FILE}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
