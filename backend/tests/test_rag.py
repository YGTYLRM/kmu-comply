"""
RAG pipeline tests.

Run from backend/: python -m pytest tests/test_rag.py -v

These tests require all ChromaDB collections to be populated.
Run scripts/ingest_regulations.py --regulation all first.
"""
from __future__ import annotations

import chromadb

from backend.rag.retrieval import deduplicate, retrieve
from backend.rag.ingest import CHROMA_DIR, REGULATION_COLLECTIONS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collection_count(name: str) -> int:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        return client.get_collection(name).count()
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Collection population
# ---------------------------------------------------------------------------

class TestCollections:
    def test_bdsg_is_indexed(self):
        assert _collection_count("bdsg") > 0, "bdsg collection is empty — run ingest first"

    def test_gdpr_is_indexed(self):
        assert _collection_count("gdpr_dsgvo") > 0, "gdpr_dsgvo collection is empty"

    def test_lksg_is_indexed(self):
        assert _collection_count("lksg") > 0, "lksg collection is empty"

    def test_enefg_is_indexed(self):
        assert _collection_count("enefg") > 0, "enefg collection is empty"

    def test_csrd_is_indexed(self):
        assert _collection_count("csrd") > 0, "csrd collection is empty"

    def test_compliance_guides_is_indexed(self):
        assert _collection_count("compliance_guides") > 0, "compliance_guides collection is empty"

    def test_all_collection_names_match_mapping(self):
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        existing = {c.name for c in client.list_collections()}
        for reg, col in REGULATION_COLLECTIONS.items():
            assert col in existing, f"Collection '{col}' (regulation '{reg}') not found"


# ---------------------------------------------------------------------------
# retrieve() — metadata shape
# ---------------------------------------------------------------------------

class TestRetrieve:
    def test_returns_list(self):
        results = retrieve("Datenschutzbeauftragter", ["bdsg"])
        assert isinstance(results, list)

    def test_results_have_required_fields(self):
        results = retrieve("Datenschutzbeauftragter", ["bdsg"], top_k=5)
        assert results, "No results returned"
        required = {"text", "score", "collection", "regulation", "article_number", "title"}
        for r in results:
            missing = required - r.keys()
            assert not missing, f"Chunk missing fields: {missing}"

    def test_scores_are_descending(self):
        results = retrieve("Videoüberwachung", ["bdsg"], top_k=10)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_scores_in_valid_range(self):
        results = retrieve("Energieaudit", ["enefg"], top_k=5)
        for r in results:
            assert 0.0 <= r["score"] <= 1.0, f"Score out of range: {r['score']}"

    def test_collection_field_matches_regulation(self):
        results = retrieve("Risikoanalyse", ["lksg"], top_k=5)
        for r in results:
            assert r["collection"] == "lksg"

    def test_multi_regulation_query(self):
        results = retrieve("Datenschutz", ["bdsg", "gdpr"], top_k=5)
        collections = {r["collection"] for r in results}
        assert len(collections) >= 1

    def test_unknown_regulation_returns_empty(self):
        results = retrieve("query", ["nonexistent_regulation"])
        assert results == []

    def test_empty_regulations_returns_empty(self):
        results = retrieve("query", [])
        assert results == []


# ---------------------------------------------------------------------------
# retrieve() — semantic correctness
# ---------------------------------------------------------------------------

class TestSemanticSearch:
    def test_datenschutzbeauftragter_finds_bdsg_38(self):
        results = retrieve("Datenschutzbeauftragter Bestellung", ["bdsg"], top_k=5)
        assert results, "No results"
        top = results[0]
        assert top["score"] >= 0.75, f"Low score for DPO query: {top['score']}"
        article_nums = [r["article_number"] for r in results[:3]]
        assert any("38" in a for a in article_nums), (
            f"Expected § 38 in top 3, got: {article_nums}"
        )

    def test_energieaudit_finds_enefg(self):
        results = retrieve("Energieaudit Pflicht Unternehmen", ["enefg"], top_k=5)
        assert results, "No results"
        assert results[0]["score"] >= 0.70

    def test_lieferkette_finds_lksg(self):
        results = retrieve("Sorgfaltspflichten Lieferkette", ["lksg"], top_k=5)
        assert results, "No results"
        assert results[0]["score"] >= 0.70

    def test_cross_regulation_dpo_query(self):
        results = retrieve("Datenschutzbeauftragter Pflicht", ["bdsg", "gdpr"], top_k=10)
        regulations_found = {r["regulation"] for r in results}
        assert len(regulations_found) >= 1


# ---------------------------------------------------------------------------
# deduplicate()
# ---------------------------------------------------------------------------

class TestDeduplicate:
    def test_removes_duplicate_articles(self):
        chunks = [
            {"regulation": "bdsg", "article_number": "§ 38", "score": 0.9, "text": "a", "title": "t"},
            {"regulation": "bdsg", "article_number": "§ 38", "score": 0.8, "text": "b", "title": "t"},
            {"regulation": "bdsg", "article_number": "§ 26", "score": 0.7, "text": "c", "title": "t"},
        ]
        result = deduplicate(chunks)
        keys = [(r["regulation"], r["article_number"]) for r in result]
        assert len(keys) == len(set(keys)), "Duplicates remain after deduplication"

    def test_keeps_highest_score(self):
        chunks = [
            {"regulation": "bdsg", "article_number": "§ 38", "score": 0.9, "text": "high"},
            {"regulation": "bdsg", "article_number": "§ 38", "score": 0.5, "text": "low"},
        ]
        result = deduplicate(chunks)
        assert len(result) == 1
        assert result[0]["text"] == "high"

    def test_different_regulations_not_merged(self):
        chunks = [
            {"regulation": "bdsg", "article_number": "Art. 5", "score": 0.9, "text": "a"},
            {"regulation": "gdpr", "article_number": "Art. 5", "score": 0.8, "text": "b"},
        ]
        result = deduplicate(chunks)
        assert len(result) == 2

    def test_output_sorted_by_score(self):
        chunks = [
            {"regulation": "bdsg", "article_number": "§ 1", "score": 0.5, "text": "a"},
            {"regulation": "bdsg", "article_number": "§ 2", "score": 0.9, "text": "b"},
            {"regulation": "bdsg", "article_number": "§ 3", "score": 0.7, "text": "c"},
        ]
        result = deduplicate(chunks)
        scores = [r["score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_empty_input(self):
        assert deduplicate([]) == []

    def test_live_retrieve_deduplicates(self):
        raw = retrieve("Datenschutzbeauftragter", ["bdsg"], top_k=15)
        deduped = deduplicate(raw)
        keys = [(r["regulation"], r["article_number"]) for r in deduped]
        assert len(keys) == len(set(keys))
        assert len(deduped) <= len(raw)
