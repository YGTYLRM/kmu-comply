"""
KB health check — run from backend/ to verify knowledge base completeness.

Usage:
    cd backend
    python scripts/kb_health.py              # all collections
    python scripts/kb_health.py gdpr_dsgvo   # specific collection
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings

REQUIRED_COLLECTIONS = [
    "gdpr_dsgvo",
    "bdsg",
    "nis2",
    "eu_ai_act",
    "hinschg",
    "lksg",
    "enefg",
    "csrd",
    "workplace_law",
    "agg",
    "milog",
    "ttdsg",
    "gwg",
    "eu_data_act",
    "compliance_guides",
]

# Minimum chunk counts for a meaningful analysis (can be lower for small laws)
MIN_CHUNKS = {
    "gdpr_dsgvo": 30,
    "bdsg": 10,
    "nis2": 20,
    "eu_ai_act": 40,
    "hinschg": 20,
    "lksg": 15,
    "enefg": 10,
    "csrd": 30,
    "workplace_law": 50,
    "agg": 20,
    "milog": 10,
    "ttdsg": 10,
    "gwg": 15,
    "eu_data_act": 15,
    "compliance_guides": 100,
}

CI_PASS_THRESHOLD = 0.80  # 80% of regulations must meet minimum chunks


def get_chroma_client():
    if settings.chroma_server_url:
        import chromadb
        return chromadb.HttpClient(host=settings.chroma_server_url.replace("http://", "").split(":")[0],
                                   port=int(settings.chroma_server_url.split(":")[-1]))
    else:
        import chromadb
        # Resolve relative to the backend/ directory regardless of cwd
        backend_dir = Path(__file__).parent.parent
        chroma_path = (backend_dir / "data" / "chroma_db").resolve()
        return chromadb.PersistentClient(path=str(chroma_path))


def check_kb(target_collections=None):
    client = get_chroma_client()
    existing = {c.name: c for c in client.list_collections()}

    collections = target_collections or REQUIRED_COLLECTIONS
    results = []
    total_chunks = 0
    passing = 0

    print(f"\n{'Regulation':<25} {'Chunks':>8} {'Min':>6} {'Status':<12} {'Unique Articles':>16}")
    print("-" * 75)

    for reg in collections:
        if reg not in existing:
            status = "MISSING"
            chunks = 0
            articles = 0
        else:
            col = existing[reg]
            chunks = col.count()
            total_chunks += chunks
            min_required = MIN_CHUNKS.get(reg, 10)

            # Count unique article numbers from metadata
            try:
                results_sample = col.get(include=["metadatas"], limit=min(chunks, 500))
                articles = len({
                    m.get("article_number", "")
                    for m in results_sample["metadatas"]
                    if m.get("article_number")
                })
            except Exception:
                articles = 0

            if chunks >= min_required:
                status = "OK"
                passing += 1
            elif chunks > 0:
                status = "LOW"
            else:
                status = "EMPTY"

        icon = "OK" if status == "OK" else ("!!" if status == "LOW" else "XX")
        min_req = MIN_CHUNKS.get(reg, 10)
        print(f"{icon} {reg:<23} {chunks:>8} {min_req:>6} {status:<12} {articles:>16}")
        results.append({
            "regulation": reg,
            "chunks": chunks,
            "unique_articles": articles,
            "status": status,
            "min_required": min_req,
        })

    print("-" * 75)
    print(f"  {'TOTAL':<23} {total_chunks:>8}")
    print(f"\n  {passing}/{len(collections)} collections meet minimum chunk threshold")

    pass_rate = passing / len(collections) if collections else 0
    overall = "PASS" if pass_rate >= CI_PASS_THRESHOLD else "FAIL"
    print(f"  Overall KB health: {overall} ({pass_rate:.0%} passing >= {CI_PASS_THRESHOLD:.0%} threshold)\n")

    return results, overall == "PASS"


def smoke_test(reg: str):
    """Quick retrieval smoke test for a single regulation."""
    from rag.retrieval import retrieve

    test_queries = {
        "gdpr_dsgvo": ("records of processing activities Art. 30", "30"),
        "bdsg": ("data protection officer BDSG §38", "38"),
        "nis2": ("incident reporting 72 hours Art. 23", "23"),
        "eu_ai_act": ("high-risk AI system transparency", "13"),
        "hinschg": ("internal reporting channel 50 employees §12", "12"),
        "lksg": ("risk analysis supply chain §5", "5"),
        "enefg": ("energy audit EDL-G §8", "8"),
        "csrd": ("sustainability reporting ESRS", ""),
        "workplace_law": ("Gefährdungsbeurteilung risk assessment §5", "5"),
        "agg": ("AGG discrimination employer §12", "12"),
        "milog": ("minimum wage documentation §17", "17"),
        "ttdsg": ("cookie consent §25 opt-in", "25"),
        "gwg": ("risk analysis money laundering §5", "5"),
        "eu_data_act": ("data sharing obligations", ""),
        "compliance_guides": ("GDPR lawful basis Art. 6", "6"),
    }

    if reg not in test_queries:
        print(f"No smoke test defined for {reg}")
        return

    query, expected_article = test_queries[reg]
    chunks = retrieve(query, [reg], top_k=5)

    if not chunks:
        print(f"✗ {reg}: No chunks retrieved for smoke test query")
        return

    articles = [c.get("article_number", "") for c in chunks]
    hit = expected_article and any(expected_article in a for a in articles)
    status = "PASS" if (hit or not expected_article) else f"PARTIAL (expected §{expected_article} in {articles[:3]})"
    print(f"  Smoke test {reg}: {status} -- retrieved {len(chunks)} chunks, top articles: {articles[:3]}")


if __name__ == "__main__":
    target = sys.argv[1:] if len(sys.argv) > 1 else None
    results, passed = check_kb(target)

    if target and len(target) == 1:
        print("Running smoke test...")
        smoke_test(target[0])

    sys.exit(0 if passed else 1)
