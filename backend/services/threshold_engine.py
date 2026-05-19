"""
Deterministic regulation applicability engine.

All threshold logic is hardcoded here. Never delegate these decisions to an LLM.
Thresholds are sourced from the regulatory texts cited in each function's docstring.
"""

from dataclasses import dataclass
from datetime import date
from models.company_profile import CompanyProfile
from models.compliance_report import RegulationApplicability
from models.enums import Regulation


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GDPRResult:
    applies: bool
    dpo_required: bool
    processing_records_required: bool
    reason: str
    dpo_reason: str
    records_reason: str


@dataclass(frozen=True)
class LkSGResult:
    applies: bool
    reason: str


@dataclass(frozen=True)
class EnEfGResult:
    applies: bool
    edl_g_audit_required: bool
    energy_management_required: bool
    waste_heat_reporting_required: bool
    reason: str


@dataclass(frozen=True)
class CSRDResult:
    applies: bool
    criteria_met: int
    wave: int | None   # 1 = PIE >500 employees; 2 = large not-Wave-1; 3 = listed SME; None = N/A
    first_reporting_fy: int | None  # first fiscal year with reporting obligation
    reason: str


@dataclass(frozen=True)
class BDSGResult:
    applies: bool
    dpo_required: bool
    reason: str


@dataclass(frozen=True)
class NIS2Result:
    applies: bool
    particularly_important: bool  # besonders wichtige Einrichtung (BSIG §28(6))
    important: bool               # wichtige Einrichtung (BSIG §28(7))
    reason: str


@dataclass(frozen=True)
class AIActResult:
    applies: bool
    high_risk_obligations_active: bool
    gpai_rules_active: bool
    reason: str


@dataclass(frozen=True)
class HinSchGResult:
    applies: bool
    reason: str


@dataclass(frozen=True)
class ArbSchGResult:
    applies: bool
    reason: str


@dataclass(frozen=True)
class AGGResult:
    applies: bool
    reason: str


@dataclass(frozen=True)
class MiLoGResult:
    applies: bool
    reason: str


@dataclass(frozen=True)
class TTDSGResult:
    applies: bool
    reason: str


@dataclass(frozen=True)
class GwGResult:
    applies: bool
    reason: str


@dataclass(frozen=True)
class EUDataActResult:
    applies: bool
    reason: str


# ── Existing regulations ───────────────────────────────────────────────────────

def check_gdpr(profile: CompanyProfile) -> GDPRResult:
    """
    SOURCE: Regulation (EU) 2016/679 (GDPR)

    Applicability — Art. 2(1) GDPR:
      "This Regulation applies to the processing of personal data wholly or partly
       by automated means and to the processing other than by automated means of
       personal data which form part of a filing system or are intended to form
       part of a filing system."
      → Applies to any company processing personal data of EU residents.

    DPO (Data Protection Officer) — BDSG §38(1) [verified from gesetze-im-internet.de]:
      "Nichtöffentliche Stellen benennen eine Datenschutzbeauftragte oder einen
       Datenschutzbeauftragten, soweit sie in der Regel mindestens 20 Personen
       ständig mit der automatisierten Verarbeitung personenbezogener Daten
       beschäftigen."
      → Threshold: ≥20 PERSONS CONSTANTLY engaged in AUTOMATED processing.
      IMPORTANT: This is not simply ≥20 employees. A 30-person company where
      only 3 staff regularly use a CRM/ERP system may not meet this threshold.
      A 25-person SaaS company where all staff process customer data does.
      We approximate this as ≥20 employees + non-occasional processing; this
      is conservative and correct for most digital/service businesses but may
      OVERSTATE the DPO obligation for manual-processing-heavy industries.
      ⚠ LEGAL REVIEW RECOMMENDED for borderline cases.

    Processing records — Art. 30(5) GDPR:
      "The obligations referred to in paragraphs 1 and 2 shall not apply to an
       enterprise or an organisation employing fewer than 250 persons unless the
       processing it carries out is likely to result in a risk to the rights and
       freedoms of data subjects, the processing is not occasional, or the
       processing includes special categories of data as referred to in Article 9(1)."
      → Exemption: <250 employees AND occasional processing AND no special categories.
      → Required if: ≥250 employees OR non-occasional OR special categories (Art. 9).
    """
    applies = profile.processes_personal_data

    if not applies:
        return GDPRResult(
            applies=False,
            dpo_required=False,
            processing_records_required=False,
            reason="Company does not process personal data — GDPR does not apply.",
            dpo_reason="N/A",
            records_reason="N/A",
        )

    # BDSG §38(1): ≥20 persons CONSTANTLY engaged in AUTOMATED processing.
    # Approximated as ≥20 employees + non-occasional; conservative for digital businesses.
    dpo_required = (
        profile.employee_count >= 20
        and not profile.processing_is_occasional
    )
    # Flag borderline cases where the heuristic may overstate the obligation
    _MANUAL_HEAVY_INDUSTRIES = {"manufacturing", "construction", "food_beverage", "logistics", "energy", "waste"}
    dpo_borderline = (
        dpo_required
        and 20 <= profile.employee_count <= 50
        and profile.industry in _MANUAL_HEAVY_INDUSTRIES
    )
    dpo_reason = (
        f"DPO likely required: {profile.employee_count} employees regularly processing "
        f"personal data automatically (BDSG §38(1) — ≥20 persons constantly in automated "
        f"processing). Note: exact applicability depends on how many staff are constantly "
        f"engaged in automated processing, not just total headcount."
        + (" ⚠ BORDERLINE: in manual-processing-heavy industries, fewer than 20 staff "
           "may actually be constantly engaged in automated processing — verify with counsel."
           if dpo_borderline else "")
        if dpo_required
        else (
            f"DPO not required: {profile.employee_count} employees < 20 threshold or "
            f"processing is occasional (BDSG §38(1))."
        )
    )

    records_required = (
        profile.employee_count >= 250
        or not profile.processing_is_occasional
        or profile.processes_special_category_data
    )
    records_parts = []
    if profile.employee_count >= 250:
        records_parts.append(f"employee count {profile.employee_count} >= 250 (Art. 30(5) GDPR)")
    if not profile.processing_is_occasional:
        records_parts.append("processing is not occasional (Art. 30(5) GDPR)")
    if profile.processes_special_category_data:
        records_parts.append("processes special category data (Art. 30(5) GDPR)")

    records_reason = (
        "Processing records required: " + "; ".join(records_parts) + "."
        if records_required
        else "Processing records not strictly required (Art. 30(5) GDPR exemption for SMEs with <250 employees and occasional processing)."
    )

    return GDPRResult(
        applies=True,
        dpo_required=dpo_required,
        processing_records_required=records_required,
        reason="Company processes personal data — GDPR applies (Art. 2 GDPR).",
        dpo_reason=dpo_reason,
        records_reason=records_reason,
    )


def check_lksg(profile: CompanyProfile) -> LkSGResult:
    """
    SOURCE: Gesetz über die unternehmerischen Sorgfaltspflichten zur Vermeidung von
    Menschenrechtsverletzungen in Lieferketten (LkSG) — gesetze-im-internet.de/lksg/

    Applicability — §1(1) LkSG [verified from official text]:
      "Dieses Gesetz ist anzuwenden auf Unternehmen ungeachtet ihrer Rechtsform, die
       1. ihre Hauptverwaltung, ihre Hauptniederlassung, ihren Verwaltungssitz oder
          ihren satzungsmäßigen Sitz im Inland haben und
       2. in der Regel mindestens 3.000 Arbeitnehmer im Inland beschäftigen."
      "Ab dem 1. Januar 2024 betragen die [...] Schwellenwerte jeweils 1.000 Arbeitnehmer."
      → From 1 January 2024: threshold is ≥1,000 employees.

    Leiharbeitnehmer — §1(2) LkSG [verified from official text]:
      "Leiharbeitnehmer sind bei der Berechnung der Arbeitnehmerzahl des
       Entleihunternehmens zu berücksichtigen, wenn die Einsatzdauer sechs Monate
       übersteigt."
      → Temporary workers (Leiharbeitnehmer) with >6 months tenure COUNT toward
        the 1,000-employee threshold for the company using them (Entleiher).
      ⚠ We cannot capture this without a specific field. Employee count provided
        by the user should include long-term temp workers.

    Group companies — §1(3) LkSG [verified from official text]:
      "Innerhalb von verbundenen Unternehmen (§15 AktG) sind die im Inland
       beschäftigten Arbeitnehmer sämtlicher konzernangehriger Gesellschaften
       bei der Berechnung der Arbeitnehmerzahl der Obergesellschaft zu
       berücksichtigen."
      → For group companies (Konzern), ALL domestic employees of all group
        entities count toward the PARENT company's threshold.
      ⚠ We cannot automatically detect group structures. If this company is
        a parent or subsidiary, the displayed employee count may be understated.

    Supply chain location is NOT an applicability trigger — LkSG covers both
    the company's own operations and its supply chain regardless of supplier location.

    Source: §1(1), §1(2), §1(3) LkSG; BAFA Guidance 2023.
    """
    directly_applies = profile.employee_count >= 1000

    if directly_applies:
        reason = (
            f"LkSG applies directly: {profile.employee_count} employees >= 1,000 threshold "
            f"(§1(1) LkSG, effective 1 Jan 2024). Due diligence obligations cover own business "
            f"area and supply chain. Policy statement (§6), risk analysis (§5), and complaints "
            f"mechanism (§8) are mandatory."
        )
    else:
        indirect_note = (
            " Note: if your company supplies to LkSG-obligated customers (>=1,000 employees), "
            "you may receive supplier due diligence questionnaires and contractual obligations "
            "even without direct LkSG applicability."
            if profile.has_supply_chain_abroad or profile.employee_count >= 500
            else ""
        )
        reason = (
            f"LkSG does not apply directly: {profile.employee_count} employees < 1,000 threshold "
            f"(§1(1) LkSG).{indirect_note}"
        )

    return LkSGResult(applies=directly_applies, reason=reason)


def check_enefg(profile: CompanyProfile) -> EnEfGResult:
    """
    SOURCE: Energieeffizienzgesetz (EnEfG) + Energiedienstleistungsgesetz (EDL-G)
    gesetze-im-internet.de/enefg/ and gesetze-im-internet.de/edl-g/

    TWO SEPARATE LEGAL TRACKS — do not conflate:

    TRACK 1 — EDL-G §8: Energy audit (Energieaudit):
      Applies to: non-SME enterprises (EU Recommendation 2003/361/EC Art. 2).
      A company is non-SME if it exceeds ANY ONE of:
        ≥250 employees, OR >€50M annual turnover, OR >€43M balance sheet total.
      Obligation: energy audit every 4 years (DIN EN 16247-1).
      A certified EnMS (ISO 50001 or EMAS) satisfies this obligation.

    TRACK 2 — EnEfG §8(1): Energy or environmental management system:
      [Verified from official text — gesetze-im-internet.de/enefg/__8.html]:
      "Unternehmen mit einem jährlichen durchschnittlichen Gesamtendenergieverbrauch
       innerhalb der letzten drei abgeschlossenen Kalenderjahre von mehr als
       7,5 Gigawattstunden sind verpflichtet, ein Energie- oder
       Umweltmanagementsystem gemäß Absatz 2 Satz 1 oder Satz 2 einzurichten."
      → Applies to ANY company (SME or not) with >7.5 GWh AVERAGE consumption
        over the last 3 completed calendar years.
      ⚠ PREVIOUS CODE ERROR: this was incorrectly gated on non-SME status.
        An SME with >7.5 GWh annual energy consumption IS subject to §8(1).
      ⚠ THRESHOLD IS A 3-YEAR AVERAGE, not a single year's consumption.

    TRACK 2 — EnEfG §9: Energy-saving implementation plans:
      Required for companies subject to §8(1) (>7.5 GWh).

    Waste heat — EnEfG §15 (now §16 after 2024 renumbering):
      Non-SME companies with technically usable waste heat ≥200 kW must assess,
      document, and report waste heat potential.

    Source: EDL-G §8; EnEfG §8(1), §9, §16; EU Recommendation 2003/361/EC Art. 2;
            BAFA Guidance on EnEfG 2023.
    """
    exceeds_employees = profile.employee_count >= 250
    exceeds_revenue   = (profile.annual_revenue_eur is not None
                         and profile.annual_revenue_eur > 50_000_000)
    exceeds_balance   = (profile.balance_sheet_total_eur is not None
                         and profile.balance_sheet_total_eur > 43_000_000)

    is_non_sme = exceeds_employees or exceeds_revenue or exceeds_balance

    energy_mwh = profile.annual_energy_consumption_mwh or 0
    energy_gwh = energy_mwh / 1000

    # TRACK 2: EnEfG §8(1) — applies to ANY company >7.5 GWh (3-year average)
    # regardless of SME status. Previous code incorrectly gated this on non-SME.
    enms_required = energy_gwh > 7.5

    # TRACK 1: EDL-G §8 audit — applies only to non-SME companies
    edl_g_audit_required = is_non_sme

    applies = is_non_sme or enms_required

    if not applies:
        unmet = []
        if not exceeds_employees:
            unmet.append(f"{profile.employee_count} employees < 250")
        if not exceeds_revenue:
            unmet.append(
                "revenue not provided" if profile.annual_revenue_eur is None
                else f"revenue {profile.annual_revenue_eur:,.0f} EUR ≤ 50M"
            )
        if not exceeds_balance:
            unmet.append(
                "balance sheet not provided" if profile.balance_sheet_total_eur is None
                else f"balance sheet {profile.balance_sheet_total_eur:,.0f} EUR ≤ 43M"
            )
        energy_note = (
            "annual energy consumption not provided — provide it to check EnEfG §8(1)"
            if energy_mwh == 0
            else f"energy consumption {energy_gwh:.1f} GWh ≤ 7.5 GWh threshold"
        )
        return EnEfGResult(
            applies=False,
            edl_g_audit_required=False,
            energy_management_required=False,
            waste_heat_reporting_required=False,
            reason=(
                f"EnEfG / EDL-G do not apply — qualifies as EU SME ({'; '.join(unmet)}) "
                f"and {energy_note} (EnEfG §8(1))."
            ),
        )

    obligations = []
    criteria = []

    if is_non_sme:
        if exceeds_employees:
            criteria.append(f"{profile.employee_count} employees ≥ 250")
        if exceeds_revenue:
            criteria.append(f"revenue {profile.annual_revenue_eur:,.0f} EUR > 50M")
        if exceeds_balance:
            criteria.append(f"balance sheet {profile.balance_sheet_total_eur:,.0f} EUR > 43M")
        obligations.append(f"non-SME ({'; '.join(criteria)}) → EDL-G §8 energy audit every 4 years")

    if energy_mwh == 0:
        obligations.append(
            "annual energy consumption not provided — cannot confirm EnEfG §8(1) status; "
            "provide 3-year average consumption in GWh"
        )
    elif enms_required:
        obligations.append(
            f"energy consumption {energy_gwh:.1f} GWh > 7.5 GWh (3-year average) → "
            f"certified energy management system (ISO 50001 or EMAS) mandatory (EnEfG §8(1)); "
            f"energy-saving implementation plans required (EnEfG §9)"
        )

    reason = (
        f"EnEfG / EDL-G apply. Obligations: {'; '.join(obligations)}. "
        f"Waste heat assessment required if technically usable waste heat ≥ 200 kW (EnEfG §16)."
    )

    return EnEfGResult(
        applies=True,
        edl_g_audit_required=edl_g_audit_required,
        energy_management_required=enms_required,
        waste_heat_reporting_required=is_non_sme,
        reason=reason,
    )


def check_csrd(profile: CompanyProfile) -> CSRDResult:
    """
    SOURCE: Directive (EU) 2022/2464 (CSRD) — eur-lex.europa.eu/eli/dir/2022/2464

    ⚠ THRESHOLD UNCERTAINTY — LEGAL REVIEW REQUIRED:
    The CSRD scope is actively changing due to the "Omnibus" simplification package.

    ORIGINAL CSRD THRESHOLDS (Directive 2022/2464, amending Art. 3(4) of 2013/34/EU):
      A "large undertaking" meets 2 of 3 criteria:
        > 250 employees, OR > €50M net turnover, OR > €25M balance sheet total.
      [Source: Art. 3(4) Directive 2013/34/EU as amended]

    OMNIBUS SIMPLIFICATION (Council agreement February 2026 — consilium.europa.eu):
      The Council agreed to narrow CSRD scope to companies with:
        > 1,000 employees AND > €450M net annual turnover.
      ⚠ STATUS: As of May 2026, the Omnibus formal adoption and transposition
        status is uncertain. We continue to use the original 2/3 criteria as
        the conservative (broader) baseline. This will OVERSTATE CSRD applicability
        for companies between the two thresholds.
      ⚠ ACTION: This threshold MUST be updated once the Omnibus directive is
        formally published in the EU Official Journal and transposed into German law.

    APPLICATION TIMELINE (per Directive (EU) 2025/794 "Stop-the-clock"):
      Wave 1 (FY 2024, report 2025): PIEs with >500 employees — NOT postponed.
      Wave 2 (postponed to FY 2027, report 2028): Large companies not in Wave 1.
      Wave 3 (postponed to FY 2028, report 2029): Listed SMEs.
      [Source: Directive (EU) 2025/794, April 2025]
    """
    criteria_met = 0
    met_list = []

    if profile.employee_count > 250:
        criteria_met += 1
        met_list.append(f"employees {profile.employee_count} > 250")
    if profile.annual_revenue_eur is not None and profile.annual_revenue_eur > 50_000_000:
        criteria_met += 1
        met_list.append(f"revenue {profile.annual_revenue_eur:,.0f} EUR > 50M")
    if profile.balance_sheet_total_eur is not None and profile.balance_sheet_total_eur > 25_000_000:
        criteria_met += 1
        met_list.append(f"balance sheet {profile.balance_sheet_total_eur:,.0f} EUR > 25M")

    is_large = criteria_met >= 2
    applies  = is_large or profile.is_listed_company

    # Wave assignment per Directive (EU) 2025/794 stop-the-clock
    # Wave 1: PIEs already subject to NFRD with >500 employees — FY2024, report 2025 (not postponed)
    # Wave 2: Large companies (2/3 criteria) not in Wave 1 — postponed FY2027, report 2028
    # Wave 3: Listed SMEs on EU-regulated markets — postponed FY2028, report 2029
    is_pie_above_500 = profile.employee_count > 500 and profile.is_listed_company
    wave: int | None = None
    first_fy: int | None = None

    if not applies:
        wave, first_fy = None, None
        unmet_count = 3 - criteria_met
        reason = (
            f"CSRD does not apply: only {criteria_met}/3 size criteria met"
            + (f" ({'; '.join(met_list)})" if met_list else "")
            + f" — 2/3 required. {unmet_count} criteria not met "
            + "(EU Directive 2022/2464, Art. 5)."
        )
    elif is_pie_above_500:
        wave, first_fy = 1, 2024
        reason = (
            "CSRD applies as Wave 1 (PIE with >500 employees): first reporting FY 2024 "
            "(report published 2025). Not postponed by Directive (EU) 2025/794."
        )
    elif is_large:
        wave, first_fy = 2, 2027
        # Add Omnibus caveat for companies that meet the original 2/3 criteria but fall below
        # the proposed Omnibus thresholds (>1,000 emp AND >€450M). These companies are
        # overcounted by the current threshold until formal Omnibus adoption.
        _below_omnibus = (
            profile.employee_count <= 1000
            or profile.annual_revenue_eur is None
            or profile.annual_revenue_eur <= 450_000_000
        )
        _omnibus_note = (
            " ⚠ OMNIBUS CAVEAT: The EU Omnibus package (Council agreement Feb 2026) proposes "
            "narrowing CSRD scope to >1,000 employees AND >€450M net turnover. Formal EU adoption "
            "and German transposition are pending as of May 2026. This company meets the original "
            "2/3 criteria but does NOT meet the proposed Omnibus thresholds — it may fall outside "
            "CSRD scope once adopted. Verify current status with legal counsel before starting "
            "any CSRD reporting programme."
            if _below_omnibus else ""
        )
        reason = (
            f"CSRD applies as Wave 2: {criteria_met}/3 size criteria met ({'; '.join(met_list)}) "
            f"(EU Directive 2022/2464, Art. 5). First reporting year: FY 2027 (report 2028) "
            f"per Directive (EU) 2025/794 stop-the-clock.{_omnibus_note}"
        )
    else:
        wave, first_fy = 3, 2028
        reason = (
            "CSRD applies as Wave 3 (listed SME on EU-regulated market). "
            "First reporting year postponed to FY 2028 (report 2029) "
            "under Directive (EU) 2025/794."
        )

    return CSRDResult(applies=applies, criteria_met=criteria_met, wave=wave, first_reporting_fy=first_fy, reason=reason)


def check_bdsg(profile: CompanyProfile) -> BDSGResult:
    """
    SOURCE: Bundesdatenschutzgesetz (BDSG) — gesetze-im-internet.de/bdsg_2018/

    Applicability — BDSG §1(1):
      BDSG supplements GDPR for companies in Germany. Cannot apply without GDPR.
      Applies to any non-public body (nichtöffentliche Stelle) in Germany that
      processes personal data.

    DPO threshold — BDSG §38(1) [verified from gesetze-im-internet.de/bdsg_2018/__38.html]:
      "Nichtöffentliche Stellen benennen eine Datenschutzbeauftragte oder einen
       Datenschutzbeauftragten, soweit sie in der Regel mindestens 20 Personen
       ständig mit der automatisierten Verarbeitung personenbezogener Daten
       beschäftigen."
      → ≥20 persons CONSTANTLY engaged in AUTOMATED processing of personal data.
      ⚠ This is stricter than "20 employees total." A construction firm with 25
        employees where only 2 admin staff use digital systems may not meet this.
        We approximate as ≥20 employees + non-occasional processing (conservative).
    """
    applies = profile.country == "DE" and profile.processes_personal_data
    if not applies:
        return BDSGResult(
            applies=False,
            dpo_required=False,
            reason=(
                "BDSG does not apply: company is not in Germany."
                if profile.country != "DE"
                else "BDSG does not apply: company does not process personal data."
            ),
        )

    dpo_required = profile.employee_count >= 20 and not profile.processing_is_occasional
    return BDSGResult(
        applies=True,
        dpo_required=dpo_required,
        reason=(
            "BDSG applies: German company processing personal data (BDSG §1). "
            + (
                f"DPO required: {profile.employee_count} employees >= 20 threshold (BDSG §38(1))."
                if dpo_required
                else f"DPO not required: {profile.employee_count} employees < 20 or processing is occasional (BDSG §38(1))."
            )
        ),
    )


# ── New Tier 1 regulations ─────────────────────────────────────────────────────

# BSIG Annex I — besonders kritische Sektoren (highly critical, §28(6) BSIG)
# Mirrors NIS2 Annex I categories translated to Complio industry strings
_NIS2_ANNEX_I = {
    "energy",        # Energie (electricity, gas, oil, hydrogen)
    "transport",     # Verkehr (air, rail, water, road)
    "finance",       # Bankwesen + Finanzmarktinfrastrukturen
    "healthcare",    # Gesundheit (hospitals, labs, pharma, medical devices)
    "water",         # Trinkwasser + Abwasser
    "digital",       # Digitale Infrastruktur (DNS, IXPs, cloud, datacenters, CDN)
    "it_software",   # IKT-Dienstleistungsmanagement (managed services, security)
    "space",         # Raumfahrt
    "government",    # Öffentliche Verwaltung (central/regional)
}

# BSIG Annex II — wichtige Sektoren (important, §28(7) BSIG)
_NIS2_ANNEX_II = {
    "manufacturing",   # Verarbeitendes Gewerbe (medical devices, electronics, machinery, vehicles)
    "chemicals",       # Chemische Industrie
    "food_beverage",   # Lebensmittel (production and distribution)
    "logistics",       # Post- und Kurierdienste
    "waste",           # Abfallwirtschaft
    "construction",    # Digitale Anbieter (online marketplaces, search engines, platforms)
    "research",        # Forschung (research organisations)
}

# Combined set for initial sector check
_NIS2_CRITICAL_INDUSTRIES = _NIS2_ANNEX_I | _NIS2_ANNEX_II

# Industries that are definitively NOT in NIS2 scope (to support CANNOT_ASSESS path)
_NIS2_OUT_OF_SCOPE = {
    "retail",      # Einzelhandel — not listed in Annex I or II
    "consulting",  # Unternehmensberatung — not listed unless providing IT/security services
    "other",       # Unknown — cannot determine
}


def check_nis2(profile: CompanyProfile) -> NIS2Result:
    """
    SOURCE: Directive (EU) 2022/2555 (NIS2) — eur-lex.europa.eu/eli/dir/2022/2555
    Implemented in Germany via BSIG (NIS2UmsuCG — Umsetzungsgesetz NIS2).

    Applicability — NIS2 Art. 3 [verified from official text]:
      "Essential entities are entities of a type referred to in Annex I that exceed
       the ceilings for medium-sized enterprises within the meaning of Article 2(1)
       of the Annex to Recommendation 2003/361/EC."
      "Important entities are entities of a type referred to in Annex I or II that
       do not qualify as essential entities."

    EU medium enterprise ceiling (Recommendation 2003/361/EC Art. 2(1)):
      Medium: ≥50 employees OR ≥€10M turnover.
      Large (above medium ceiling): ≥250 employees OR ≥€50M turnover.

    German BSIG implementation thresholds (BSIG §28(6)+(7)):
      besonders wichtige Einrichtung (essential): Annex I sector + large (≥250/≥€50M)
        OR designated KRITIS operator regardless of size.
      wichtige Einrichtung (important): Annex I or II sector + medium (≥50/≥€10M)
        but not meeting the essential threshold.

    Incident reporting — NIS2 Art. 23 [verified from official text]:
      ⚠ NIS2 has TWO reporting steps — NOT a single deadline:
        1. Early warning: within 24 hours of becoming aware of a significant incident.
        2. Incident notification: within 72 hours, with initial assessment of severity.
        3. Final report: within 1 month, with full details.
      ⚠ PREVIOUS ERROR in product documentation: described this as "changed from
        72 to 24 hours" — this is WRONG. Both deadlines exist simultaneously.

    Source: NIS2 Art. 2, 3, 23; BSIG §28(6), §28(7); BSI sector guidance.
    """
    in_annex_i   = profile.is_critical_infrastructure_sector or profile.industry in _NIS2_ANNEX_I
    in_annex_ii  = profile.industry in _NIS2_ANNEX_II
    in_any_scope = in_annex_i or in_annex_ii
    ambiguous    = profile.industry not in _NIS2_CRITICAL_INDUSTRIES and profile.industry not in _NIS2_OUT_OF_SCOPE

    if ambiguous and not profile.is_critical_infrastructure_sector:
        return NIS2Result(
            applies=False, particularly_important=False, important=False,
            reason=(
                f"NIS2 sector classification cannot be determined for industry '{profile.industry}'. "
                f"NIS2 / BSIG applies to 18 specific sector categories (Annex I and II). "
                f"Consult BSI sector guidance to confirm whether your company falls under "
                f"§28(6) or §28(7) BSIG. Set 'is_critical_infrastructure_sector=true' if "
                f"your company has been designated as a KRITIS operator."
            ),
        )

    if not in_any_scope:
        return NIS2Result(
            applies=False, particularly_important=False, important=False,
            reason=(
                f"NIS2 does not apply: industry '{profile.industry}' is not in a critical "
                f"or important sector under NIS2 Annex I or II / BSIG, and no KRITIS designation set."
            ),
        )

    is_large = (
        profile.employee_count >= 250
        or (profile.annual_revenue_eur is not None and profile.annual_revenue_eur >= 50_000_000)
    )
    is_medium = (
        profile.employee_count >= 50
        or (profile.annual_revenue_eur is not None and profile.annual_revenue_eur >= 10_000_000)
    )

    # besonders wichtige Einrichtung: Annex I sector + large, OR KRITIS operator
    is_particularly_important = (in_annex_i and is_large) or profile.is_critical_infrastructure_sector
    # wichtige Einrichtung: Annex I medium OR Annex II large/medium
    is_important_entity = (not is_particularly_important) and (
        (in_annex_i and is_medium) or (in_annex_ii and is_medium)
    )

    if is_particularly_important:
        kritis_note = (
            " Company is a designated KRITIS operator — besonders wichtige Einrichtung "
            "regardless of size thresholds."
            if profile.is_critical_infrastructure_sector and not is_large
            else ""
        )
        revenue_caveat = (
            " Note: revenue alone may not be sufficient for all sectors — "
            "some require balance sheet confirmation (sector-dependent per BSIG)."
            if profile.annual_revenue_eur is not None and not (profile.employee_count >= 250)
            else ""
        )
        return NIS2Result(
            applies=True, particularly_important=True, important=False,
            reason=(
                f"NIS2 (BSIG) applies as besonders wichtige Einrichtung: "
                f"{profile.employee_count} employees in critical/important sector.{kritis_note} "
                f"Full BSIG obligations apply (§28(6) BSIG / Art. 3(1) NIS2).{revenue_caveat}"
            ),
        )
    if is_important_entity:
        annex = "Annex I" if in_annex_i else "Annex II"
        return NIS2Result(
            applies=True, particularly_important=False, important=True,
            reason=(
                f"NIS2 (BSIG) applies as wichtige Einrichtung: "
                f"{profile.employee_count} employees in {annex} sector '{profile.industry}'. "
                f"Security and incident reporting obligations apply (§28(7) BSIG / Art. 3(2) NIS2)."
            ),
        )

    return NIS2Result(
        applies=False, particularly_important=False, important=False,
        reason=(
            "NIS2 does not apply: below size thresholds (< 50 employees, < 10M revenue) "
            "for the identified sector (NIS2 Art. 2(2)). Small enterprises generally exempt."
        ),
    )


def check_ai_act(profile: CompanyProfile) -> AIActResult:
    """
    SOURCE: Regulation (EU) 2024/1689 (EU AI Act)
    eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202401689

    Applicability — Art. 2(1) EU AI Act:
      "This Regulation applies to [...] providers that place on the market or
       put into service AI systems or place on the market general-purpose AI models
       in the Union, irrespective of whether those providers are established or
       located within the Union or in a third country."
      And to deployers: Art. 2(1)(b): "deployers of AI systems that are established
       or located within the Union."
      → Applies to any company that DEVELOPS (provider) or USES (deployer) AI systems
        in the EU. No size threshold.

    Application timeline — Art. 113 EU AI Act [verified]:
      2 Feb 2025: Prohibited AI practices (Art. 5) — IN FORCE.
      2 Aug 2025: GPAI model rules (Art. 51–56) — IN FORCE.
      2 Aug 2026: High-risk Annex I system obligations.
      2 Aug 2027: High-risk Annex III systems already on market before Aug 2026.
    Source: Art. 113 EU AI Act.

    Roles and obligations:
      Provider (Art. 3(3)): places an AI system on the market or into service under own name.
        — Full conformity obligations for high-risk systems: risk management (Art. 9),
          data governance (Art. 10), technical documentation (Art. 11), logging (Art. 12),
          transparency (Art. 13), human oversight (Art. 14), accuracy/robustness (Art. 15),
          quality management system (Art. 17), conformity assessment (Art. 43).
      Deployer (Art. 3(4)): uses an AI system developed by another party.
        — Obligations (Art. 26): use within intended purpose, human oversight measures,
          monitor operation, fundamental rights impact assessment for certain high-risk uses,
          inform employees when subject to AI-assisted decisions.
      Importer / Distributor: additional supply chain obligations.

    Risk classification:
      Unacceptable risk (Art. 5): prohibited outright (social scoring, real-time biometric, etc.)
      High risk (Art. 6 + Annex III): employment/HR decisions, creditworthiness, education,
        law enforcement, migration, critical infrastructure, safety components.
      Limited risk (Art. 50): transparency obligations only (chatbots, deepfakes).
      Minimal risk: no specific obligations.

    Source: Art. 2, 3, 5, 6, 9–17, 26, 50, 113 EU AI Act.
    """
    today = date.today()
    gpai_rules_active = today >= date(2025, 8, 2)
    # High-risk Annex I/III obligations: officially 2 Aug 2026 per Art. 113 EU AI Act.
    # Digital Omnibus proposal (provisional EU agreement, Reuters 2025) may delay
    # Annex III to 2 Dec 2027 — pending formal adoption. Treating as uncertain until
    # formal adoption is published in the Official Journal.
    high_risk_obligations_active = today >= date(2026, 8, 2)

    if not profile.uses_ai_systems:
        return AIActResult(
            applies=False,
            high_risk_obligations_active=high_risk_obligations_active,
            gpai_rules_active=gpai_rules_active,
            reason="EU AI Act does not apply: company does not develop or deploy AI systems.",
        )

    is_high_risk = profile.ai_systems_are_high_risk

    if is_high_risk:
        risk_note = (
            "AI systems are classified as high-risk (Annex III): full provider/deployer "
            "obligations apply including risk management (Art. 9), technical documentation "
            "(Art. 11), human oversight (Art. 14), and quality management system (Art. 17). "
            "Fundamental rights impact assessment required for deployers in public/HR contexts (Art. 26(9))."
        )
    elif is_high_risk is False:
        risk_note = (
            "AI systems are not classified as high-risk: transparency obligations apply "
            "where AI interacts with people (Art. 50). Verify classification against "
            "Annex III — employment decisions, creditworthiness, and safety components "
            "are always high-risk regardless of perceived impact."
        )
    else:
        risk_note = (
            "High-risk classification not confirmed. Verify against Annex III EU AI Act: "
            "AI used in employment/HR decisions, creditworthiness, education, law enforcement, "
            "or safety-critical systems is high-risk regardless of company size. "
            "Transparency obligations (Art. 50) apply in all cases where AI interacts with people."
        )

    active_now = ["Art. 5 prohibited AI practices (since 2 Feb 2025)"]
    if gpai_rules_active:
        active_now.append("GPAI rules Arts. 51-56 (since 2 Aug 2025)")

    coming = []
    if not gpai_rules_active:
        coming.append("GPAI rules Arts. 51-56 (2 Aug 2025)")
    if not high_risk_obligations_active:
        coming.append(
            "high-risk Annex I + III system obligations Arts. 9-17 — current law: 2 Aug 2026; "
            "NOTE: Digital Omnibus proposal (pending formal adoption) may delay Annex III to 2 Dec 2027. "
            "Treat as uncertain until published in the EU Official Journal."
        )
    coming.append("high-risk legacy Annex III obligations for systems already on market before Aug 2026 (2 Aug 2027)")

    timeline = (
        f"Active now: {'; '.join(active_now)}. "
        f"Coming: {'; '.join(coming)}."
    )

    return AIActResult(
        applies=True,
        high_risk_obligations_active=high_risk_obligations_active,
        gpai_rules_active=gpai_rules_active,
        reason=(
            f"EU AI Act applies: company develops or deploys AI systems (Art. 2). "
            f"{risk_note} {timeline}"
        ),
    )


def check_hinschg(profile: CompanyProfile) -> HinSchGResult:
    """
    SOURCE: Hinweisgeberschutzgesetz (HinSchG) — gesetze-im-internet.de/hinschg/

    Applicability — HinSchG §12(1) [verified from official text]:
      "Beschäftigungsstellen des privaten Sektors, die in der Regel 50 oder mehr
       Beschäftigte haben, sind verpflichtet, interne Meldestellen einzurichten
       und zu betreiben."
      → ≥50 employees → mandatory internal whistleblower reporting channel.

    Implementation deadlines — HinSchG §12(2)+(3) [verified from official text]:
      50–249 employees: obligation from 17 December 2023 (could use shared channel).
      ≥250 employees: obligation from 2 July 2023.

    Note: "Beschäftigte" includes employees, trainees, and workers posted abroad.
    """
    applies = profile.employee_count >= 50
    reason = (
        f"HinSchG applies: {profile.employee_count} employees >= 50 — "
        f"internal whistleblower reporting channel mandatory (§12(2) HinSchG). "
        f"Deadline: December 2023 (50-249 employees) or July 2023 (250+ employees)."
        if applies
        else f"HinSchG does not apply: {profile.employee_count} employees < 50 threshold (§12(2) HinSchG)."
    )
    return HinSchGResult(applies=applies, reason=reason)


def check_arbschg(profile: CompanyProfile) -> ArbSchGResult:
    """
    SOURCE: Arbeitsschutzgesetz (ArbSchG) — gesetze-im-internet.de/arbschg/

    Applicability — ArbSchG §1(1)+(2) [verified from official text]:
      "(1) Dieses Gesetz dient dazu, Sicherheit und Gesundheitsschutz der
       Beschäftigten bei der Arbeit durch Maßnahmen des Arbeitsschutzes zu
       sichern und zu verbessern. Es gilt in allen Tätigkeitsbereichen."
      "(2) Dieses Gesetz gilt für alle Arbeitgeber in Deutschland, unabhängig
       von der Anzahl der Beschäftigten."
      Exception (§1(2) last sentence): "Es gilt nicht für private Haushalte."
      → Applies to ALL employers in Germany with ≥1 employee, in all sectors.
      → Does NOT apply to private households employing domestic staff.

    Key obligations:
      §5: Gefährdungsbeurteilung (workplace risk assessment) — mandatory.
      §6: Documentation of risk assessment — mandatory.
      §10: First aid measures — mandatory.
      §12: Employee safety instruction — mandatory at onboarding and regularly.
    """
    applies = profile.employee_count >= 1
    reason = (
        f"ArbSchG applies to all employers: {profile.employee_count} employees "
        f"(ArbSchG §1(2) — 'gilt für alle Arbeitgeber in Deutschland, unabhängig "
        f"von der Anzahl der Beschäftigten'). "
        f"Risk assessment (§5), documentation (§6), and employee instruction (§12) are mandatory."
        if applies
        else "ArbSchG does not apply: no employees reported."
    )
    return ArbSchGResult(applies=applies, reason=reason)


def check_agg(profile: CompanyProfile) -> AGGResult:
    """
    SOURCE: Allgemeines Gleichbehandlungsgesetz (AGG) — gesetze-im-internet.de/agg/

    Applicability — AGG §6(2) [verified from official text]:
      "Arbeitgeber im Sinne dieses Gesetzes sind natürliche und juristische
       Personen sowie rechtsfähige Personengesellschaften, die Personen nach
       Absatz 1 beschäftigen. Werden Beschäftigte einem Dritten zur Arbeits-
       leistung überlassen, so gilt auch dieser als Arbeitgeber im Sinne
       dieses Abschnitts."
      → Applies to ALL employers (natural persons, legal entities, partnerships)
        with ≥1 employee. No size threshold.
      → Also applies to companies that USE leased workers (Leiharbeitnehmer) —
        they count as employer for AGG purposes too.

    Protected grounds (AGG §1): race, ethnic origin, gender, religion/belief,
      disability, age, sexual identity.

    Key obligations:
      §12: Preventive measures (training, policies) — mandatory for all employers.
      §13: Complaints procedure — mandatory for all employers.
    """
    applies = profile.employee_count >= 1
    reason = (
        f"AGG applies to all employers: {profile.employee_count} employees. "
        f"Employer must take active measures against discrimination on grounds of race, gender, "
        f"religion, disability, age, and sexual identity (§12 AGG). "
        f"Complaints procedure required (§13 AGG)."
        if applies
        else "AGG does not apply: no employees reported."
    )
    return AGGResult(applies=applies, reason=reason)


def check_milog(profile: CompanyProfile) -> MiLoGResult:
    """
    SOURCE: Mindestlohngesetz (MiLoG) — gesetze-im-internet.de/milog/

    Applicability — MiLoG §20 [verified from official text]:
      "Arbeitgeber mit Sitz im In- oder Ausland sind verpflichtet, ihren im
       Inland beschäftigten Arbeitnehmerinnen und Arbeitnehmern ein Arbeitsentgelt
       mindestens in Höhe des Mindestlohns nach §1 Absatz 2 spätestens zu dem in
       §2 Absatz 1 Satz 1 Nummer 2 genannten Zeitpunkt zu zahlen."
      → Applies to ALL employers (domestic or foreign) with employees working
        in Germany. No size threshold.

    Current minimum wage — MiLoG §1(2) + 4. MiLoGV (Mindestlohnverordnung):
      EUR 13.90/hour (effective 1 January 2026).
      EUR 14.60/hour (effective 1 January 2027) — announced by Mindestlohnkommission.
      ⚠ This changes periodically via Mindestlohnkommission recommendation.
        Verify current rate at: bmas.de or gesetze-im-internet.de/milog/__1.html

    Working time documentation — MiLoG §17(1):
      Required for employees earning ≤ EUR 2,000/month gross AND in covered sectors
      (§17(4) MiLoG lists exemptions for fully documented payroll systems).

    Subcontractor liability — MiLoG §13:
      Principal employers are jointly liable for minimum wage violations by
      subcontractors providing labour.
    """
    applies = profile.employee_count >= 1
    reason = (
        f"MiLoG applies to all employers: {profile.employee_count} employees. "
        f"Current statutory minimum wage is EUR 13.90/hour (§1 MiLoG, effective 1 January 2026; rises to EUR 14.60/hour from 1 January 2027). "
        f"Working time records required for employees earning < EUR 2,000/month (§17 MiLoG)."
        if applies
        else "MiLoG does not apply: no employees reported."
    )
    return MiLoGResult(applies=applies, reason=reason)


def check_ttdsg(profile: CompanyProfile) -> TTDSGResult:
    """
    TTDSG / TDDDG — Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz.

    §25 TTDSG (now §25 TDDDG) prohibits storing or accessing information on
    a user's terminal equipment (cookies, local storage, tracking pixels,
    fingerprinting) without prior informed consent, unless strictly necessary
    for the requested service.

    Applies to any operator of a website or app that is accessible by users
    in Germany and processes personal data through tracking technologies.
    There is no size threshold — a one-person company with a website is bound.

    Source: §25, §26 TTDSG (TDDDG); ePrivacy Directive 2002/58/EC Art. 5(3).
    """
    applies = profile.has_website and profile.processes_personal_data
    if not applies:
        if not profile.has_website:
            reason = "TTDSG does not apply: company has no public-facing website or app."
        else:
            reason = "TTDSG does not apply: company does not process personal data online."
        return TTDSGResult(applies=False, reason=reason)

    return TTDSGResult(
        applies=True,
        reason=(
            "TTDSG (§25 TDDDG) applies: company operates a website or app and processes "
            "personal data of users in Germany. Prior informed consent is required before "
            "setting any non-essential cookies, tracking pixels, analytics scripts, or "
            "fingerprinting technologies on users' devices. No size threshold applies — "
            "all website operators are bound regardless of company size."
        ),
    )


# AML-obligated industries under §2 GwG — maps to Complio industry strings.
# Source: §2(1) GwG [verified from gesetze-im-internet.de/gwg_2017/]
# Nr. 1:  Kreditinstitute (banks, savings banks)
# Nr. 2:  Finanzdienstleistungsinstitute (financial service providers)
# Nr. 3:  Zahlungsinstitute, E-Geld-Institute (payment, e-money)
# Nr. 5:  Investmentvermittler (investment intermediaries)
# Nr. 6:  Versicherungsunternehmen (life insurance)
# Nr. 8:  Kapitalverwaltungsgesellschaften (fund management)
# Nr. 10: Rechtsanwälte, Notare (lawyers, notaries — when managing assets, company formation, real estate)
# Nr. 11: Wirtschaftsprüfer, Steuerberater (accountants, tax advisors)
# Nr. 12: Immobilienmakler (real estate agents) — for transactions ≥€10,000 cash
# Nr. 14: Glücksspielveranstalter (gambling operators)
# Nr. 15: Kryptowertedienstleister (crypto-asset service providers)
# Nr. 13: Güterhändler (goods traders) — only for cash transactions >€10,000
#
# ⚠ The "finance" industry covers Nr. 1-8, 15.
# ⚠ "legal", "real_estate", "gambling", "crypto" must also auto-trigger but may not
#    appear as named industries in the current Industry enum. Companies in these sectors
#    MUST set is_aml_obligated_sector=true if their industry field does not map here.
_GWG_OBLIGATED_INDUSTRIES = {
    "finance",      # banks, financial services, payment, e-money, investment, insurance, crypto
    "real_estate",  # Immobilienmakler — real estate agents (§2(1) Nr. 12)
}


def check_gwg(profile: CompanyProfile) -> GwGResult:
    """
    GwG — Geldwäschegesetz (Anti-Money Laundering Act).

    §2(1) GwG lists 16 categories of obligated entities (Verpflichtete).
    Key categories relevant to German SMEs:
      Nr. 1:  Credit institutions (Kreditinstitute)
      Nr. 2:  Financial service providers (Finanzdienstleistungsinstitute)
      Nr. 3:  Payment and e-money institutions
      Nr. 6:  Life insurance companies and intermediaries
      Nr. 10: Lawyers, notaries, and legal professionals (when managing assets,
              establishing companies, or advising on real estate transactions)
      Nr. 12: Real estate agents (Immobilienmakler)
      Nr. 14: Gambling operators (Glücksspielveranstalter)
      Nr. 15: Crypto-asset service providers (Kryptowertedienstleister)

    Obligated entities must implement: risk analysis (§5), internal safeguards (§6),
    KYC / customer due diligence (§10-§13), AML officer appointment (§7 for larger
    entities), transaction monitoring, and suspicious transaction reporting (§43).

    Source: §2, §5, §6, §7, §10, §43 GwG; FATF Recommendations.
    """
    in_obligated_industry = profile.industry in _GWG_OBLIGATED_INDUSTRIES
    applies = in_obligated_industry or profile.is_aml_obligated_sector

    if not applies:
        return GwGResult(
            applies=False,
            reason=(
                f"GwG does not apply: industry '{profile.industry}' is not in an AML-obligated "
                f"sector under §2 GwG. If the company provides financial services, crypto, "
                f"real estate brokerage, legal/notarial services, or gambling operations, "
                f"set is_aml_obligated_sector=true to trigger a GwG assessment."
            ),
        )

    trigger = (
        f"industry '{profile.industry}' is a GwG-obligated sector (§2 GwG)"
        if in_obligated_industry
        else "company self-declared as AML-obligated sector (is_aml_obligated_sector=true)"
    )
    return GwGResult(
        applies=True,
        reason=(
            f"GwG applies: {trigger}. Obligated entities must implement: risk analysis (§5 GwG), "
            f"internal AML safeguards (§6 GwG), customer due diligence / KYC procedures (§10 GwG), "
            f"beneficial owner identification (§11 GwG), transaction monitoring, and suspicious "
            f"transaction reporting to the FIU (§43 GwG). An AML compliance officer "
            f"(Geldwäschebeauftragter) is mandatory for regulated financial institutions (§7 GwG)."
        ),
    )


def check_eu_data_act(profile: CompanyProfile) -> EUDataActResult:
    """
    EU Data Act — Regulation (EU) 2023/2854.
    Applicable from 12 September 2025.

    Applies to:
      - Manufacturers of connected products (Art. 3-4): IoT devices, smart appliances,
        industrial sensors, wearables, connected vehicles, smart meters — any product
        that generates data during use and is placed on the EU market.
      - Providers of related services (Art. 3): services intrinsically linked to the
        connected product (e.g. companion apps, cloud processing of device data).
      - Data processing service providers (Art. 23-31): cloud, edge, and other data
        processing services — must enable customer switching without obstacles.

    Key obligations for manufacturers / related service providers:
      - By design: products must be designed so data is easily accessible to users (Art. 3)
      - On request: provide users with real-time or near-real-time data access (Art. 4)
      - Third-party sharing: share data with designated third parties on user instruction (Art. 5)
      - No exclusive use: data holders may not prevent user access to their own data (Art. 6)

    Key obligations for data processing service providers (cloud switching):
      - Must enable customers to switch to another provider within maximum 30 business days (Art. 25)
      - Must remove barriers (technical, contractual, financial) to switching (Art. 23)
      - Switching fees must be phased out by 12 September 2027 (Art. 25)

    Source: Art. 2, 3, 4, 5, 6, 23, 25, 40 EU Data Act (Regulation (EU) 2023/2854).
    """
    applies = profile.produces_connected_products or profile.provides_data_processing_services

    if not applies:
        return EUDataActResult(
            applies=False,
            reason=(
                "EU Data Act does not apply: company does not manufacture connected (IoT) "
                "products and does not provide cloud or data processing services. "
                "If either applies, set produces_connected_products=true or "
                "provides_data_processing_services=true."
            ),
        )

    obligations = []
    if profile.produces_connected_products:
        obligations.append(
            "connected product manufacturer: design-for-access obligation (Art. 3), "
            "user data access on request (Art. 4), third-party sharing on user instruction (Art. 5)"
        )
    if profile.provides_data_processing_services:
        obligations.append(
            "data processing service provider: cloud switching obligations (Art. 23-25), "
            "30-day maximum switching period, elimination of switching barriers by Sept 2027"
        )

    return EUDataActResult(
        applies=True,
        reason=(
            f"EU Data Act (Regulation (EU) 2023/2854) applies — applicable since 12 September 2025. "
            f"Obligations: {'; '.join(obligations)}."
        ),
    )


# ── Master applicability function ──────────────────────────────────────────────

def determine_applicable_regulations(
    profile: CompanyProfile,
) -> list[RegulationApplicability]:
    """
    Run all threshold checks and return a list of RegulationApplicability objects
    ready for inclusion in the compliance report.
    """
    gdpr         = check_gdpr(profile)
    lksg         = check_lksg(profile)
    enefg        = check_enefg(profile)
    csrd         = check_csrd(profile)
    bdsg         = check_bdsg(profile)
    nis2         = check_nis2(profile)
    ai_act       = check_ai_act(profile)
    hinschg      = check_hinschg(profile)
    arbschg      = check_arbschg(profile)
    agg          = check_agg(profile)
    milog        = check_milog(profile)
    ttdsg        = check_ttdsg(profile)
    gwg          = check_gwg(profile)
    eu_data_act  = check_eu_data_act(profile)

    return [
        RegulationApplicability(
            regulation=Regulation.GDPR,
            applies=gdpr.applies,
            reason=gdpr.reason,
            key_threshold="Processes personal data (Art. 2 GDPR)",
        ),
        RegulationApplicability(
            regulation=Regulation.LKSG,
            applies=lksg.applies,
            reason=lksg.reason,
            key_threshold=">= 1,000 employees (§1(1) LkSG)",
        ),
        RegulationApplicability(
            regulation=Regulation.ENEFG,
            applies=enefg.applies,
            reason=enefg.reason,
            key_threshold="EnEfG §8 / EDL-G §8: non-SME (>=250 employees OR >50M revenue OR >43M balance sheet)",
        ),
        RegulationApplicability(
            regulation=Regulation.CSRD,
            applies=csrd.applies,
            reason=csrd.reason,
            key_threshold=(
                "2 of 3: >250 employees, >50M revenue, >25M balance sheet"
                + (f" — Wave {csrd.wave}, first FY {csrd.first_reporting_fy}" if csrd.wave else "")
            ),
        ),
        RegulationApplicability(
            regulation=Regulation.BDSG,
            applies=bdsg.applies,
            reason=bdsg.reason,
            key_threshold="German company processing personal data (BDSG §1)",
        ),
        RegulationApplicability(
            regulation=Regulation.NIS2,
            applies=nis2.applies,
            reason=nis2.reason,
            key_threshold=">=50 employees in critical/important sector (Art. 3 NIS2)",
        ),
        RegulationApplicability(
            regulation=Regulation.AI_ACT,
            applies=ai_act.applies,
            reason=ai_act.reason,
            key_threshold="Develops or deploys AI systems (Art. 2 EU AI Act)",
        ),
        RegulationApplicability(
            regulation=Regulation.HINSCHG,
            applies=hinschg.applies,
            reason=hinschg.reason,
            key_threshold=">=50 employees (§12(2) HinSchG)",
        ),
        RegulationApplicability(
            regulation=Regulation.ARBSCHG,
            applies=arbschg.applies,
            reason=arbschg.reason,
            key_threshold="All employers (§3 ArbSchG)",
        ),
        RegulationApplicability(
            regulation=Regulation.AGG,
            applies=agg.applies,
            reason=agg.reason,
            key_threshold="All employers (§6(2) AGG)",
        ),
        RegulationApplicability(
            regulation=Regulation.MILOG,
            applies=milog.applies,
            reason=milog.reason,
            key_threshold="All employers, EUR 12.82/hour minimum (§1 MiLoG)",
        ),
        RegulationApplicability(
            regulation=Regulation.TTDSG,
            applies=ttdsg.applies,
            reason=ttdsg.reason,
            key_threshold="Website/app operator processing personal data of users in Germany (§25 TTDSG)",
        ),
        RegulationApplicability(
            regulation=Regulation.GWG,
            applies=gwg.applies,
            reason=gwg.reason,
            key_threshold="AML-obligated sector under §2 GwG (finance, crypto, real estate, legal, gambling)",
        ),
        RegulationApplicability(
            regulation=Regulation.EU_DATA_ACT,
            applies=eu_data_act.applies,
            reason=eu_data_act.reason,
            key_threshold="Connected product manufacturer or data processing service provider (Art. 2 EU Data Act)",
        ),
    ]
