"""Integrity tests for the structured obligation database (agent/obligations.py).

The registry is consumed by the obligation-first retrieval pipeline — every
entry must reference real CompanyProfile fields and valid regulation keys,
or retrieval/assessment will silently skip it.
"""
from agent.obligations import (
    OBLIGATION_REGISTRY,
    get_obligation_by_id,
    get_obligations,
)
from models.company_profile import CompanyProfile
from models.enums import Regulation

_VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

_ALL_OBLIGATIONS = [ob for obs in OBLIGATION_REGISTRY.values() for ob in obs]


class TestRegistryIntegrity:
    def test_registry_not_empty(self):
        assert len(_ALL_OBLIGATIONS) > 40

    def test_ids_are_unique(self):
        ids = [ob.id for ob in _ALL_OBLIGATIONS]
        assert len(ids) == len(set(ids)), f"duplicate ids: {[i for i in ids if ids.count(i) > 1]}"

    def test_registry_keys_are_valid_regulation_values(self):
        valid = {r.value for r in Regulation}
        for key in OBLIGATION_REGISTRY:
            assert key in valid, f"registry key '{key}' is not a Regulation enum value"

    def test_obligation_regulation_matches_registry_key(self):
        for key, obligations in OBLIGATION_REGISTRY.items():
            for ob in obligations:
                assert ob.regulation == key, (
                    f"{ob.id}: regulation '{ob.regulation}' != registry key '{key}'"
                )

    def test_required_profile_fields_exist_on_company_profile(self):
        profile_fields = set(CompanyProfile.model_fields)
        for ob in _ALL_OBLIGATIONS:
            for field in ob.required_profile_fields:
                assert field in profile_fields, (
                    f"{ob.id}: required_profile_field '{field}' does not exist on CompanyProfile"
                )

    def test_severities_are_valid(self):
        for ob in _ALL_OBLIGATIONS:
            assert ob.severity in _VALID_SEVERITIES, f"{ob.id}: invalid severity '{ob.severity}'"

    def test_every_obligation_has_article_and_actions(self):
        for ob in _ALL_OBLIGATIONS:
            assert ob.article.strip(), f"{ob.id}: empty article citation"
            assert len(ob.actions) >= 1, f"{ob.id}: no actions"
            assert ob.applies_when, f"{ob.id}: no applies_when conditions"
            assert ob.effort_estimate.strip(), f"{ob.id}: empty effort estimate"


class TestLookupFunctions:
    def test_get_obligations_known_regulation(self):
        assert len(get_obligations("gdpr_dsgvo")) >= 10

    def test_get_obligations_unknown_regulation_returns_empty(self):
        assert get_obligations("nonexistent") == []

    def test_get_obligation_by_id(self):
        ob = get_obligation_by_id("lksg_p5_risk_analysis")
        assert ob is not None
        assert ob.regulation == "lksg"
        assert "§ 5" in ob.article

    def test_get_obligation_by_unknown_id_returns_none(self):
        assert get_obligation_by_id("no_such_id") is None


class TestLksgCoverage:
    """LkSG obligations must cover the full §3(1) due diligence catalog."""

    def test_lksg_has_ten_obligations(self):
        assert len(get_obligations("lksg")) == 10

    def test_lksg_covers_core_duty_catalog(self):
        articles = " | ".join(ob.article for ob in get_obligations("lksg"))
        for section in ["§ 4", "§ 5", "§ 6", "§ 7", "§ 8", "§ 9", "§ 10"]:
            assert section in articles, f"LkSG duty catalog section '{section}' not covered"

    def test_lksg_report_obligation_mentions_bafa_submission(self):
        ob = get_obligation_by_id("lksg_p10_2_annual_report")
        assert any("§12" in a or "§ 12" in a or "BAFA" in a for a in ob.actions)


class TestEnefgCoverage:
    """EnEfG obligations must cover both consumption thresholds and the EDL-G audit."""

    def test_enefg_has_seven_obligations(self):
        assert len(get_obligations("enefg")) == 7

    def test_enefg_covers_core_sections(self):
        articles = " | ".join(ob.article for ob in get_obligations("enefg"))
        for section in ["§ 8", "§ 9", "§ 10", "§ 16", "§ 17", "EDL-G"]:
            assert section in articles, f"EnEfG section '{section}' not covered"

    def test_enms_obligation_references_energy_threshold_field(self):
        ob = get_obligation_by_id("enefg_p8_energy_management_system")
        assert "annual_energy_consumption_mwh" in ob.required_profile_fields

    def test_edlg_audit_mentions_iso50001_exemption(self):
        ob = get_obligation_by_id("enefg_edlg_p8_energy_audit")
        assert any("50001" in a or "EMAS" in a for a in ob.actions)


class TestGwgCoverage:
    """GwG obligations must cover risk management, KYC, reporting, and the register."""

    def test_gwg_has_eight_obligations(self):
        assert len(get_obligations("gwg")) == 8

    def test_gwg_covers_core_sections(self):
        articles = " | ".join(ob.article for ob in get_obligations("gwg"))
        for section in ["§§ 4-5", "§ 6", "§ 7", "§ 8", "§§ 10-13", "§ 15", "§ 20", "§§ 43, 45"]:
            assert section in articles, f"GwG section '{section}' not covered"

    def test_transparency_register_applies_beyond_obligated_parties(self):
        ob = get_obligation_by_id("gwg_p20_transparency_register")
        assert "regardless" in " ".join(ob.applies_when)

    def test_sar_obligation_mentions_goaml_and_tipping_off(self):
        ob = get_obligation_by_id("gwg_p43_45_suspicious_reports")
        text = " ".join(ob.actions)
        assert "goAML" in text
        assert "§47" in text or "§ 47" in text or "tipping" in text.lower()


class TestTtdsgCoverage:
    """TTDSG obligations must cover consent, exemptions, banner design, and transparency."""

    def test_ttdsg_has_four_obligations(self):
        assert len(get_obligations("ttdsg")) == 4

    def test_consent_obligation_requires_prior_blocking(self):
        ob = get_obligation_by_id("ttdsg_p25_endpoint_consent")
        text = " ".join(ob.actions)
        assert "BEFORE" in text or "before" in text

    def test_exemption_obligation_distinguishes_analytics(self):
        ob = get_obligation_by_id("ttdsg_p25_2_exemption_scope")
        text = " ".join(ob.actions)
        assert "analytics" in text.lower()

    def test_banner_obligation_requires_equal_reject(self):
        ob = get_obligation_by_id("ttdsg_banner_design_dsk")
        text = " ".join(ob.actions).lower()
        assert "reject" in text
