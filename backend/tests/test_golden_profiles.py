"""
Golden profile test set — regression guard for the compliance analysis system.

Two test layers:
  1. test_threshold_* — pure unit tests, no LLM, deterministic. Run always.
     Assert which regulations apply for 5 canonical company profiles.

  2. test_e2e_* — integration tests requiring a real ANTHROPIC_API_KEY.
     Assert that the full pipeline gives a sensible compliance direction
     (compliant ↔ non-compliant) for two extreme profiles.
     Mark with: pytest -m e2e  (skipped in CI unless key is set)

Run: pytest tests/test_golden_profiles.py -v
     pytest tests/test_golden_profiles.py -v -m e2e  # also runs LLM tests
"""
from __future__ import annotations

import os
import pytest

from models.company_profile import CompanyProfile
from models.enums import ComplianceStatus, Regulation
from services.threshold_engine import determine_applicable_regulations


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _applies(profile: CompanyProfile, reg: Regulation) -> bool:
    results = determine_applicable_regulations(profile)
    for r in results:
        if r.regulation == reg:
            return r.applies
    raise AssertionError(f"Regulation {reg} not found in results")


def _applicability_map(profile: CompanyProfile) -> dict[Regulation, bool]:
    return {r.regulation: r.applies for r in determine_applicable_regulations(profile)}


# ─────────────────────────────────────────────────────────────────────────────
# Profile 1 — Tiny IT startup (8 employees)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def tiny_it_startup() -> CompanyProfile:
    return CompanyProfile(
        company_name="TestCo GmbH",
        industry="it_software",
        country="DE",
        employee_count=8,
        processes_personal_data=True,
        processing_is_occasional=False,
        has_website=True,
    )


def test_tiny_it_startup_applies(tiny_it_startup):
    m = _applicability_map(tiny_it_startup)
    # Must apply
    assert m[Regulation.GDPR],    "GDPR must apply (processes personal data)"
    assert m[Regulation.BDSG],    "BDSG must apply (DE + personal data)"
    assert m[Regulation.TTDSG],   "TTDSG must apply (has website + personal data)"
    assert m[Regulation.ARBSCHG], "ArbSchG applies to all employers"
    assert m[Regulation.AGG],     "AGG applies to all employers"
    assert m[Regulation.MILOG],   "MiLoG applies to all employers"
    # Must NOT apply
    assert not m[Regulation.NIS2],        "NIS2: 8 employees < 50 minimum threshold"
    assert not m[Regulation.HINSCHG],     "HinSchG: 8 employees < 50 threshold"
    assert not m[Regulation.LKSG],        "LkSG: 8 employees < 1,000 threshold"
    assert not m[Regulation.ENEFG],       "EnEfG: 8 employees < 250, qualifies as SME"
    assert not m[Regulation.CSRD],        "CSRD: 8 employees, no size criteria met"
    assert not m[Regulation.GWG],         "GwG: IT is not an AML-obligated sector"
    assert not m[Regulation.EU_DATA_ACT], "EU Data Act: no connected products or cloud services"


# ─────────────────────────────────────────────────────────────────────────────
# Profile 2 — Healthcare SME (85 employees, special category data)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def healthcare_sme() -> CompanyProfile:
    return CompanyProfile(
        company_name="MedService GmbH",
        industry="healthcare",
        country="DE",
        employee_count=85,
        processes_personal_data=True,
        processes_special_category_data=True,
        processing_is_occasional=False,
        has_website=True,
    )


def test_healthcare_sme_applies(healthcare_sme):
    m = _applicability_map(healthcare_sme)
    assert m[Regulation.GDPR]
    assert m[Regulation.BDSG]
    assert m[Regulation.TTDSG]
    assert m[Regulation.NIS2],    "NIS2: healthcare Annex I sector, 85 >= 50 employees (wichtige Einrichtung)"
    assert m[Regulation.HINSCHG], "HinSchG: 85 employees >= 50 threshold"
    assert m[Regulation.ARBSCHG]
    assert m[Regulation.AGG]
    assert m[Regulation.MILOG]
    assert not m[Regulation.LKSG],        "LkSG: 85 employees < 1,000"
    assert not m[Regulation.ENEFG],       "EnEfG: 85 employees < 250, qualifies as SME"
    assert not m[Regulation.CSRD],        "CSRD: 85 employees < 250, 0 criteria met"
    assert not m[Regulation.GWG],         "GwG: healthcare not AML-obligated"
    assert not m[Regulation.EU_DATA_ACT], "EU Data Act: no connected products flagged"


def test_healthcare_sme_nis2_entity_type(healthcare_sme):
    from services.threshold_engine import check_nis2
    result = check_nis2(healthcare_sme)
    assert result.applies
    assert result.important, "85-employee healthcare company is wichtige Einrichtung (Annex I, medium)"
    assert not result.particularly_important, "Not besonders wichtig (< 250 employees)"


# ─────────────────────────────────────────────────────────────────────────────
# Profile 3 — Large manufacturer (600 employees, €200M revenue)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def large_manufacturer() -> CompanyProfile:
    return CompanyProfile(
        company_name="IndustrieAG GmbH",
        industry="manufacturing",
        country="DE",
        employee_count=600,
        annual_revenue_eur=200_000_000,
        processes_personal_data=True,
        processing_is_occasional=False,
        has_supply_chain_abroad=True,
        has_website=True,
    )


def test_large_manufacturer_applies(large_manufacturer):
    m = _applicability_map(large_manufacturer)
    assert m[Regulation.GDPR]
    assert m[Regulation.BDSG]
    assert m[Regulation.TTDSG]
    assert m[Regulation.NIS2],    "NIS2: manufacturing Annex II, 600 employees >= 50"
    assert m[Regulation.HINSCHG], "HinSchG: 600 >= 50"
    assert m[Regulation.ARBSCHG]
    assert m[Regulation.AGG]
    assert m[Regulation.MILOG]
    assert m[Regulation.ENEFG],   "EnEfG: 600 employees >= 250, non-SME"
    assert m[Regulation.CSRD],    "CSRD: 600 > 250 employees AND €200M > €50M revenue → 2/3 criteria"
    assert not m[Regulation.LKSG],        "LkSG: 600 < 1,000 employees"
    assert not m[Regulation.GWG],         "GwG: manufacturing not AML-obligated"
    assert not m[Regulation.EU_DATA_ACT], "EU Data Act: no connected products flagged"


def test_large_manufacturer_csrd_wave(large_manufacturer):
    from services.threshold_engine import check_csrd
    result = check_csrd(large_manufacturer)
    assert result.applies
    assert result.criteria_met >= 2
    assert result.wave == 2, "Large non-PIE company is Wave 2"


# ─────────────────────────────────────────────────────────────────────────────
# Profile 4 — Finance advisory firm (20 employees)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def finance_firm() -> CompanyProfile:
    return CompanyProfile(
        company_name="FinanzBerater GmbH",
        industry="finance",
        country="DE",
        employee_count=20,
        processes_personal_data=True,
        processing_is_occasional=False,
        has_website=True,
        is_aml_obligated_sector=True,
    )


def test_finance_firm_applies(finance_firm):
    m = _applicability_map(finance_firm)
    assert m[Regulation.GDPR]
    assert m[Regulation.BDSG]
    assert m[Regulation.TTDSG]
    assert m[Regulation.GWG],     "GwG: finance is AML-obligated sector under §2 GwG"
    assert m[Regulation.ARBSCHG]
    assert m[Regulation.AGG]
    assert m[Regulation.MILOG]
    # Below NIS2 size threshold despite being in Annex I sector
    assert not m[Regulation.NIS2],    "NIS2: 20 employees < 50 minimum (no revenue provided)"
    assert not m[Regulation.HINSCHG], "HinSchG: 20 < 50"
    assert not m[Regulation.LKSG]
    assert not m[Regulation.ENEFG]
    assert not m[Regulation.CSRD]
    assert not m[Regulation.EU_DATA_ACT]


def test_finance_firm_bdsg_dpo_required(finance_firm):
    from services.threshold_engine import check_bdsg
    result = check_bdsg(finance_firm)
    assert result.applies
    assert result.dpo_required, "DPO required: 20 employees >= 20 threshold (BDSG §38)"


# ─────────────────────────────────────────────────────────────────────────────
# Profile 5 — Large logistics enterprise with AI (1,500 employees)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def large_logistics_ai() -> CompanyProfile:
    return CompanyProfile(
        company_name="LogistikGruppe AG",
        industry="logistics",
        country="DE",
        employee_count=1500,
        annual_revenue_eur=100_000_000,
        processes_personal_data=True,
        processing_is_occasional=False,
        has_supply_chain_abroad=True,
        uses_ai_systems=True,
        ai_systems_are_high_risk=True,
        has_website=True,
    )


def test_large_logistics_ai_applies(large_logistics_ai):
    m = _applicability_map(large_logistics_ai)
    assert m[Regulation.GDPR]
    assert m[Regulation.BDSG]
    assert m[Regulation.TTDSG]
    assert m[Regulation.NIS2],    "NIS2: logistics Annex II, 1500 >= 50"
    assert m[Regulation.AI_ACT],  "EU AI Act: company deploys AI systems"
    assert m[Regulation.HINSCHG], "HinSchG: 1500 >= 50"
    assert m[Regulation.ARBSCHG]
    assert m[Regulation.AGG]
    assert m[Regulation.MILOG]
    assert m[Regulation.LKSG],    "LkSG: 1,500 employees >= 1,000 threshold"
    assert m[Regulation.ENEFG],   "EnEfG: 1,500 >= 250, non-SME"
    assert m[Regulation.CSRD],    "CSRD: 1500 > 250 AND €100M > €50M → 2/3 criteria"
    assert not m[Regulation.GWG],         "GwG: logistics not AML-obligated"
    assert not m[Regulation.EU_DATA_ACT], "EU Data Act: no connected products or cloud services"


# ─────────────────────────────────────────────────────────────────────────────
# Profile 6 — IoT manufacturer triggering EU Data Act
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def iot_manufacturer() -> CompanyProfile:
    return CompanyProfile(
        company_name="SmartDevice GmbH",
        industry="manufacturing",
        country="DE",
        employee_count=45,
        processes_personal_data=True,
        processing_is_occasional=False,
        has_website=True,
        produces_connected_products=True,
    )


def test_iot_manufacturer_eu_data_act(iot_manufacturer):
    m = _applicability_map(iot_manufacturer)
    assert m[Regulation.EU_DATA_ACT], "EU Data Act applies: company produces connected products"
    assert not m[Regulation.LKSG],    "LkSG: 45 < 1,000"
    assert not m[Regulation.ENEFG],   "EnEfG: 45 < 250"
    assert not m[Regulation.NIS2],    "NIS2: 45 < 50 minimum threshold"


# ─────────────────────────────────────────────────────────────────────────────
# E2E tests — require ANTHROPIC_API_KEY, skipped otherwise
# ─────────────────────────────────────────────────────────────────────────────

e2e = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping LLM e2e tests",
)


@e2e
def test_e2e_fully_compliant_profile():
    """A company with ALL compliance measures in place must not be rated NON_COMPLIANT."""
    from agent.planning import determine_applicability, retrieve_regulatory_context, run_gap_analysis
    from agent.profiling import enrich_profile

    profile = CompanyProfile(
        company_name="MusterCompliant GmbH",
        industry="it_software",
        country="DE",
        employee_count=30,
        processes_personal_data=True,
        processing_is_occasional=False,
        has_website=True,
        # GDPR / BDSG measures all in place
        has_privacy_policy=True,
        has_processor_agreements=True,
        has_data_breach_procedure=True,
        has_tom_documentation=True,
        has_data_retention_policy=True,
        has_data_protection_training=True,
        has_consent_management=True,
        transfers_data_outside_eea=False,
        # TTDSG
        has_cookie_banner=True,
        has_cookie_policy=True,
        # ArbSchG
        has_gefaehrdungsbeurteilung=True,
        has_gefaehrdungsbeurteilung_documented=True,
        has_first_aid_measures=True,
        has_employee_safety_training=True,
        # AGG
        has_anti_discrimination_policy=True,
        has_agc_complaints_procedure=True,
        # MiLoG
        has_working_time_records=True,
    )

    enriched = enrich_profile(profile)
    applicability = determine_applicability(enriched)
    chunks = retrieve_regulatory_context(enriched, applicability)
    gaps = run_gap_analysis(enriched, chunks, [])

    non_compliant = [
        g for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT
    ]
    assert not non_compliant, (
        f"Fully-documented company should have zero NON_COMPLIANT gaps. "
        f"Got: {[(g.regulation, g.article) for g in non_compliant]}"
    )


@e2e
def test_e2e_bare_minimum_profile():
    """A company with NO compliance measures must not be rated COMPLIANT for core regulations."""
    from agent.planning import determine_applicability, retrieve_regulatory_context, run_gap_analysis
    from agent.profiling import enrich_profile

    profile = CompanyProfile(
        company_name="NullCompliance GmbH",
        industry="it_software",
        country="DE",
        employee_count=30,
        processes_personal_data=True,
        processing_is_occasional=False,
        has_website=True,
        # All measures explicitly absent
        has_privacy_policy=False,
        has_processor_agreements=False,
        has_data_breach_procedure=False,
        has_tom_documentation=False,
        has_data_retention_policy=False,
        has_cookie_banner=False,
        has_gefaehrdungsbeurteilung=False,
        has_anti_discrimination_policy=False,
        has_working_time_records=False,
    )

    enriched = enrich_profile(profile)
    applicability = determine_applicability(enriched)
    chunks = retrieve_regulatory_context(enriched, applicability)
    gaps = run_gap_analysis(enriched, chunks, [])

    compliant_gaps = [
        g for g in gaps if g.status == ComplianceStatus.COMPLIANT
    ]
    non_compliant_or_partial = [
        g for g in gaps
        if g.status in (ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT)
    ]
    assert non_compliant_or_partial, (
        "Company with no measures in place must have at least one NON_COMPLIANT or PARTIALLY_COMPLIANT gap."
    )
    assert len(compliant_gaps) < len(non_compliant_or_partial), (
        "Company with no measures should have more issues than compliant items."
    )
