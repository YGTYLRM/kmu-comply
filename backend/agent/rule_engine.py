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
                reasons.append("verarbeitet personenbezogene Daten (Art. 2 DSGVO)")
            if profile.has_website:
                reasons.append("betreibt eine Website (implizite Verarbeitung personenbezogener Daten)")
            if profile.employee_count >= 1:
                reasons.append(f"beschäftigt {profile.employee_count} Mitarbeiter (Verarbeitung von Arbeitnehmerdaten)")
            reason = "DSGVO gilt: " + "; ".join(reasons) + "."
        else:
            reason = "DSGVO gilt nicht: Unternehmen verarbeitet keine personenbezogenen Daten und hat keine Website oder Mitarbeiter."

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
            reason = "BDSG gilt: Deutsches Unternehmen verarbeitet personenbezogene Daten (BDSG §1)."
        elif profile.country != "DE":
            reason = "BDSG gilt nicht: Unternehmen ist nicht in Deutschland ansässig."
        else:
            reason = "BDSG gilt nicht: Unternehmen verarbeitet keine personenbezogenen Daten."

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
                f"NIS2 (BSIG) gilt als {entity_type}: "
                f"{profile.employee_count} Mitarbeiter in kritischem/wichtigem Sektor '{profile.industry}'."
            )
        elif not in_scope_sector:
            reason = f"NIS2 gilt nicht: Branche '{profile.industry}' ist kein kritischer oder wichtiger NIS2-Sektor."
        else:
            reason = (
                f"NIS2 gilt nicht: Schwellenwerte unterschritten "
                f"({profile.employee_count} Mitarbeiter < 50 Minimum)."
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
            "EU AI Act gilt: Unternehmen entwickelt oder betreibt KI-Systeme (Art. 2)."
            if applies
            else "EU AI Act gilt nicht: Unternehmen entwickelt oder betreibt keine KI-Systeme."
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
            f"HinSchG gilt: {profile.employee_count} Mitarbeiter >= 50 - "
            f"interner Hinweisgeberkanal vorgeschrieben (§12 HinSchG)."
            if applies
            else f"HinSchG gilt nicht: {profile.employee_count} Mitarbeiter < Schwellenwert 50 (§12 HinSchG)."
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
            f"LkSG gilt: {profile.employee_count} Mitarbeiter >= 1.000 Schwellenwert (§1 Abs. 1 LkSG, ab 1. Jan. 2024)."
            if applies
            else f"LkSG gilt nicht: {profile.employee_count} Mitarbeiter < 1.000 Schwellenwert (§1 Abs. 1 LkSG)."
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
                parts.append(f"{profile.employee_count} Mitarbeiter >= 250 (kein KMU) → EDL-G §8 Energieaudit")
            if high_energy:
                parts.append(f"Energieverbrauch {energy_gwh:.1f} GWh > 7,5 GWh → EnEfG §8 Abs. 1 Energiemanagementsystem")
            reason = f"EnEfG / EDL-G gelten: {'; '.join(parts)}."
        else:
            energy_note = (
                "Energieverbrauch nicht angegeben (bitte ergänzen zur Prüfung von EnEfG §8 Abs. 1)"
                if not energy_known
                else f"Energieverbrauch {energy_gwh:.1f} GWh <= 7,5 GWh"
            )
            reason = (
                f"EnEfG / EDL-G gelten nicht: {profile.employee_count} Mitarbeiter < 250 (gilt als KMU); "
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
            omnibus_note = " Hinweis: Omnibus-Vereinfachung (>1.000 Mitarbeiter UND >450 Mio. Euro Umsatz) steht noch aus - aktuellen Anwendungsbereich prüfen."
            reason = (
                f"CSRD gilt: {criteria_met}/3 Größenkriterien erfüllt "
                f"(EU-Richtlinie 2022/2464, Art. 5).{omnibus_note}"
            )
        else:
            reason = (
                f"CSRD gilt nicht: nur {criteria_met}/3 Größenkriterien erfüllt "
                f"(2 von 3 erforderlich: >250 Mitarbeiter, >50 Mio. Euro Umsatz, >25 Mio. Euro Bilanzsumme)."
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
            f"ArbSchG gilt für alle Arbeitgeber: {profile.employee_count} Mitarbeiter "
            f"(ArbSchG §1 - gilt für alle Arbeitgeber in Deutschland unabhängig von der Größe)."
            if applies
            else "ArbSchG gilt nicht: keine Mitarbeiter angegeben."
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
            f"AGG gilt für alle Arbeitgeber: {profile.employee_count} Mitarbeiter. "
            f"Antidiskriminierungsmaßnahmen (§12 AGG) und Beschwerdestellenverfahren (§13 AGG) vorgeschrieben."
            if applies
            else "AGG gilt nicht: keine Mitarbeiter angegeben."
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
            f"MiLoG gilt für alle Arbeitgeber: {profile.employee_count} Mitarbeiter. "
            f"Gesetzlicher Mindestlohn (12,82 Euro/Stunde, 2025) und Arbeitszeitaufzeichnungen (§17 MiLoG) vorgeschrieben."
            if applies
            else "MiLoG gilt nicht: keine Mitarbeiter angegeben."
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
            "TTDSG (§25 TDDDG) gilt: Unternehmen betreibt eine Website. "
            "Einwilligung erforderlich vor dem Setzen nicht notwendiger Cookies oder Tracking-Maßnahmen."
            if applies
            else "TTDSG gilt nicht: Unternehmen hat keine öffentliche Website oder App."
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
                f"Branche '{profile.industry}' ist ein GwG-pflichtiger Sektor"
                if in_gwg_sector
                else "Unternehmen hat sich als geldwäscherechtlich verpflichtet erklärt"
            )
            reason = f"GwG gilt: {trigger} (§2 GwG). Risikoanalyse, Kundensorgfaltspflichten und Geldwäschebeauftragter vorgeschrieben."
        else:
            reason = (
                f"GwG gilt nicht: Branche '{profile.industry}' ist kein geldwäscherechtlich verpflichteter Sektor. "
                f"Feld 'geldwäschepflichtig' aktivieren, falls das Unternehmen Finanz-, Krypto-, Rechts- oder Glücksspieldienstleistungen erbringt."
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
                parts.append("stellt vernetzte (IoT) Produkte her (Art. 3-4)")
            if profile.provides_data_processing_services:
                parts.append("erbringt Cloud-/Datenverarbeitungsdienste (Art. 23-25)")
            reason = f"EU Data Act gilt: {'; '.join(parts)}."
        else:
            reason = (
                "EU Data Act gilt nicht: Unternehmen stellt keine vernetzten Produkte her "
                "und erbringt keine Datenverarbeitungsdienste."
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
                    reason=f"Regelmotor-Fehler: {exc}",
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
