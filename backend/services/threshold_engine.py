"""
Deterministic regulation applicability engine.

All threshold logic is hardcoded here. Never delegate these decisions to an LLM.
Thresholds are sourced from the regulatory texts cited in each function's docstring.
"""

from dataclasses import dataclass
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
    energy_audit_required: bool
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
    essential: bool
    important: bool
    reason: str


@dataclass(frozen=True)
class AIActResult:
    applies: bool
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
    LkSG applies if employee_count >= 1000 (since Jan 2024).
    Source: §1(1) LkSG.
    """
    applies = profile.employee_count >= 1000
    reason = (
        f"LkSG applies: {profile.employee_count} employees >= 1,000 threshold (§1(1) LkSG, effective Jan 2024)."
        if applies
        else f"LkSG does not apply: {profile.employee_count} employees < 1,000 threshold (§1(1) LkSG, effective Jan 2024)."
    )
    return LkSGResult(applies=applies, reason=reason)


def check_enefg(profile: CompanyProfile) -> EnEfGResult:
    """
    Energy audit required if NOT an SME by EU definition (>250 employees OR >50M revenue).
    Energy management system (ISO 50001) required if annual_energy_consumption >= 7500 MWh (§8 EnEfG).
    Waste heat reporting required if annual_energy_consumption >= 2500 MWh (§15 EnEfG).
    """
    is_large_enterprise = (
        profile.employee_count > 250
        or (profile.annual_revenue_eur is not None and profile.annual_revenue_eur > 50_000_000)
    )
    audit_required = is_large_enterprise

    energy_kwh = (profile.annual_energy_consumption_mwh or 0)
    mgmt_required = energy_kwh >= 7500
    waste_heat_required = energy_kwh >= 2500

    parts = []
    if audit_required:
        criteria = []
        if profile.employee_count > 250:
            criteria.append(f"{profile.employee_count} employees > 250")
        if profile.annual_revenue_eur and profile.annual_revenue_eur > 50_000_000:
            criteria.append(f"revenue {profile.annual_revenue_eur:,.0f} EUR > 50M")
        parts.append(f"Energy audit required — not an EU SME ({'; '.join(criteria)}) (§8(3) EnEfG).")
    else:
        parts.append(f"Energy audit not required — qualifies as EU SME (<=250 employees, <=50M revenue) (§8(3) EnEfG).")

    if mgmt_required:
        parts.append(f"Energy management system required: {energy_kwh} MWh >= 7,500 MWh (§8(1) EnEfG).")
    if waste_heat_required:
        parts.append(f"Waste heat reporting required: {energy_kwh} MWh >= 2,500 MWh (§15 EnEfG).")

    applies = audit_required or mgmt_required or waste_heat_required
    return EnEfGResult(
        applies=applies,
        energy_audit_required=audit_required,
        energy_management_required=mgmt_required,
        waste_heat_reporting_required=waste_heat_required,
        reason=" ".join(parts) if parts else "EnEfG does not apply.",
    )


def check_csrd(profile: CompanyProfile) -> CSRDResult:
    """
    CSRD applies if at least 2 of 3 criteria are met:
      - employee_count > 250
      - annual_revenue > 50M EUR
      - balance_sheet_total > 25M EUR
    Listed SMEs fall under CSRD from 2026 regardless.
    Source: EU Directive 2022/2464, Art. 5.
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

    applies = criteria_met >= 2 or profile.is_listed_company

    if profile.is_listed_company and criteria_met < 2:
        reason = "CSRD applies: listed company (CSRD listed SME provisions from 2026, EU Directive 2022/2464)."
    elif applies:
        reason = f"CSRD applies: {criteria_met}/3 criteria met ({'; '.join(met_list)}) — threshold is 2/3 (EU Directive 2022/2464, Art. 5)."
    else:
        unmet = 3 - criteria_met
        reason = (
            f"CSRD does not apply: only {criteria_met}/3 criteria met"
            + (f" ({'; '.join(met_list)})" if met_list else "")
            + f" — need 2/3 (EU Directive 2022/2464, Art. 5). {unmet} criteria not met."
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
    NIS2 Directive (EU) 2022/2555.
    Essential entities: >= 250 employees OR >= 50M revenue, in critical sector.
    Important entities: >= 50 employees OR >= 10M revenue, in critical/important sector.
    Source: NIS2 Art. 2, 3.
    """
    in_critical_sector = (
        profile.is_critical_infrastructure_sector
        or profile.industry in _NIS2_CRITICAL_INDUSTRIES
    )

    if not in_critical_sector:
        return NIS2Result(
            applies=False, essential=False, important=False,
            reason=(
                f"NIS2 does not apply: industry '{profile.industry}' is not in a critical "
                f"or important sector under NIS2 Art. 3, and no critical infrastructure flag set."
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

    if is_large:
        return NIS2Result(
            applies=True, essential=True, important=False,
            reason=(
                f"NIS2 applies as Essential Entity: {profile.employee_count} employees "
                f"in critical/important sector. Full NIS2 obligations apply (Art. 3(1) NIS2)."
            ),
        )
    if is_medium:
        return NIS2Result(
            applies=True, essential=False, important=True,
            reason=(
                f"NIS2 applies as Important Entity: {profile.employee_count} employees "
                f"in critical/important sector. Security and incident reporting obligations apply (Art. 3(2) NIS2)."
            ),
        )

    return NIS2Result(
        applies=False, essential=False, important=False,
        reason=(
            f"NIS2 does not apply: below size thresholds (< 50 employees, < 10M revenue) "
            f"for the identified sector. Small enterprises generally exempt (Art. 2(2) NIS2)."
        ),
    )


def check_ai_act(profile: CompanyProfile) -> AIActResult:
    """
    EU AI Act (EU) 2024/1689.
    Applies to any provider or deployer of AI systems in the EU.
    Source: AI Act Art. 2, 3, 26.
    """
    if not profile.uses_ai_systems:
        return AIActResult(
            applies=False,
            reason="EU AI Act does not apply: company does not develop or deploy AI systems.",
        )
    return AIActResult(
        applies=True,
        reason=(
            "EU AI Act applies: company develops or deploys AI systems (Art. 2 EU AI Act). "
            "Deployer obligations include transparency (Art. 13), human oversight (Art. 14), "
            "and fundamental rights impact assessment for high-risk systems (Art. 26)."
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
            key_threshold=">250 employees OR >50M revenue OR >=7,500/2,500 MWh",
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
