"""
Integration tests for the full analysis pipeline.

These tests run against real ChromaDB + LLM — mark with -m integration to run.
Skipped by default in CI to avoid LLM API costs.

Run manually:
    cd backend
    python -m pytest tests/test_pipeline.py -m integration -v
"""
import pytest

from agent.planning import determine_applicability, retrieve_regulatory_context
from agent.profiling import enrich_profile
from models.enums import Regulation


pytestmark = pytest.mark.integration


# ── Step 1: profiling ─────────────────────────────────────────────────────────

class TestProfiling:
    def test_it_agency_enriched(self, profile_it_agency):
        result = enrich_profile(profile_it_agency)
        assert result.company_name == profile_it_agency.company_name
        assert result.employee_count == profile_it_agency.employee_count
        assert isinstance(result.inferred_characteristics, list)
        assert isinstance(result.validation_warnings, list)

    def test_healthcare_flags_special_data(self, profile_healthcare):
        result = enrich_profile(profile_healthcare)
        assert result.processes_special_category_data is True
        assert any("Art. 9" in c or "special" in c.lower() for c in result.inferred_characteristics)

    def test_manufacturer_flags_supply_chain(self, profile_manufacturer):
        result = enrich_profile(profile_manufacturer)
        assert result.has_supply_chain_abroad is True

    def test_missing_revenue_flagged(self, profile_it_agency):
        profile_it_agency.annual_revenue_eur = None
        result = enrich_profile(profile_it_agency)
        assert "annual_revenue_eur" in result.missing_optional_fields

    def test_fallback_on_no_api_key(self, profile_it_agency, monkeypatch):
        from config import settings
        monkeypatch.setattr(settings, "llm_api_key", "")
        result = enrich_profile(profile_it_agency)
        assert result.inferred_characteristics == []
        assert isinstance(result.missing_optional_fields, list)


# ── Step 2: applicability ─────────────────────────────────────────────────────

class TestApplicability:
    def test_freelancer_minimal(self, profile_freelancer):
        enriched = enrich_profile(profile_freelancer)
        result = determine_applicability(enriched)
        applicable = [r for r in result if r.applies]
        regs = {r.regulation for r in applicable}
        assert Regulation.LKSG not in regs
        assert Regulation.CSRD not in regs
        assert Regulation.ENEFG not in regs

    def test_large_company_all_apply(self, profile_large_listed):
        enriched = enrich_profile(profile_large_listed)
        result = determine_applicability(enriched)
        regs = {r.regulation for r in result if r.applies}
        assert regs == {Regulation.GDPR, Regulation.LKSG, Regulation.ENEFG, Regulation.CSRD, Regulation.BDSG}

    def test_it_agency_gdpr_bdsg_only(self, profile_it_agency):
        enriched = enrich_profile(profile_it_agency)
        result = determine_applicability(enriched)
        regs = {r.regulation for r in result if r.applies}
        assert Regulation.GDPR in regs
        assert Regulation.BDSG in regs
        assert Regulation.LKSG not in regs

    def test_applicability_has_reasons(self, profile_manufacturer):
        enriched = enrich_profile(profile_manufacturer)
        result = determine_applicability(enriched)
        for reg_app in result:
            assert reg_app.reason, f"{reg_app.regulation} has no reason"


# ── Step 3: retrieval ─────────────────────────────────────────────────────────

class TestRetrieval:
    def test_retrieves_gdpr_chunks(self, profile_it_agency):
        enriched = enrich_profile(profile_it_agency)
        applicability = determine_applicability(enriched)
        chunks = retrieve_regulatory_context(enriched, applicability)
        assert len(chunks) >= 5
        regs = {c.regulation for c in chunks}
        assert Regulation.GDPR in regs

    def test_no_chunks_for_non_applicable(self, profile_freelancer):
        enriched = enrich_profile(profile_freelancer)
        applicability = determine_applicability(enriched)
        applicable_regs = {a.regulation for a in applicability if a.applies}
        chunks = retrieve_regulatory_context(enriched, applicability)
        chunk_regs = {c.regulation for c in chunks}
        for reg in chunk_regs:
            assert reg in applicable_regs

    def test_manufacturer_retrieves_lksg(self, profile_manufacturer):
        enriched = enrich_profile(profile_manufacturer)
        applicability = determine_applicability(enriched)
        chunks = retrieve_regulatory_context(enriched, applicability)
        regs = {c.regulation for c in chunks}
        assert Regulation.LKSG in regs

    def test_chunks_have_required_fields(self, profile_healthcare):
        enriched = enrich_profile(profile_healthcare)
        applicability = determine_applicability(enriched)
        chunks = retrieve_regulatory_context(enriched, applicability)
        for c in chunks:
            assert c.article_number
            assert c.text
            assert c.regulation


# ── Step 4 + 5: gap analysis and action plan (smoke tests) ────────────────────

class TestGapAndActions:
    def test_gap_analysis_returns_results(self, profile_it_agency):
        from agent.planning import run_gap_analysis
        enriched = enrich_profile(profile_it_agency)
        applicability = determine_applicability(enriched)
        chunks = retrieve_regulatory_context(enriched, applicability)
        failures: list[str] = []
        gaps = run_gap_analysis(enriched, chunks, failures)
        assert isinstance(gaps, list)
        for gap in gaps:
            assert gap.evidence

    def test_action_plan_covers_non_compliant(self, profile_it_agency):
        from agent.planning import generate_action_plan, run_gap_analysis
        from models.enums import ComplianceStatus
        enriched = enrich_profile(profile_it_agency)
        applicability = determine_applicability(enriched)
        chunks = retrieve_regulatory_context(enriched, applicability)
        failures: list[str] = []
        gaps = run_gap_analysis(enriched, chunks, failures)
        actions = generate_action_plan(enriched, gaps, failures)
        non_compliant_refs = {
            f"{g.regulation.value}:{g.article_number}"
            for g in gaps
            if g.status in (ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT)
        }
        action_refs = {a.gap_reference for a in actions}
        uncovered = non_compliant_refs - action_refs
        assert not uncovered, f"Gaps without actions: {uncovered}"
