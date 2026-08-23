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
        assert report.disclaimer  # non-empty disclaimer is required
        assert any(phrase in report.disclaimer for phrase in [
            "not constitute legal advice",       # English disclaimer
            "keine Rechtsberatung",              # German disclaimer
            "stellt keine Rechtsberatung dar",   # German disclaimer variant
        ]), f"Disclaimer does not contain a legal advice caveat: {report.disclaimer[:200]}"


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


class TestEvidenceQuoteVerification:
    """Tests for agent.validation.check_evidence_quotes."""

    _CHUNK_TEXT = (
        "Art. 30 Verzeichnis von Verarbeitungstätigkeiten\n\n"
        "(1) Jeder Verantwortliche und gegebenenfalls sein Vertreter führen ein "
        "Verzeichnis aller Verarbeitungstätigkeiten, die ihrer Zuständigkeit unterliegen."
    )

    def _make_gap(self, quote=None, confidence="HIGH", status=ComplianceStatus.NON_COMPLIANT):
        return ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="Art. 30",
            article_title="Verzeichnis von Verarbeitungstätigkeiten",
            status=status,
            evidence="Test evidence",
            evidence_quote=quote,
            confidence=confidence,
        )

    def _make_chunk(self, text=None):
        from models.compliance_report import RegulatoryChunk
        from models.enums import ObligationType
        return RegulatoryChunk(
            regulation=Regulation.GDPR,
            article_number="Art. 30",
            title="Verzeichnis von Verarbeitungstätigkeiten",
            text=text or self._CHUNK_TEXT,
            obligation_type=ObligationType.MUST,
        )

    def test_genuine_quote_passes(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(quote="führen ein Verzeichnis aller Verarbeitungstätigkeiten")
        warnings = check_evidence_quotes([gap], [self._make_chunk()])
        assert warnings == []
        assert gap.confidence == "HIGH"

    def test_quote_with_different_whitespace_and_case_passes(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(quote="Führen ein  Verzeichnis\naller   verarbeitungstätigkeiten")
        warnings = check_evidence_quotes([gap], [self._make_chunk()])
        assert warnings == []
        assert gap.confidence == "HIGH"

    def test_fabricated_quote_downgraded_to_low(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(quote="Unternehmen müssen jährlich einen Bericht an die Behörde senden")
        warnings = check_evidence_quotes([gap], [self._make_chunk()])
        assert len(warnings) == 1
        assert "fabricated" in warnings[0]
        assert gap.confidence == "LOW"

    def test_ellipsis_quote_checks_each_fragment(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(
            quote="Jeder Verantwortliche und gegebenenfalls sein Vertreter ... die ihrer Zuständigkeit unterliegen"
        )
        warnings = check_evidence_quotes([gap], [self._make_chunk()])
        assert warnings == []
        assert gap.confidence == "HIGH"

    def test_ellipsis_quote_with_one_fabricated_fragment_fails(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(
            quote="Jeder Verantwortliche und gegebenenfalls sein Vertreter ... muss der Aufsichtsbehörde monatlich berichten"
        )
        warnings = check_evidence_quotes([gap], [self._make_chunk()])
        assert len(warnings) == 1
        assert gap.confidence == "LOW"

    def test_missing_quote_on_high_confidence_downgraded_to_medium(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(quote=None, confidence="HIGH")
        warnings = check_evidence_quotes([gap], [self._make_chunk()])
        assert len(warnings) == 1
        assert "missing evidence_quote" in warnings[0]
        assert gap.confidence == "MEDIUM"

    def test_missing_quote_on_medium_confidence_no_warning(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(quote=None, confidence="MEDIUM")
        warnings = check_evidence_quotes([gap], [self._make_chunk()])
        assert warnings == []
        assert gap.confidence == "MEDIUM"

    def test_no_chunks_for_regulation_skips_quote_check(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(quote="irgendein erfundenes Zitat das nirgends steht")
        warnings = check_evidence_quotes([gap], [])
        assert warnings == []
        assert gap.confidence == "HIGH"

    def test_cannot_assess_skipped(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(quote="erfundenes Zitat", status=ComplianceStatus.CANNOT_ASSESS)
        warnings = check_evidence_quotes([gap], [self._make_chunk()])
        assert warnings == []

    def test_backwards_compatible_without_chunks_arg(self):
        from agent.validation import check_evidence_quotes
        gap = self._make_gap(quote=None, confidence="HIGH")
        warnings = check_evidence_quotes([gap])
        assert len(warnings) == 1
        assert gap.confidence == "MEDIUM"

    def test_short_generic_quote_not_flagged(self):
        from agent.validation import check_evidence_quotes
        # Fragments under the minimum length are too generic to verify — no false positive
        gap = self._make_gap(quote="Art. 30")
        warnings = check_evidence_quotes([gap], [self._make_chunk()])
        assert warnings == []
        assert gap.confidence == "HIGH"


class TestObligationClassifier:
    """Tests for rag.ingest._obligation negation handling."""

    def test_positive_muss_is_must(self):
        from rag.ingest import _obligation
        assert _obligation("Der Verantwortliche muss ein Verzeichnis führen.") == "MUST"

    def test_ist_verpflichtet_is_must(self):
        from rag.ingest import _obligation
        assert _obligation("Der Arbeitgeber ist verpflichtet, eine Meldestelle einzurichten.") == "MUST"

    def test_muss_nicht_is_not_must(self):
        from rag.ingest import _obligation
        assert _obligation("Der Betreiber muss nicht melden.") != "MUST"

    def test_ist_nicht_verpflichtet_is_not_must(self):
        from rag.ingest import _obligation
        assert _obligation("Das Unternehmen ist nicht verpflichtet, einen Bericht vorzulegen.") != "MUST"

    def test_besteht_keine_pflicht_is_not_must(self):
        from rag.ingest import _obligation
        assert _obligation("Es besteht keine Pflicht zur Benennung.") != "MUST"

    def test_shall_not_is_not_must(self):
        from rag.ingest import _obligation
        assert _obligation("The provider shall not disclose the data.") != "MUST"

    def test_negation_does_not_mask_separate_positive_obligation(self):
        from rag.ingest import _obligation
        text = (
            "Der Betreiber muss nicht jährlich berichten. "
            "Der Verantwortliche muss jedoch ein Verzeichnis führen."
        )
        assert _obligation(text) == "MUST"

    def test_kann_is_may(self):
        from rag.ingest import _obligation
        assert _obligation("Die Behörde kann eine Ausnahme gewähren.") == "MAY"

    def test_soll_is_should(self):
        from rag.ingest import _obligation
        assert _obligation("Der Arbeitgeber soll geeignete Maßnahmen treffen.") == "SHOULD"


class TestLegalVersionDate:
    """Tests for rag.ingest._legal_version_date (Rechtsstand extraction)."""

    def test_stand_zuletzt_geaendert(self):
        from rag.ingest import _legal_version_date
        text = "Gesetz X\nStand:Zuletzt geändert durch Art. 12 Abs. 4 G v. 29.6.2026 I Nr. 197\n§ 1 ..."
        assert _legal_version_date(text) == "2026-06-29"

    def test_stand_geaendert_without_zuletzt(self):
        from rag.ingest import _legal_version_date
        text = "Stand:Geändert durch Art. 25 G v. 5.7.2021 I 3338"
        assert _legal_version_date(text) == "2021-07-05"

    def test_ausfertigungsdatum_fallback(self):
        from rag.ingest import _legal_version_date
        text = "Gesetz Y\nAusfertigungsdatum: 16.07.2021\n§ 1 ..."
        assert _legal_version_date(text) == "2021-07-16"

    def test_stand_wins_over_ausfertigungsdatum(self):
        from rag.ingest import _legal_version_date
        text = (
            "Ausfertigungsdatum: 23.06.2021\n"
            "Stand:Zuletzt geändert durch Art. 3 G v. 10.3.2026 I Nr. 64\n"
        )
        assert _legal_version_date(text) == "2026-03-10"

    def test_no_date_returns_empty_string(self):
        from rag.ingest import _legal_version_date
        assert _legal_version_date("EDPB Guidelines on legitimate interests ...") == ""

    def test_real_statute_files_yield_dates(self):
        from pathlib import Path
        from rag.ingest import DATA_DIR, _legal_version_date
        # Every gesetze-im-internet.de full text fetched to disk must produce a date
        for rel in ["gwg/gwg_full_text.txt", "hinschg/hinschg_full_text.txt",
                    "lksg/lksg_full_text.txt", "milog/milog_full_text.txt"]:
            path = Path(DATA_DIR) / rel
            if not path.exists():
                continue
            date = _legal_version_date(path.read_text(encoding="utf-8"))
            assert date and date[:2] == "20", f"{rel}: no Rechtsstand extracted"


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
