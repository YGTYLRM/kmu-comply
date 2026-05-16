"""
Unit tests for the deterministic threshold engine.
All threshold decisions must be code-driven, never LLM-driven.
"""

from services.threshold_engine import (
    check_gdpr,
    check_lksg,
    check_enefg,
    check_csrd,
    check_bdsg,
    determine_applicable_regulations,
)
from models.company_profile import CompanyProfile
from models.enums import Regulation


# ── GDPR ──────────────────────────────────────────────────────────────────────

class TestGDPR:
    def test_applies_when_processing_personal_data(self, profile_it_agency):
        result = check_gdpr(profile_it_agency)
        assert result.applies is True

    def test_does_not_apply_when_no_personal_data(self):
        profile = CompanyProfile(
            company_name="Bäckerei Müller",
            industry="retail",
            employee_count=10,
            processes_personal_data=False,
        )
        result = check_gdpr(profile)
        assert result.applies is False
        assert result.dpo_required is False
        assert result.processing_records_required is False

    def test_dpo_required_at_20_employees(self):
        profile = CompanyProfile(
            company_name="Test GmbH",
            industry="it_software",
            employee_count=20,
            processes_personal_data=True,
            processing_is_occasional=False,
        )
        assert check_gdpr(profile).dpo_required is True

    def test_dpo_not_required_at_19_employees(self):
        profile = CompanyProfile(
            company_name="Test GmbH",
            industry="it_software",
            employee_count=19,
            processes_personal_data=True,
            processing_is_occasional=False,
        )
        assert check_gdpr(profile).dpo_required is False

    def test_dpo_not_required_when_processing_occasional(self):
        profile = CompanyProfile(
            company_name="Test GmbH",
            industry="it_software",
            employee_count=100,
            processes_personal_data=True,
            processing_is_occasional=True,
        )
        assert check_gdpr(profile).dpo_required is False

    def test_processing_records_required_at_250_employees(self):
        profile = CompanyProfile(
            company_name="Big Corp GmbH",
            industry="manufacturing",
            employee_count=250,
            processes_personal_data=True,
            processing_is_occasional=True,
        )
        assert check_gdpr(profile).processing_records_required is True

    def test_processing_records_required_when_not_occasional(self):
        profile = CompanyProfile(
            company_name="Small Corp",
            industry="it_software",
            employee_count=5,
            processes_personal_data=True,
            processing_is_occasional=False,
        )
        assert check_gdpr(profile).processing_records_required is True

    def test_processing_records_required_for_special_category_data(self):
        profile = CompanyProfile(
            company_name="Clinic",
            industry="healthcare",
            employee_count=5,
            processes_personal_data=True,
            processes_special_category_data=True,
            processing_is_occasional=True,
        )
        assert check_gdpr(profile).processing_records_required is True

    def test_processing_records_not_required_small_occasional(self):
        profile = CompanyProfile(
            company_name="Freelancer",
            industry="consulting",
            employee_count=1,
            processes_personal_data=True,
            processes_special_category_data=False,
            processing_is_occasional=True,
        )
        assert check_gdpr(profile).processing_records_required is False

    def test_freelancer_profile(self, profile_freelancer):
        result = check_gdpr(profile_freelancer)
        assert result.applies is True
        assert result.dpo_required is False
        assert result.processing_records_required is False

    def test_healthcare_profile_special_data(self, profile_healthcare):
        result = check_gdpr(profile_healthcare)
        assert result.applies is True
        assert result.dpo_required is True
        assert result.processing_records_required is True


# ── LkSG ──────────────────────────────────────────────────────────────────────

class TestLkSG:
    def test_applies_at_1000_employees(self):
        profile = CompanyProfile(
            company_name="Large Corp",
            industry="manufacturing",
            employee_count=1000,
            processes_personal_data=False,
        )
        assert check_lksg(profile).applies is True

    def test_does_not_apply_at_999_employees(self):
        profile = CompanyProfile(
            company_name="Medium Corp",
            industry="manufacturing",
            employee_count=999,
            processes_personal_data=False,
        )
        assert check_lksg(profile).applies is False

    def test_does_not_apply_to_small_it_agency(self, profile_it_agency):
        assert check_lksg(profile_it_agency).applies is False

    def test_applies_to_large_listed(self, profile_large_listed):
        assert check_lksg(profile_large_listed).applies is True

    def test_does_not_apply_to_manufacturer_500(self, profile_manufacturer):
        assert check_lksg(profile_manufacturer).applies is False

    def test_reason_cites_paragraph(self):
        profile = CompanyProfile(
            company_name="Test",
            industry="manufacturing",
            employee_count=1000,
            processes_personal_data=False,
        )
        result = check_lksg(profile)
        assert "§1(1)" in result.reason
        assert "LkSG" in result.reason


# ── EnEfG ──────────────────────────────────────────────────────────────────────

class TestEnEfG:
    def test_audit_required_above_250_employees(self):
        profile = CompanyProfile(
            company_name="Big Corp",
            industry="manufacturing",
            employee_count=251,
            processes_personal_data=False,
        )
        result = check_enefg(profile)
        assert result.edl_g_audit_required is True

    def test_audit_not_required_below_250_employees_low_revenue(self):
        profile = CompanyProfile(
            company_name="Small Corp",
            industry="manufacturing",
            employee_count=50,
            annual_revenue_eur=10_000_000,
            processes_personal_data=False,
        )
        result = check_enefg(profile)
        assert result.edl_g_audit_required is False

    def test_audit_required_by_revenue_above_50m(self):
        profile = CompanyProfile(
            company_name="Revenue Corp",
            industry="retail",
            employee_count=100,
            annual_revenue_eur=51_000_000,
            processes_personal_data=False,
        )
        result = check_enefg(profile)
        assert result.edl_g_audit_required is True

    def test_energy_management_required_at_7500_mwh(self):
        # Must be non-SME (>=250 employees) for EnEfG energy management to apply
        profile = CompanyProfile(
            company_name="Energy Corp",
            industry="manufacturing",
            employee_count=300,
            annual_energy_consumption_mwh=7500,
            processes_personal_data=False,
        )
        result = check_enefg(profile)
        assert result.energy_management_required is True

    def test_energy_management_not_required_below_7500_mwh(self):
        profile = CompanyProfile(
            company_name="Big Energy",
            industry="manufacturing",
            employee_count=300,
            annual_energy_consumption_mwh=7499,
            processes_personal_data=False,
        )
        result = check_enefg(profile)
        assert result.energy_management_required is False

    def test_waste_heat_required_for_nonsme(self):
        # All non-SMEs get waste_heat_reporting_required=True — the 200 kW technical
        # threshold (EnEfG §15) cannot be derived from a company profile alone
        profile = CompanyProfile(
            company_name="Factory",
            industry="manufacturing",
            employee_count=300,
            annual_energy_consumption_mwh=2500,
            processes_personal_data=False,
        )
        result = check_enefg(profile)
        assert result.waste_heat_reporting_required is True

    def test_waste_heat_not_required_for_sme(self):
        # SMEs are exempt from EnEfG entirely
        profile = CompanyProfile(
            company_name="Small Factory",
            industry="manufacturing",
            employee_count=50,
            annual_energy_consumption_mwh=2500,
            processes_personal_data=False,
        )
        result = check_enefg(profile)
        assert result.waste_heat_reporting_required is False

    def test_manufacturer_profile_applies(self, profile_manufacturer):
        result = check_enefg(profile_manufacturer)
        assert result.applies is True
        assert result.edl_g_audit_required is True
        assert result.energy_management_required is True
        assert result.waste_heat_reporting_required is True

    def test_it_agency_does_not_apply(self, profile_it_agency):
        result = check_enefg(profile_it_agency)
        assert result.applies is False


# ── CSRD ──────────────────────────────────────────────────────────────────────

class TestCSRD:
    def test_applies_with_two_criteria(self):
        profile = CompanyProfile(
            company_name="Mid Corp",
            industry="retail",
            employee_count=260,
            annual_revenue_eur=60_000_000,
            processes_personal_data=False,
        )
        result = check_csrd(profile)
        assert result.applies is True
        assert result.criteria_met == 2

    def test_does_not_apply_with_one_criterion(self):
        profile = CompanyProfile(
            company_name="Small Corp",
            industry="retail",
            employee_count=260,
            annual_revenue_eur=10_000_000,
            processes_personal_data=False,
        )
        result = check_csrd(profile)
        assert result.applies is False
        assert result.criteria_met == 1

    def test_applies_with_all_three_criteria(self, profile_large_listed):
        result = check_csrd(profile_large_listed)
        assert result.applies is True
        assert result.criteria_met == 3

    def test_applies_to_listed_company_regardless_of_size(self):
        profile = CompanyProfile(
            company_name="Listed Startup",
            industry="it_software",
            employee_count=30,
            annual_revenue_eur=5_000_000,
            is_listed_company=True,
            processes_personal_data=False,
        )
        result = check_csrd(profile)
        assert result.applies is True

    def test_does_not_apply_to_small_it_agency(self, profile_it_agency):
        result = check_csrd(profile_it_agency)
        assert result.applies is False

    def test_balance_sheet_criterion(self):
        profile = CompanyProfile(
            company_name="Asset Heavy",
            industry="finance",
            employee_count=260,
            balance_sheet_total_eur=30_000_000,
            processes_personal_data=False,
        )
        result = check_csrd(profile)
        assert result.applies is True
        assert result.criteria_met == 2


# ── BDSG ──────────────────────────────────────────────────────────────────────

class TestBDSG:
    def test_applies_to_german_company_processing_data(self, profile_it_agency):
        result = check_bdsg(profile_it_agency)
        assert result.applies is True

    def test_does_not_apply_to_non_german_company(self):
        profile = CompanyProfile(
            company_name="UK Ltd",
            industry="it_software",
            country="GB",
            employee_count=10,
            processes_personal_data=True,
        )
        result = check_bdsg(profile)
        assert result.applies is False

    def test_does_not_apply_without_personal_data(self):
        profile = CompanyProfile(
            company_name="No Data GmbH",
            industry="manufacturing",
            employee_count=30,
            processes_personal_data=False,
        )
        result = check_bdsg(profile)
        assert result.applies is False

    def test_dpo_required_at_20_employees(self):
        profile = CompanyProfile(
            company_name="Tech GmbH",
            industry="it_software",
            employee_count=20,
            processes_personal_data=True,
            processing_is_occasional=False,
        )
        result = check_bdsg(profile)
        assert result.dpo_required is True

    def test_reason_cites_paragraph(self, profile_it_agency):
        result = check_bdsg(profile_it_agency)
        assert "BDSG" in result.reason


# ── Integration: determine_applicable_regulations ────────────────────────────

class TestDetermineApplicableRegulations:
    def test_returns_all_eleven_regulations(self, profile_it_agency):
        results = determine_applicable_regulations(profile_it_agency)
        assert len(results) == 11
        regs = {r.regulation for r in results}
        assert regs == {
            Regulation.GDPR, Regulation.LKSG, Regulation.ENEFG, Regulation.CSRD,
            Regulation.BDSG, Regulation.NIS2, Regulation.AI_ACT, Regulation.HINSCHG,
            Regulation.ARBSCHG, Regulation.AGG, Regulation.MILOG,
        }

    def test_it_agency_only_gdpr_and_bdsg_apply(self, profile_it_agency):
        results = determine_applicable_regulations(profile_it_agency)
        applicable = {r.regulation for r in results if r.applies}
        assert Regulation.GDPR in applicable
        assert Regulation.BDSG in applicable
        assert Regulation.LKSG not in applicable
        assert Regulation.CSRD not in applicable

    def test_large_listed_all_regulations_apply(self, profile_large_listed):
        results = determine_applicable_regulations(profile_large_listed)
        applicable = {r.regulation for r in results if r.applies}
        # All regulations apply to a large listed company except AI Act (no AI systems in profile)
        assert Regulation.GDPR in applicable
        assert Regulation.LKSG in applicable
        assert Regulation.ENEFG in applicable
        assert Regulation.CSRD in applicable
        assert Regulation.BDSG in applicable
        assert Regulation.NIS2 in applicable
        assert Regulation.HINSCHG in applicable
        assert Regulation.ARBSCHG in applicable
        assert Regulation.AGG in applicable
        assert Regulation.MILOG in applicable

    def test_freelancer_minimal_obligations(self, profile_freelancer):
        results = determine_applicable_regulations(profile_freelancer)
        applicable = {r.regulation for r in results if r.applies}
        assert Regulation.GDPR in applicable
        assert Regulation.LKSG not in applicable
        assert Regulation.CSRD not in applicable

    def test_all_results_have_reason(self, profile_manufacturer):
        results = determine_applicable_regulations(profile_manufacturer)
        for r in results:
            assert r.reason, f"Missing reason for {r.regulation}"

    def test_all_results_have_key_threshold(self, profile_manufacturer):
        results = determine_applicable_regulations(profile_manufacturer)
        for r in results:
            assert r.key_threshold, f"Missing key_threshold for {r.regulation}"
