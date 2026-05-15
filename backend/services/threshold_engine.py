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


# ── Existing regulations ───────────────────────────────────────────────────────

def check_gdpr(profile: CompanyProfile) -> GDPRResult:
    """
    GDPR applies if the company processes personal data of EU residents.
    DPO required if employee_count >= 20 and processing not occasional (BDSG s38).
    Processing records required if:
      - employee_count >= 250, OR
      - processing is not occasional, OR
      - processes special categories of data (Art. 9 GDPR).
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

    dpo_required = (
        profile.employee_count >= 20
        and not profile.processing_is_occasional
    )
    dpo_reason = (
        f"DPO required: {profile.employee_count} employees regularly processing personal data "
        f"(BDSG §38(1) — threshold: 20 employees)."
        if dpo_required
        else (
            f"DPO not required: employee count {profile.employee_count} < 20 threshold "
            f"(BDSG §38(1)) or processing is occasional."
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
    LkSG — Lieferkettensorgfaltspflichtengesetz.

    Direct applicability (§1(1) LkSG):
      - Company has its registered seat, principal place of business, or administrative
        headquarters in Germany, AND
      - >= 3,000 employees (effective 1 Jan 2023), OR
      - >= 1,000 employees (effective 1 Jan 2024)
    Employee count includes employees at foreign affiliates where the German parent
    has decisive influence (group counting).

    Note on indirect relevance: SMEs below the threshold may still receive LkSG
    supplier questionnaires and contractual due diligence obligations from their
    LkSG-covered customers. This does not trigger direct LkSG applicability but
    is worth flagging for any company with large-enterprise customers.

    Supply chain location is NOT an applicability trigger — LkSG due diligence
    covers both the company's own business area and its supply chain, regardless
    of whether suppliers are domestic or international.

    Source: §1(1), §2(6) LkSG; BAFA Guidance 2023.
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
    EnEfG / EDL-G — German Energy Efficiency Act 2023 + Energy Services Act (EDL-G).

    Step 1 — Applicability gate: non-SME status by EU Recommendation 2003/361/EC.
    A company is NOT an SME (and therefore subject to these obligations) if it exceeds
    ANY ONE of the three EU criteria:
      >= 250 employees, OR
      > EUR 50M annual turnover, OR
      > EUR 43M balance sheet total
    Source: EU Recommendation 2003/361/EC Art. 2.

    Step 2 — Which obligation applies (only for non-SME companies):
    EDL-G §8: Energy audit every 4 years (DIN EN 16247-1) is the baseline obligation
      for all non-SME companies. A certified EnMS satisfies this obligation.
    EnEfG §8(1): If annual total final energy consumption >= 7.5 GWh (averaged
      over the last 3 completed calendar years), a certified energy management
      system (ISO 50001) or EMAS registration is mandatory (replaces audit).
    EnEfG §9: Companies above applicable consumption thresholds must prepare and
      implement energy-saving measure plans and document their progress.

    Waste heat (EnEfG §15):
    Non-SME companies with technically usable waste heat >= 200 kW must assess,
    document, and report waste heat potential, and consider reuse options.
    This is triggered by operational heat processes, not by total energy consumption.

    Source: EDL-G §8; EnEfG §8(1), §9, §15; BAFA Guidance on EnEfG 2023.
    """
    exceeds_employees = profile.employee_count >= 250
    exceeds_revenue   = (profile.annual_revenue_eur is not None
                         and profile.annual_revenue_eur > 50_000_000)
    exceeds_balance   = (profile.balance_sheet_total_eur is not None
                         and profile.balance_sheet_total_eur > 43_000_000)

    is_non_sme = exceeds_employees or exceeds_revenue or exceeds_balance

    if not is_non_sme:
        unmet = []
        if not exceeds_employees:
            unmet.append(f"{profile.employee_count} employees < 250")
        if not exceeds_revenue:
            unmet.append(
                "revenue not provided" if profile.annual_revenue_eur is None
                else f"revenue {profile.annual_revenue_eur:,.0f} EUR <= 50M"
            )
        if not exceeds_balance:
            unmet.append(
                "balance sheet not provided" if profile.balance_sheet_total_eur is None
                else f"balance sheet {profile.balance_sheet_total_eur:,.0f} EUR <= 43M"
            )
        return EnEfGResult(
            applies=False,
            edl_g_audit_required=False,
            energy_management_required=False,
            waste_heat_reporting_required=False,
            reason=(
                f"EnEfG / EDL-G do not apply — qualifies as EU SME ({'; '.join(unmet)}). "
                f"Energy audit and management obligations only apply to non-SME enterprises."
            ),
        )

    # Non-SME — determine which specific obligation applies
    energy_mwh = profile.annual_energy_consumption_mwh or 0
    energy_gwh  = energy_mwh / 1000  # convert MWh → GWh for §8 threshold

    # >= 7.5 GWh → certified EnMS mandatory under EnEfG §8(1); satisfies the EDL-G §8 audit
    # <  7.5 GWh → energy audit every 4 years under EDL-G §8 is the baseline obligation
    enms_required      = energy_gwh >= 7.5
    edl_g_audit_required = True  # always required for non-SME; EnMS satisfies this if enms_required

    criteria = []
    if exceeds_employees:
        criteria.append(f"{profile.employee_count} employees >= 250")
    if exceeds_revenue:
        criteria.append(f"revenue {profile.annual_revenue_eur:,.0f} EUR > 50M")
    if exceeds_balance:
        criteria.append(f"balance sheet {profile.balance_sheet_total_eur:,.0f} EUR > 43M")

    if energy_mwh == 0:
        energy_note = (
            "Annual energy consumption not provided — cannot determine whether EnEfG §8(1) EnMS "
            "obligation (>= 7.5 GWh) or EDL-G §8 energy audit (every 4 years) applies. "
            "Provide annual energy consumption for a precise assessment."
        )
    elif enms_required:
        energy_note = (
            f"Annual energy consumption {energy_gwh:.1f} GWh >= 7.5 GWh threshold: "
            f"certified energy management system (ISO 50001 or EMAS) mandatory (EnEfG §8(1)). "
            f"This satisfies the EDL-G §8 energy audit obligation. "
            f"Energy-saving measure implementation plans also required (EnEfG §9)."
        )
    else:
        energy_note = (
            f"Annual energy consumption {energy_gwh:.1f} GWh < 7.5 GWh threshold: "
            f"energy audit every 4 years (DIN EN 16247-1) required (EDL-G §8). "
            f"A certified EnMS (ISO 50001 or EMAS) is an accepted alternative."
        )

    reason = (
        f"EnEfG / EDL-G apply — non-SME enterprise ({'; '.join(criteria)}). "
        f"{energy_note} "
        f"Waste heat assessment required if technically usable waste heat >= 200 kW (EnEfG §15)."
    )

    return EnEfGResult(
        applies=True,
        edl_g_audit_required=edl_g_audit_required,
        energy_management_required=enms_required,
        waste_heat_reporting_required=True,
        reason=reason,
    )


def check_csrd(profile: CompanyProfile) -> CSRDResult:
    """
    CSRD — Corporate Sustainability Reporting Directive (EU) 2022/2464.

    Size criteria (2 of 3 must be met to qualify as a large company):
      > 250 employees, OR
      > EUR 50M annual net turnover, OR
      > EUR 25M balance sheet total
    Source: Art. 3(4) Accounting Directive 2013/34/EU as amended by CSRD.

    Application timeline — IMPORTANT: Directive (EU) 2025/794 ("Stop-the-clock")
    postponed certain CSRD obligations:
      Wave 1 (FY 2024, report 2025): Large PIEs already subject to NFRD with >500 employees
        — NOT postponed, reporting as scheduled.
      Wave 2 (FY 2025, report 2026 → postponed to FY 2027, report 2028):
        Large companies meeting 2/3 criteria, not yet in Wave 1.
      Wave 3 (FY 2026, report 2027 → postponed to FY 2028, report 2029):
        Listed SMEs, small and non-complex credit institutions, captive insurance.
      Source: Directive (EU) 2025/794, April 2025.

    Listed SMEs:
      Listed SMEs on EU-regulated markets fall under CSRD (Wave 3, postponed).
      They may opt out until 2028 under the Stop-the-clock postponement.
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

    stop_the_clock_note = (
        " IMPORTANT: Directive (EU) 2025/794 ('Stop-the-clock') has postponed Wave 2 "
        "reporting obligations by 2 years. Verify your specific wave with your auditor "
        "before planning implementation."
    )

    if profile.is_listed_company and not is_large:
        reason = (
            f"CSRD applies: listed company on EU-regulated market (Wave 3, postponed). "
            f"First reporting year postponed to FY 2028 under Directive (EU) 2025/794."
        )
    elif is_large:
        reason = (
            f"CSRD applies: {criteria_met}/3 size criteria met ({'; '.join(met_list)}) "
            f"(EU Directive 2022/2464, Art. 5).{stop_the_clock_note}"
        )
    else:
        unmet_count = 3 - criteria_met
        reason = (
            f"CSRD does not apply: only {criteria_met}/3 size criteria met"
            + (f" ({'; '.join(met_list)})" if met_list else "")
            + f" — 2/3 required. {unmet_count} criteria not met "
            + f"(EU Directive 2022/2464, Art. 5)."
        )

    return CSRDResult(applies=applies, criteria_met=criteria_met, reason=reason)


def check_bdsg(profile: CompanyProfile) -> BDSGResult:
    """
    BDSG applies if the company is in Germany and processes personal data.
    DPO required if >= 20 employees regularly processing personal data (BDSG §38(1)).
    BDSG supplements GDPR — cannot apply without GDPR also applying.
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
            f"BDSG applies: German company processing personal data (BDSG §1). "
            + (
                f"DPO required: {profile.employee_count} employees >= 20 threshold (BDSG §38(1))."
                if dpo_required
                else f"DPO not required: {profile.employee_count} employees < 20 or processing is occasional (BDSG §38(1))."
            )
        ),
    )


# ── New Tier 1 regulations ─────────────────────────────────────────────────────

_NIS2_CRITICAL_INDUSTRIES = {
    "energy", "finance", "healthcare", "logistics", "it_software",
}


def check_nis2(profile: CompanyProfile) -> NIS2Result:
    """
    NIS2 Directive (EU) 2022/2555, implemented in Germany via BSIG (NIS2UmsuCG).

    German BSIG categories (not EU Directive terms):
      besonders wichtige Einrichtungen (§28(6) BSIG): >= 250 employees OR >= 50M revenue
        in a critical sector — OR designated KRITIS operator regardless of size.
      wichtige Einrichtungen (§28(7) BSIG): >= 50 employees OR >= 10M revenue
        in a critical/important sector.

    Note: revenue-based thresholds may not be sufficient alone — some sectors also require
    balance sheet assessment; in all cases, KRITIS designation overrides size thresholds.

    Source: NIS2 Art. 2, 3; BSIG §28(6), §28(7); BSI sector guidance.
    """
    in_critical_sector = (
        profile.is_critical_infrastructure_sector
        or profile.industry in _NIS2_CRITICAL_INDUSTRIES
    )

    if not in_critical_sector:
        return NIS2Result(
            applies=False, particularly_important=False, important=False,
            reason=(
                f"NIS2 does not apply: industry '{profile.industry}' is not in a critical "
                f"or important sector under NIS2 Art. 3, and no KRITIS designation set."
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

    # besonders wichtige Einrichtung: size threshold OR KRITIS operator status
    is_particularly_important = is_large or profile.is_critical_infrastructure_sector

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
    if is_medium:
        return NIS2Result(
            applies=True, particularly_important=False, important=True,
            reason=(
                f"NIS2 (BSIG) applies as wichtige Einrichtung: "
                f"{profile.employee_count} employees in critical/important sector. "
                f"Security and incident reporting obligations apply (§28(7) BSIG / Art. 3(2) NIS2)."
            ),
        )

    return NIS2Result(
        applies=False, particularly_important=False, important=False,
        reason=(
            f"NIS2 does not apply: below size thresholds (< 50 employees, < 10M revenue) "
            f"for the identified sector. Small enterprises generally exempt (Art. 2(2) NIS2)."
        ),
    )


def check_ai_act(profile: CompanyProfile) -> AIActResult:
    """
    EU AI Act — Regulation (EU) 2024/1689.

    Application timeline (phased rollout):
      2 Feb 2025: Prohibited AI practices banned (Art. 5)
      2 Aug 2025: GPAI model rules and governance obligations (Art. 51–56, Title III Ch. 2)
      2 Aug 2026: High-risk AI system obligations for Annex I systems (safety components)
      2 Aug 2027: High-risk AI obligations for Annex III systems already on market before Aug 2026
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
    HinSchG — Hinweisgeberschutzgesetz (Whistleblower Protection Act).
    Mandatory internal reporting channel for employers with >= 50 employees.
    Source: HinSchG §12(2).
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
    ArbSchG — Arbeitsschutzgesetz (Occupational Health and Safety Act).
    Applies to all employers with at least one employee.
    Source: ArbSchG §2(3), §3.
    """
    applies = profile.employee_count >= 1
    reason = (
        f"ArbSchG applies to all employers: {profile.employee_count} employees. "
        f"Risk assessment (§5), documentation (§6), and employee instruction (§12) are mandatory."
        if applies
        else "ArbSchG does not apply: no employees reported."
    )
    return ArbSchGResult(applies=applies, reason=reason)


def check_agg(profile: CompanyProfile) -> AGGResult:
    """
    AGG — Allgemeines Gleichbehandlungsgesetz (General Equal Treatment Act).
    Applies to all employers. Prohibits discrimination on 6 protected grounds.
    Source: AGG §6(2), §12.
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
    MiLoG — Mindestlohngesetz (Minimum Wage Act).
    Applies to all employers. Current minimum wage: EUR 12.82/hour (2025).
    Working time documentation required for employees earning < EUR 2,000/month.
    Source: MiLoG §1, §17, §20.
    """
    applies = profile.employee_count >= 1
    reason = (
        f"MiLoG applies to all employers: {profile.employee_count} employees. "
        f"Current statutory minimum wage is EUR 12.82/hour (§1 MiLoG, 2025). "
        f"Working time records required for employees earning < EUR 2,000/month (§17 MiLoG)."
        if applies
        else "MiLoG does not apply: no employees reported."
    )
    return MiLoGResult(applies=applies, reason=reason)


# ── Master applicability function ──────────────────────────────────────────────

def determine_applicable_regulations(
    profile: CompanyProfile,
) -> list[RegulationApplicability]:
    """
    Run all threshold checks and return a list of RegulationApplicability objects
    ready for inclusion in the compliance report.
    """
    gdpr    = check_gdpr(profile)
    lksg    = check_lksg(profile)
    enefg   = check_enefg(profile)
    csrd    = check_csrd(profile)
    bdsg    = check_bdsg(profile)
    nis2    = check_nis2(profile)
    ai_act  = check_ai_act(profile)
    hinschg = check_hinschg(profile)
    arbschg = check_arbschg(profile)
    agg     = check_agg(profile)
    milog   = check_milog(profile)

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
            key_threshold="2 of 3: >250 employees, >50M revenue, >25M balance sheet",
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
    ]
