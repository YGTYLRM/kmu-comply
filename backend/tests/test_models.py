"""
Unit tests for Pydantic model validation — company profile and report models.
"""

import pytest
from pydantic import ValidationError

from models.company_profile import CompanyProfile, EnrichedCompanyProfile
from models.compliance_report import (
    RegulationApplicability,
    ComplianceGap,
    ActionItem,
    RegulationScore,
    ComplianceReport,
)
from models.enums import (
    Regulation,
    ComplianceStatus,
    Priority,
)


class TestCompanyProfile:
    def test_valid_minimal_profile(self):
        profile = CompanyProfile(
            company_name="Test GmbH",
            industry="it_software",
            employee_count=10,
            processes_personal_data=True,
        )
        assert profile.country == "DE"
        assert profile.processing_is_occasional is False

    def test_employee_count_must_be_positive(self):
        with pytest.raises(ValidationError):
            CompanyProfile(
                company_name="Test",
                industry="it_software",
                employee_count=0,
                processes_personal_data=False,
            )

    def test_company_name_stripped(self):
        profile = CompanyProfile(
            company_name="  TechCo  ",
            industry="it_software",
            employee_count=5,
            processes_personal_data=False,
        )
        assert profile.company_name == "TechCo"

    def test_supply_chain_countries_implies_abroad_flag(self):
        profile = CompanyProfile(
            company_name="ManuCo",
            industry="manufacturing",
            employee_count=100,
            processes_personal_data=False,
            has_supply_chain_abroad=False,
            supply_chain_countries=["CN"],
        )
        assert profile.has_supply_chain_abroad is True

    def test_annual_revenue_must_be_non_negative(self):
        with pytest.raises(ValidationError):
            CompanyProfile(
                company_name="Test",
                industry="it_software",
                employee_count=5,
                processes_personal_data=False,
                annual_revenue_eur=-1.0,
            )

    def test_empty_compliance_notes_becomes_none(self):
        profile = CompanyProfile(
            company_name="Test",
            industry="it_software",
            employee_count=5,
            processes_personal_data=False,
            existing_compliance_notes="   ",
        )
        assert profile.existing_compliance_notes is None

    def test_enriched_profile_extends_base(self):
        profile = CompanyProfile(
            company_name="Test",
            industry="it_software",
            employee_count=5,
            processes_personal_data=True,
        )
        enriched = EnrichedCompanyProfile(
            **profile.model_dump(),
            inferred_characteristics=["processes_employee_data"],
            validation_warnings=["Missing revenue data"],
        )
        assert enriched.company_name == "Test"
        assert len(enriched.validation_warnings) == 1


class TestComplianceReportModels:
    def test_regulation_applicability_valid(self):
        ra = RegulationApplicability(
            regulation=Regulation.GDPR,
            applies=True,
            reason="Processes personal data.",
            key_threshold="Personal data processing",
        )
        assert ra.applies is True

    def test_compliance_gap_requires_evidence(self):
        with pytest.raises(ValidationError):
            ComplianceGap(
                regulation=Regulation.GDPR,
                article_number="Art. 30",
                article_title="Records of Processing Activities",
                status=ComplianceStatus.NON_COMPLIANT,
                # evidence is required
            )

    def test_action_item_valid(self):
        item = ActionItem(
            regulation=Regulation.GDPR,
            article_number="Art. 30",
            action="Create a Record of Processing Activities.",
            priority=Priority.HIGH,
            estimated_effort="4-8 hours",
            gap_reference="GDPR-Art.30-NON_COMPLIANT",
        )
        assert item.priority == Priority.HIGH

    def test_regulation_score_bounds(self):
        with pytest.raises(ValidationError):
            RegulationScore(
                regulation=Regulation.GDPR,
                total_requirements=10,
                compliant=5,
                partially_compliant=2,
                non_compliant=3,
                cannot_assess=0,
                score_percent=101.0,  # out of bounds
            )

    def test_compliance_report_has_disclaimer(self):
        report = ComplianceReport(
            job_id="test-123",
            company_name="Test GmbH",
            generated_at="2026-04-30T12:00:00Z",
            applicable_regulations=[],
            inferred_characteristics=[],
            missing_optional_fields=[],
            validation_warnings=[],
            retrieved_chunks=[],
            gap_analysis=[],
            action_plan=[],
            regulation_scores=[],
            overall_score_percent=0.0,
        )
        assert "not constitute legal advice" in report.disclaimer


class TestCitationVerification:
    """Tests for agent.validation.verify_gap_citations."""

    def _make_gap(self, reg: Regulation, article: str, status=ComplianceStatus.NON_COMPLIANT):
        return ComplianceGap(
            regulation=reg,
            article_number=article,
            article_title="Test",
            status=status,
            evidence="Test evidence",
            confidence="HIGH",
        )

    def _make_chunk(self, reg: Regulation, article: str):
        from models.compliance_report import RegulatoryChunk
        from models.enums import ObligationType
        return RegulatoryChunk(
            regulation=reg,
            article_number=article,
            title="Test",
            text="Test text",
            obligation_type=ObligationType.MUST,
        )

    def test_verified_citation_no_warning(self):
        from agent.validation import verify_gap_citations
        gap = self._make_gap(Regulation.GDPR, "Art. 32")
        chunk = self._make_chunk(Regulation.GDPR, "Art. 32")
        warnings = verify_gap_citations([gap], [chunk])
        assert warnings == []
        assert gap.confidence == "HIGH"

    def test_hallucinated_citation_flagged(self):
        from agent.validation import verify_gap_citations
        gap = self._make_gap(Regulation.GDPR, "Art. 99")
        chunk = self._make_chunk(Regulation.GDPR, "Art. 32")
        warnings = verify_gap_citations([gap], [chunk])
        assert len(warnings) == 1
        assert "Art. 99" in warnings[0]
        assert gap.confidence == "LOW"

    def test_cannot_assess_skipped(self):
        from agent.validation import verify_gap_citations
        gap = self._make_gap(Regulation.GDPR, "KB-EMPTY", ComplianceStatus.CANNOT_ASSESS)
        warnings = verify_gap_citations([gap], [])
        assert warnings == []

    def test_normalisation_ignores_whitespace_and_dots(self):
        from agent.validation import verify_gap_citations
        gap = self._make_gap(Regulation.GDPR, "Art.32(1)(a)")
        chunk = self._make_chunk(Regulation.GDPR, "Art. 32")
        warnings = verify_gap_citations([gap], [chunk])
        assert warnings == []  # "3210a" contains "32" — matches

    def test_no_chunks_for_regulation_skipped(self):
        from agent.validation import verify_gap_citations
        gap = self._make_gap(Regulation.LKSG, "§ 5")
        chunk = self._make_chunk(Regulation.GDPR, "Art. 32")  # different regulation
        warnings = verify_gap_citations([gap], [chunk])
        assert warnings == []  # no chunks for LkSG → skip (zero-chunks guard handles it)

    def test_multiple_gaps_one_hallucinated(self):
        from agent.validation import verify_gap_citations
        gap_good = self._make_gap(Regulation.GDPR, "Art. 32")
        gap_bad = self._make_gap(Regulation.GDPR, "Art. 99")
        chunk = self._make_chunk(Regulation.GDPR, "Art. 32")
        warnings = verify_gap_citations([gap_good, gap_bad], [chunk])
        assert len(warnings) == 1
        assert gap_good.confidence == "HIGH"
        assert gap_bad.confidence == "LOW"


class TestAPIModels:
    def test_health_response_defaults(self):
        from models.api_responses import HealthResponse
        h = HealthResponse(
            status="ok",
            chromadb="connected",
            embedding_model="intfloat/multilingual-e5-large",
        )
        assert h.version == "0.1.0"

    def test_error_response(self):
        from models.api_responses import ErrorResponse
        e = ErrorResponse(error="Something went wrong", code="VALIDATION_FAILED")
        assert e.detail is None
