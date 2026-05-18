"""
Deterministic regulation applicability + required-field rule engine.

This module never calls an LLM. All decisions are based on hard thresholds
sourced from the same regulatory texts as services/threshold_engine.py.

The key addition over threshold_engine is:
  - required_fields: the CompanyProfile attributes needed to make each decision
  - missing_fields(): which of those are None/unset for a given profile
  - confidence grading based on field completeness

Usage:
    engine = RuleEngine()
    results = engine.check_all(profile)   # dict[str, ApplicabilityResult]
    result  = engine.check_one("gdpr_dsgvo", profile)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from models.company_profile import CompanyProfile

logger = logging.getLogger(__name__)

RULE_ENGINE_VERSION = "v1.0.0"

# Industries that are in NIS2 Annex I (critical)
_NIS2_ANNEX_I = {
    "energy", "transport", "finance", "healthcare", "water",
    "digital", "it_software", "space", "government",
}
# Industries in NIS2 Annex II (important)
_NIS2_ANNEX_II = {
    "manufacturing", "chemicals", "food_beverage", "logistics",
    "waste", "construction", "research",
}
_NIS2_ALL_SECTORS = _NIS2_ANNEX_I | _NIS2_ANNEX_II

# GwG (AML) obligated industries
_GWG_SECTORS = {
    "finance", "real_estate", "financial_services", "banking",
    "crypto", "gambling", "insurance",
}


@dataclass
class ApplicabilityResult:
    """Result of a single regulation applicability check."""
    regulation: str
    applies: bool
    confidence: str          # "HIGH", "MEDIUM", "LOW"
    reason: str
    required_fields: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "regulation": self.regulation,
            "applies": self.applies,
            "confidence": self.confidence,
            "reason": self.reason,
            "required_fields": self.required_fields,
            "missing_fields": self.missing_fields,
        }


def _missing(profile: CompanyProfile, fields: list[str]) -> list[str]:
    """Return which fields are None on the profile."""
    return [f for f in fields if getattr(profile, f, None) is None]


def _confidence(missing_count: int, total_required: int) -> str:
    if total_required == 0:
        return "HIGH"
    ratio = missing_count / total_required
    if ratio == 0:
        return "HIGH"
    if ratio <= 0.5:
        return "MEDIUM"
    return "LOW"


class RuleEngine:
    """
    Deterministic applicability checks for all 14 regulations.

    Each check_ method returns an ApplicabilityResult. The rule logic mirrors
    services/threshold_engine.py but adds structured field-tracking.
    """

    # ── Individual regulation checks ─────────────────────────────────────────

    def check_gdpr_dsgvo(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "gdpr_dsgvo"
        required = ["processes_personal_data"]
        # Secondary fields that improve precision
        secondary = ["has_website", "has_employees"]
        missing = _missing(profile, required)

        # Applies if processes personal data OR has website OR has employees
        # (any employer has employee personal data; any website may process visitor data)
        applies = (
            profile.processes_personal_data
            or profile.has_website
            or profile.employee_count >= 1
        )

        # If processes_personal_data is explicitly set, confidence is deterministic
        conf = "HIGH" if len(missing) == 0 else "MEDIUM"

        if applies:
            reasons = []
            if profile.processes_personal_data:
                reasons.append("processes personal data (Art. 2 GDPR)")
            if profile.has_website:
                reasons.append("operates a website (implicit personal data processing)")
            if profile.employee_count >= 1:
                reasons.append(f"employs {profile.employee_count} people (employee data processing)")
            reason = "GDPR applies: " + "; ".join(reasons) + "."
        else:
            reason = "GDPR does not apply: company does not process personal data and has no website or employees."

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_bdsg(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "bdsg"
        required = ["processes_personal_data"]
        missing = _missing(profile, required)

        applies = profile.country == "DE" and profile.processes_personal_data
        conf = "HIGH" if not missing else "MEDIUM"

        if applies:
            reason = "BDSG applies: German company processing personal data (BDSG §1)."
        elif profile.country != "DE":
            reason = "BDSG does not apply: company is not in Germany."
        else:
            reason = "BDSG does not apply: company does not process personal data."

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_nis2(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "nis2"
        required = ["employee_count", "is_critical_infrastructure_sector"]
        optional_size = ["annual_revenue_eur"]
        missing = _missing(profile, required)

        in_scope_sector = (
            profile.is_critical_infrastructure_sector
            or profile.industry in _NIS2_ALL_SECTORS
        )

        is_medium_or_above = (
            profile.employee_count >= 50
            or (profile.annual_revenue_eur is not None and profile.annual_revenue_eur >= 10_000_000)
        )

        applies = in_scope_sector and is_medium_or_above

        # Confidence: HIGH if sector is clear + size is clear; MEDIUM if sector is ambiguous
        sector_known = profile.industry in _NIS2_ALL_SECTORS or profile.is_critical_infrastructure_sector
        conf = "HIGH" if (sector_known and not missing) else "MEDIUM" if in_scope_sector else "LOW"

        if applies:
            entity_type = "besonders wichtige Einrichtung" if profile.employee_count >= 250 else "wichtige Einrichtung"
            reason = (
                f"NIS2 (BSIG) applies as {entity_type}: "
                f"{profile.employee_count} employees in critical/important sector '{profile.industry}'."
            )
        elif not in_scope_sector:
            reason = f"NIS2 does not apply: industry '{profile.industry}' is not in a NIS2 critical or important sector."
        else:
            reason = (
                f"NIS2 does not apply: below size thresholds "
                f"({profile.employee_count} employees < 50 minimum)."
            )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_eu_ai_act(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "eu_ai_act"
        required = ["uses_ai_systems"]
        missing = _missing(profile, required)

        applies = bool(profile.uses_ai_systems)
        conf = "HIGH" if not missing else "LOW"

        reason = (
            "EU AI Act applies: company develops or deploys AI systems (Art. 2)."
            if applies
            else "EU AI Act does not apply: company does not develop or deploy AI systems."
        )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_hinschg(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "hinschg"
        required = ["employee_count"]
        missing = _missing(profile, required)

        applies = profile.employee_count >= 50
        conf = "HIGH" if not missing else "LOW"

        reason = (
            f"HinSchG applies: {profile.employee_count} employees >= 50 — "
            f"internal whistleblower reporting channel mandatory (§12 HinSchG)."
            if applies
            else f"HinSchG does not apply: {profile.employee_count} employees < 50 threshold (§12 HinSchG)."
        )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_lksg(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "lksg"
        required = ["employee_count"]
        missing = _missing(profile, required)

        applies = profile.employee_count >= 1000
        conf = "HIGH" if not missing else "LOW"

        reason = (
            f"LkSG applies: {profile.employee_count} employees >= 1,000 threshold (§1(1) LkSG, from 1 Jan 2024)."
            if applies
            else f"LkSG does not apply: {profile.employee_count} employees < 1,000 threshold (§1(1) LkSG)."
        )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_enefg(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "enefg"
        required = ["employee_count"]
        optional = ["annual_energy_consumption_mwh", "annual_revenue_eur", "balance_sheet_total_eur"]
        missing = _missing(profile, required)

        energy_mwh = profile.annual_energy_consumption_mwh or 0
        energy_gwh = energy_mwh / 1000

        is_non_sme = (
            profile.employee_count >= 250
            or (profile.annual_revenue_eur is not None and profile.annual_revenue_eur > 50_000_000)
            or (profile.balance_sheet_total_eur is not None and profile.balance_sheet_total_eur > 43_000_000)
        )
        high_energy = energy_gwh > 7.5

        applies = is_non_sme or high_energy

        # Confidence reduced if energy consumption not provided (common trigger)
        energy_known = profile.annual_energy_consumption_mwh is not None
        conf = "HIGH" if (not missing and energy_known) else "MEDIUM"

        if applies:
            parts = []
            if is_non_sme:
                parts.append(f"{profile.employee_count} employees >= 250 (non-SME) → EDL-G §8 energy audit")
            if high_energy:
                parts.append(f"energy consumption {energy_gwh:.1f} GWh > 7.5 GWh → EnEfG §8(1) management system")
            reason = f"EnEfG / EDL-G apply: {'; '.join(parts)}."
        else:
            energy_note = (
                "energy consumption not provided (provide to check EnEfG §8(1))"
                if not energy_known
                else f"energy {energy_gwh:.1f} GWh <= 7.5 GWh"
            )
            reason = (
                f"EnEfG / EDL-G do not apply: {profile.employee_count} employees < 250 (qualifies as SME); "
                f"{energy_note}."
            )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_csrd(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "csrd"
        required = ["employee_count"]
        optional = ["annual_revenue_eur", "balance_sheet_total_eur"]
        missing = _missing(profile, required)

        criteria_met = 0
        if profile.employee_count > 250:
            criteria_met += 1
        if profile.annual_revenue_eur is not None and profile.annual_revenue_eur > 50_000_000:
            criteria_met += 1
        if profile.balance_sheet_total_eur is not None and profile.balance_sheet_total_eur > 25_000_000:
            criteria_met += 1

        is_large = criteria_met >= 2
        applies = is_large or profile.is_listed_company

        # Confidence: MEDIUM if revenue/balance sheet not provided (might be missing a criterion)
        financials_known = (
            profile.annual_revenue_eur is not None
            and profile.balance_sheet_total_eur is not None
        )
        conf = "HIGH" if (financials_known and not missing) else "MEDIUM"

        if applies:
            omnibus_note = " NOTE: Omnibus simplification (>1,000 employees AND >€450M revenue) pending formal adoption — verify current scope."
            reason = (
                f"CSRD applies: {criteria_met}/3 size criteria met "
                f"(EU Directive 2022/2464, Art. 5).{omnibus_note}"
            )
        else:
            reason = (
                f"CSRD does not apply: only {criteria_met}/3 size criteria met "
                f"(need 2/3: >250 employees, >€50M revenue, >€25M balance sheet)."
            )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_workplace_law(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "workplace_law"
        required = ["employee_count"]
        missing = _missing(profile, required)

        applies = profile.employee_count >= 1
        conf = "HIGH"

        reason = (
            f"ArbSchG applies to all employers: {profile.employee_count} employees "
            f"(ArbSchG §1 — applies to all employers in Germany regardless of size)."
            if applies
            else "ArbSchG does not apply: no employees reported."
        )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_agg(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "agg"
        required = ["employee_count"]
        missing = _missing(profile, required)

        applies = profile.employee_count >= 1
        conf = "HIGH"

        reason = (
            f"AGG applies to all employers: {profile.employee_count} employees. "
            f"Anti-discrimination measures (§12 AGG) and complaints procedure (§13 AGG) mandatory."
            if applies
            else "AGG does not apply: no employees reported."
        )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_milog(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "milog"
        required = ["employee_count"]
        missing = _missing(profile, required)

        applies = profile.employee_count >= 1
        conf = "HIGH"

        reason = (
            f"MiLoG applies to all employers: {profile.employee_count} employees. "
            f"Statutory minimum wage (EUR 12.82/hour, 2025) and working time records (§17 MiLoG) mandatory."
            if applies
            else "MiLoG does not apply: no employees reported."
        )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_ttdsg(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "ttdsg"
        required = ["has_website"]
        missing = _missing(profile, required)

        applies = profile.has_website
        conf = "HIGH" if not missing else "MEDIUM"

        reason = (
            "TTDSG (§25 TDDDG) applies: company operates a website. "
            "Prior informed consent required before setting non-essential cookies or tracking."
            if applies
            else "TTDSG does not apply: company has no public-facing website or app."
        )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_gwg(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "gwg"
        required = ["is_aml_obligated_sector"]
        missing = _missing(profile, required)

        in_gwg_sector = profile.industry in _GWG_SECTORS
        applies = in_gwg_sector or profile.is_aml_obligated_sector
        conf = "HIGH" if not missing else "MEDIUM"

        if applies:
            trigger = (
                f"industry '{profile.industry}' is a GwG-obligated sector"
                if in_gwg_sector
                else "company self-declared as AML-obligated (is_aml_obligated_sector=true)"
            )
            reason = f"GwG applies: {trigger} (§2 GwG). Risk analysis, KYC, and AML officer obligations apply."
        else:
            reason = (
                f"GwG does not apply: industry '{profile.industry}' is not in an AML-obligated sector. "
                f"Set is_aml_obligated_sector=true if the company provides financial, crypto, legal, or gambling services."
            )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    def check_eu_data_act(self, profile: CompanyProfile) -> ApplicabilityResult:
        reg = "eu_data_act"
        required = ["produces_connected_products", "provides_data_processing_services"]
        missing = _missing(profile, required)

        applies = profile.produces_connected_products or profile.provides_data_processing_services
        conf = "HIGH" if not missing else "MEDIUM"

        if applies:
            parts = []
            if profile.produces_connected_products:
                parts.append("manufactures connected (IoT) products (Art. 3-4)")
            if profile.provides_data_processing_services:
                parts.append("provides cloud/data processing services (Art. 23-25)")
            reason = f"EU Data Act applies: {'; '.join(parts)}."
        else:
            reason = (
                "EU Data Act does not apply: company does not manufacture connected products "
                "and does not provide data processing services."
            )

        return ApplicabilityResult(
            regulation=reg,
            applies=applies,
            confidence=conf,
            reason=reason,
            required_fields=required,
            missing_fields=missing,
        )

    # ── Master check ──────────────────────────────────────────────────────────

    _CHECKS = {
        "gdpr_dsgvo":    "check_gdpr_dsgvo",
        "bdsg":          "check_bdsg",
        "nis2":          "check_nis2",
        "eu_ai_act":     "check_eu_ai_act",
        "hinschg":       "check_hinschg",
        "lksg":          "check_lksg",
        "enefg":         "check_enefg",
        "csrd":          "check_csrd",
        "workplace_law": "check_workplace_law",
        "agg":           "check_agg",
        "milog":         "check_milog",
        "ttdsg":         "check_ttdsg",
        "gwg":           "check_gwg",
        "eu_data_act":   "check_eu_data_act",
    }

    def check_one(self, regulation: str, profile: CompanyProfile) -> ApplicabilityResult:
        """Run a single regulation check by key."""
        method_name = self._CHECKS.get(regulation)
        if not method_name:
            raise ValueError(f"Unknown regulation key: {regulation!r}. Valid keys: {list(self._CHECKS)}")
        return getattr(self, method_name)(profile)

    def check_all(self, profile: CompanyProfile) -> dict[str, ApplicabilityResult]:
        """
        Run all regulation checks.

        Returns a dict keyed by regulation string (matching Regulation enum values),
        e.g. {"gdpr_dsgvo": ApplicabilityResult(...), ...}
        """
        results: dict[str, ApplicabilityResult] = {}
        for reg_key, method_name in self._CHECKS.items():
            try:
                results[reg_key] = getattr(self, method_name)(profile)
            except Exception as exc:
                logger.error("RuleEngine.check_all: error checking %s: %s", reg_key, exc)
                results[reg_key] = ApplicabilityResult(
                    regulation=reg_key,
                    applies=False,
                    confidence="LOW",
                    reason=f"Rule engine error: {exc}",
                    required_fields=[],
                    missing_fields=[],
                )
        return results

    def get_all_missing_fields(self, profile: CompanyProfile) -> dict[str, list[str]]:
        """
        Return a dict of {regulation_key: [missing_field, ...]} for all applicable regulations.
        Only includes regulations that apply AND have missing required fields.
        """
        results = self.check_all(profile)
        return {
            reg_key: result.missing_fields
            for reg_key, result in results.items()
            if result.applies and result.missing_fields
        }
