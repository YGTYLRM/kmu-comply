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
    implementation_plan_required: bool
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
            reason="Unternehmen verarbeitet keine personenbezogenen Daten: DSGVO ist nicht anwendbar.",
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
        f"Datenschutzbeauftragter voraussichtlich erforderlich: {profile.employee_count} "
        f"Mitarbeitende verarbeiten regelmäßig automatisiert personenbezogene Daten (§38 Abs. 1 "
        f"BDSG - ab 20 Personen ständig mit automatisierter Verarbeitung beschäftigt). Hinweis: "
        f"Die genaue Anwendbarkeit hängt davon ab, wie viele Mitarbeitende ständig mit "
        f"automatisierter Verarbeitung befasst sind, nicht nur von der Gesamtmitarbeiterzahl."
        + (" ⚠ GRENZFALL: In Branchen mit überwiegend manueller Verarbeitung sind unter "
           "Umständen weniger als 20 Mitarbeitende tatsächlich ständig mit automatisierter "
           "Verarbeitung befasst - bitte rechtlich prüfen lassen."
           if dpo_borderline else "")
        if dpo_required
        else (
            f"Datenschutzbeauftragter nicht erforderlich: {profile.employee_count} Mitarbeitende "
            f"liegen unter dem Schwellenwert von 20 oder die Verarbeitung erfolgt nur "
            f"gelegentlich (§38 Abs. 1 BDSG)."
        )
    )

    records_required = (
        profile.employee_count >= 250
        or not profile.processing_is_occasional
        or profile.processes_special_category_data
    )
    records_parts = []
    if profile.employee_count >= 250:
        records_parts.append(f"Mitarbeiterzahl {profile.employee_count} >= 250 (Art. 30 Abs. 5 DSGVO)")
    if not profile.processing_is_occasional:
        records_parts.append("Verarbeitung erfolgt nicht nur gelegentlich (Art. 30 Abs. 5 DSGVO)")
    if profile.processes_special_category_data:
        records_parts.append("verarbeitet besondere Kategorien personenbezogener Daten (Art. 30 Abs. 5 DSGVO)")

    records_reason = (
        "Verarbeitungsverzeichnis erforderlich: " + "; ".join(records_parts) + "."
        if records_required
        else "Verarbeitungsverzeichnis nicht zwingend erforderlich (Ausnahme nach Art. 30 Abs. 5 DSGVO für KMU mit weniger als 250 Mitarbeitenden und nur gelegentlicher Verarbeitung)."
    )

    return GDPRResult(
        applies=True,
        dpo_required=dpo_required,
        processing_records_required=records_required,
        reason="Unternehmen verarbeitet personenbezogene Daten: DSGVO ist anwendbar (Art. 2 DSGVO).",
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
            f"LkSG ist direkt anwendbar: {profile.employee_count} Mitarbeitende erreichen den "
            f"Schwellenwert von 1.000 (§1 Abs. 1 LkSG, gültig seit 1. Januar 2024). Die "
            f"Sorgfaltspflichten umfassen den eigenen Geschäftsbereich sowie die Lieferkette. "
            f"Grundsatzerklärung (§6), Risikoanalyse (§5) und Beschwerdeverfahren (§8) sind "
            f"verpflichtend."
        )
    else:
        indirect_note = (
            " Hinweis: Beliefert Ihr Unternehmen LkSG-verpflichtete Kunden (>= 1.000 "
            "Mitarbeitende), können Sie auch ohne direkte LkSG-Anwendbarkeit "
            "Sorgfaltspflichten-Fragebögen und vertragliche Verpflichtungen von diesen Kunden "
            "erhalten."
            if profile.has_supply_chain_abroad or profile.employee_count >= 500
            else ""
        )
        reason = (
            f"LkSG ist nicht direkt anwendbar: {profile.employee_count} Mitarbeitende liegen "
            f"unter dem Schwellenwert von 1.000 (§1 Abs. 1 LkSG).{indirect_note}"
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
      [Verified from official text — gesetze-im-internet.de/enefg/__9.html]:
      "Unternehmen mit einem jährlichen durchschnittlichen Gesamtendenergieverbrauch
       innerhalb der letzten drei abgeschlossenen Kalenderjahre von mehr als
       2,5 Gigawattstunden sind verpflichtet, [...] konkrete, durchführbare
       Umsetzungspläne zu erstellen und zu veröffentlichen."
      → Independent of §8(1): applies to ANY company (SME or not) with >2.5 GWh
        AVERAGE consumption, a lower threshold than the >7.5 GWh EnMS duty, so a
        company between 2.5 and 7.5 GWh owes implementation plans without yet
        owing an EnMS.

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

    # TRACK 2: EnEfG §9 — independent, lower 2.5 GWh threshold for implementation
    # plans. Every company subject to §8(1) (>7.5 GWh) is also above this, but a
    # company between 2.5 and 7.5 GWh owes this duty without owing an EnMS.
    implementation_plan_required = energy_gwh > 2.5

    # TRACK 1: EDL-G §8 audit — applies only to non-SME companies
    edl_g_audit_required = is_non_sme

    applies = is_non_sme or enms_required or implementation_plan_required

    if not applies:
        unmet = []
        if not exceeds_employees:
            unmet.append(f"{profile.employee_count} Mitarbeitende < 250")
        if not exceeds_revenue:
            unmet.append(
                "Umsatz nicht angegeben" if profile.annual_revenue_eur is None
                else f"Umsatz {profile.annual_revenue_eur:,.0f} EUR <= 50 Mio."
            )
        if not exceeds_balance:
            unmet.append(
                "Bilanzsumme nicht angegeben" if profile.balance_sheet_total_eur is None
                else f"Bilanzsumme {profile.balance_sheet_total_eur:,.0f} EUR <= 43 Mio."
            )
        energy_note = (
            "jährlicher Energieverbrauch nicht angegeben - bitte angeben, um §8 Abs. 1 und §9 EnEfG zu prüfen"
            if energy_mwh == 0
            else f"Energieverbrauch {energy_gwh:.1f} GWh <= Schwellenwert von 2,5 GWh"
        )
        return EnEfGResult(
            applies=False,
            edl_g_audit_required=False,
            energy_management_required=False,
            implementation_plan_required=False,
            waste_heat_reporting_required=False,
            reason=(
                f"EnEfG / EDL-G sind nicht anwendbar - das Unternehmen gilt als EU-KMU "
                f"({'; '.join(unmet)}) und {energy_note} (§8 Abs. 1, §9 EnEfG)."
            ),
        )

    obligations = []
    criteria = []

    if is_non_sme:
        if exceeds_employees:
            criteria.append(f"{profile.employee_count} Mitarbeitende >= 250")
        if exceeds_revenue:
            criteria.append(f"Umsatz {profile.annual_revenue_eur:,.0f} EUR > 50 Mio.")
        if exceeds_balance:
            criteria.append(f"Bilanzsumme {profile.balance_sheet_total_eur:,.0f} EUR > 43 Mio.")
        obligations.append(f"kein KMU ({'; '.join(criteria)}) - Energieaudit alle 4 Jahre verpflichtend (§8 EDL-G)")

    if energy_mwh == 0:
        obligations.append(
            "jährlicher Energieverbrauch nicht angegeben - Status nach §8 Abs. 1 und §9 EnEfG kann "
            "nicht bestätigt werden; bitte 3-Jahres-Durchschnittsverbrauch in GWh angeben"
        )
    elif enms_required:
        obligations.append(
            f"Energieverbrauch {energy_gwh:.1f} GWh > 7,5 GWh (3-Jahres-Durchschnitt) - "
            f"zertifiziertes Energie- oder Umweltmanagementsystem (ISO 50001 oder EMAS) "
            f"verpflichtend (§8 Abs. 1 EnEfG); Energieeinsparungs-Umsetzungspläne erforderlich (§9 EnEfG)"
        )
    elif implementation_plan_required:
        obligations.append(
            f"Energieverbrauch {energy_gwh:.1f} GWh > 2,5 GWh (3-Jahres-Durchschnitt) - "
            f"konkrete Energieeinsparungs-Umsetzungspläne erforderlich (§9 EnEfG), auch ohne "
            f"Pflicht zum Energie- oder Umweltmanagementsystem"
        )

    reason = (
        f"EnEfG / EDL-G sind anwendbar. Pflichten: {'; '.join(obligations)}. "
        f"Bei technisch nutzbarer Abwärme ab 200 kW ist eine Abwärme-Bewertung erforderlich (§16 EnEfG)."
    )

    return EnEfGResult(
        applies=True,
        edl_g_audit_required=edl_g_audit_required,
        energy_management_required=enms_required,
        implementation_plan_required=implementation_plan_required,
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
        met_list.append(f"Mitarbeitende {profile.employee_count} > 250")
    if profile.annual_revenue_eur is not None and profile.annual_revenue_eur > 50_000_000:
        criteria_met += 1
        met_list.append(f"Umsatz {profile.annual_revenue_eur:,.0f} EUR > 50 Mio.")
    if profile.balance_sheet_total_eur is not None and profile.balance_sheet_total_eur > 25_000_000:
        criteria_met += 1
        met_list.append(f"Bilanzsumme {profile.balance_sheet_total_eur:,.0f} EUR > 25 Mio.")

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
            f"CSRD ist nicht anwendbar: nur {criteria_met}/3 Größenkriterien erfüllt"
            + (f" ({'; '.join(met_list)})" if met_list else "")
            + f" - 2 von 3 erforderlich. {unmet_count} Kriterien nicht erfüllt "
            + "(EU-Richtlinie 2022/2464, Art. 5)."
        )
    elif is_pie_above_500:
        wave, first_fy = 1, 2024
        reason = (
            "CSRD ist anwendbar als Welle 1 (kapitalmarktorientiertes Unternehmen von "
            "öffentlichem Interesse mit > 500 Mitarbeitenden): erste Berichtspflicht für das "
            "Geschäftsjahr 2024 (Bericht veröffentlicht 2025). Nicht verschoben durch "
            "Richtlinie (EU) 2025/794."
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
            " ⚠ OMNIBUS-VORBEHALT: Das EU-Omnibus-Paket (Ratseinigung Februar 2026) sieht vor, "
            "den CSRD-Anwendungsbereich auf Unternehmen mit > 1.000 Mitarbeitenden UND > 450 "
            "Mio. EUR Nettoumsatz einzugrenzen. Die formelle Verabschiedung auf EU-Ebene und die "
            "Umsetzung in deutsches Recht stehen mit Stand Mai 2026 noch aus. Dieses Unternehmen "
            "erfüllt die ursprünglichen 2-von-3-Kriterien, jedoch NICHT die vorgeschlagenen "
            "Omnibus-Schwellenwerte - es könnte nach Inkrafttreten aus dem CSRD-Anwendungsbereich "
            "herausfallen. Bitte den aktuellen Stand vor Beginn eines CSRD-Berichtsprogramms "
            "rechtlich prüfen lassen."
            if _below_omnibus else ""
        )
        reason = (
            f"CSRD ist anwendbar als Welle 2: {criteria_met}/3 Größenkriterien erfüllt "
            f"({'; '.join(met_list)}) (EU-Richtlinie 2022/2464, Art. 5). Erstes Berichtsjahr: "
            f"Geschäftsjahr 2027 (Bericht 2028) gemäß Stop-the-Clock-Richtlinie (EU) "
            f"2025/794.{_omnibus_note}"
        )
    else:
        wave, first_fy = 3, 2028
        reason = (
            "CSRD ist anwendbar als Welle 3 (börsennotiertes KMU an einem EU-regulierten Markt). "
            "Das erste Berichtsjahr wurde auf das Geschäftsjahr 2028 (Bericht 2029) gemäß "
            "Richtlinie (EU) 2025/794 verschoben."
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
                "BDSG ist nicht anwendbar: Unternehmen hat seinen Sitz nicht in Deutschland."
                if profile.country != "DE"
                else "BDSG ist nicht anwendbar: Unternehmen verarbeitet keine personenbezogenen Daten."
            ),
        )

    dpo_required = profile.employee_count >= 20 and not profile.processing_is_occasional
    return BDSGResult(
        applies=True,
        dpo_required=dpo_required,
        reason=(
            "BDSG ist anwendbar: deutsches Unternehmen verarbeitet personenbezogene Daten "
            "(§1 BDSG). "
            + (
                f"Datenschutzbeauftragter erforderlich: {profile.employee_count} Mitarbeitende "
                f"erreichen den Schwellenwert von 20 (§38 Abs. 1 BDSG)."
                if dpo_required
                else f"Datenschutzbeauftragter nicht erforderlich: {profile.employee_count} "
                     f"Mitarbeitende < 20 oder die Verarbeitung erfolgt nur gelegentlich (§38 Abs. 1 BDSG)."
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
                f"Die NIS2-Sektoreinordnung kann für die Branche '{profile.industry}' nicht "
                f"eindeutig bestimmt werden. NIS2 / BSIG erfasst 18 spezifische Sektorkategorien "
                f"(Anlage 1 und 2). Bitte anhand der BSI-Sektorleitfäden prüfen, ob Ihr "
                f"Unternehmen unter §28 Abs. 6 oder Abs. 7 BSIG fällt. Markieren Sie Ihr "
                f"Unternehmen im Profil als KRITIS-Betreiber, falls eine entsprechende "
                f"Einstufung vorliegt."
            ),
        )

    if not in_any_scope:
        return NIS2Result(
            applies=False, particularly_important=False, important=False,
            reason=(
                f"NIS2 ist nicht anwendbar: Die Branche '{profile.industry}' zählt nicht zu "
                f"den kritischen oder wichtigen Sektoren nach NIS2 Anlage 1 oder 2 / BSIG, und "
                f"es liegt keine KRITIS-Einstufung vor."
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
            " Das Unternehmen ist als KRITIS-Betreiber eingestuft - unabhängig von "
            "Größenschwellen eine besonders wichtige Einrichtung."
            if profile.is_critical_infrastructure_sector and not is_large
            else ""
        )
        revenue_caveat = (
            " Hinweis: Der Umsatz allein ist nicht für alle Sektoren ausschlaggebend - je "
            "nach Sektor ist nach BSIG zusätzlich die Bilanzsumme zu prüfen."
            if profile.annual_revenue_eur is not None and not (profile.employee_count >= 250)
            else ""
        )
        return NIS2Result(
            applies=True, particularly_important=True, important=False,
            reason=(
                f"NIS2 (BSIG) ist anwendbar als besonders wichtige Einrichtung: "
                f"{profile.employee_count} Mitarbeitende in einem kritischen/wichtigen "
                f"Sektor.{kritis_note} Es gelten die vollen BSIG-Pflichten (§28 Abs. 6 BSIG / "
                f"Art. 3 Abs. 1 NIS2).{revenue_caveat}"
            ),
        )
    if is_important_entity:
        annex = "Anlage 1" if in_annex_i else "Anlage 2"
        return NIS2Result(
            applies=True, particularly_important=False, important=True,
            reason=(
                f"NIS2 (BSIG) ist anwendbar als wichtige Einrichtung: "
                f"{profile.employee_count} Mitarbeitende im Sektor '{profile.industry}' "
                f"({annex}). Es gelten Sicherheits- und Meldepflichten (§28 Abs. 7 BSIG / "
                f"Art. 3 Abs. 2 NIS2)."
            ),
        )

    return NIS2Result(
        applies=False, particularly_important=False, important=False,
        reason=(
            "NIS2 ist nicht anwendbar: Das Unternehmen liegt unter den Größenschwellen "
            "(< 50 Mitarbeitende, < 10 Mio. EUR Umsatz) für den identifizierten Sektor "
            "(Art. 2 Abs. 2 NIS2). Kleinstunternehmen sind in der Regel ausgenommen."
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
            reason="Der EU AI Act ist nicht anwendbar: Das Unternehmen entwickelt oder nutzt keine KI-Systeme.",
        )

    is_high_risk = profile.ai_systems_are_high_risk

    if is_high_risk:
        risk_note = (
            "Die KI-Systeme sind als Hochrisiko-Systeme eingestuft (Anhang III): Es gelten die "
            "vollständigen Anbieter-/Betreiberpflichten, u. a. Risikomanagement (Art. 9), "
            "technische Dokumentation (Art. 11), menschliche Aufsicht (Art. 14) und "
            "Qualitätsmanagementsystem (Art. 17). Für Betreiber im öffentlichen Bereich oder "
            "im HR-Kontext ist eine Grundrechte-Folgenabschätzung erforderlich (Art. 26 Abs. 9)."
        )
    elif is_high_risk is False:
        risk_note = (
            "Die KI-Systeme sind nicht als Hochrisiko-Systeme eingestuft: Es gelten "
            "Transparenzpflichten, sofern die KI mit Menschen interagiert (Art. 50). Bitte die "
            "Einstufung anhand von Anhang III prüfen - Personalentscheidungen, "
            "Kreditwürdigkeitsprüfungen und sicherheitsrelevante Komponenten gelten unabhängig "
            "von der wahrgenommenen Auswirkung stets als Hochrisiko."
        )
    else:
        risk_note = (
            "Die Hochrisiko-Einstufung ist nicht bestätigt. Bitte anhand von Anhang III des EU "
            "AI Act prüfen: KI in Personal-/HR-Entscheidungen, Kreditwürdigkeitsprüfungen, "
            "Bildung, Strafverfolgung oder sicherheitskritischen Systemen gilt unabhängig von "
            "der Unternehmensgröße als Hochrisiko. Transparenzpflichten (Art. 50) gelten in "
            "allen Fällen, in denen KI mit Menschen interagiert."
        )

    active_now = ["verbotene KI-Praktiken nach Art. 5 (seit 2. Februar 2025)"]
    if gpai_rules_active:
        active_now.append("GPAI-Regeln Art. 51-56 (seit 2. August 2025)")

    coming = []
    if not gpai_rules_active:
        coming.append("GPAI-Regeln Art. 51-56 (2. August 2025)")
    if not high_risk_obligations_active:
        coming.append(
            "Pflichten für Hochrisiko-Systeme nach Anhang I und III, Art. 9-17 - aktuell "
            "geltendes Recht: 2. August 2026; HINWEIS: Der Digital-Omnibus-Vorschlag (noch "
            "nicht formell verabschiedet) könnte Anhang III auf den 2. Dezember 2027 "
            "verschieben. Bis zur Veröffentlichung im EU-Amtsblatt als unsicher zu betrachten."
        )
    coming.append("Pflichten für bereits vor August 2026 in Verkehr gebrachte Hochrisiko-Bestandssysteme nach Anhang III (2. August 2027)")

    timeline = (
        f"Aktuell in Kraft: {'; '.join(active_now)}. "
        f"Demnächst: {'; '.join(coming)}."
    )

    return AIActResult(
        applies=True,
        high_risk_obligations_active=high_risk_obligations_active,
        gpai_rules_active=gpai_rules_active,
        reason=(
            f"Der EU AI Act ist anwendbar: Das Unternehmen entwickelt oder nutzt KI-Systeme "
            f"(Art. 2). {risk_note} {timeline}"
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
        f"Das HinSchG ist anwendbar: {profile.employee_count} Mitarbeitende erreichen den "
        f"Schwellenwert von 50 - eine interne Meldestelle ist verpflichtend einzurichten "
        f"(§12 Abs. 2 HinSchG). Frist: Dezember 2023 (50-249 Mitarbeitende) bzw. Juli 2023 "
        f"(ab 250 Mitarbeitenden)."
        if applies
        else f"Das HinSchG ist nicht anwendbar: {profile.employee_count} Mitarbeitende liegen "
             f"unter dem Schwellenwert von 50 (§12 Abs. 2 HinSchG)."
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
        f"Das ArbSchG gilt für alle Arbeitgeber: {profile.employee_count} Mitarbeitende "
        f"(§1 Abs. 2 ArbSchG - 'gilt für alle Arbeitgeber in Deutschland, unabhängig "
        f"von der Anzahl der Beschäftigten'). Gefährdungsbeurteilung (§5), deren "
        f"Dokumentation (§6) und Unterweisung der Beschäftigten (§12) sind verpflichtend."
        if applies
        else "Das ArbSchG ist nicht anwendbar: Es wurden keine Mitarbeitenden angegeben."
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
        f"Das AGG gilt für alle Arbeitgeber: {profile.employee_count} Mitarbeitende. Der "
        f"Arbeitgeber muss aktive Maßnahmen gegen Diskriminierung aufgrund von Rasse, "
        f"Geschlecht, Religion, Behinderung, Alter und sexueller Identität ergreifen "
        f"(§12 AGG). Ein Beschwerdeverfahren ist einzurichten (§13 AGG)."
        if applies
        else "Das AGG ist nicht anwendbar: Es wurden keine Mitarbeitenden angegeben."
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
        f"Das MiLoG gilt für alle Arbeitgeber: {profile.employee_count} Mitarbeitende. Der "
        f"gesetzliche Mindestlohn beträgt derzeit 13,90 EUR/Stunde (§1 MiLoG, gültig ab "
        f"1. Januar 2026; steigt ab 1. Januar 2027 auf 14,60 EUR/Stunde). Für Mitarbeitende "
        f"mit einem Verdienst unter 2.000 EUR/Monat ist eine Arbeitszeiterfassung "
        f"erforderlich (§17 MiLoG)."
        if applies
        else "Das MiLoG ist nicht anwendbar: Es wurden keine Mitarbeitenden angegeben."
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
            reason = "Das TTDSG ist nicht anwendbar: Das Unternehmen betreibt keine öffentlich zugängliche Website oder App."
        else:
            reason = "Das TTDSG ist nicht anwendbar: Das Unternehmen verarbeitet online keine personenbezogenen Daten."
        return TTDSGResult(applies=False, reason=reason)

    return TTDSGResult(
        applies=True,
        reason=(
            "Das TTDSG (§25 TDDDG) ist anwendbar: Das Unternehmen betreibt eine Website oder "
            "App und verarbeitet personenbezogene Daten von Nutzern in Deutschland. Vor dem "
            "Setzen nicht-essenzieller Cookies, Tracking-Pixel, Analyse-Skripte oder "
            "Fingerprinting-Technologien auf Endgeräten der Nutzer ist eine vorherige "
            "informierte Einwilligung erforderlich. Es gilt kein Größenschwellenwert - alle "
            "Website-Betreiber sind unabhängig von der Unternehmensgröße gebunden."
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
                f"Das GwG ist nicht anwendbar: Die Branche '{profile.industry}' zählt nicht zu "
                f"den geldwäscherechtlich verpflichteten Sektoren nach §2 GwG. Bietet das "
                f"Unternehmen Finanzdienstleistungen, Krypto-Dienstleistungen, "
                f"Immobilienmaklertätigkeiten, Rechts-/Notardienstleistungen oder Glücksspiel "
                f"an, markieren Sie es im Profil als geldwäscherechtlich verpflichteten "
                f"Sektor, um eine GwG-Prüfung auszulösen."
            ),
        )

    trigger = (
        f"die Branche '{profile.industry}' zählt zu den GwG-verpflichteten Sektoren (§2 GwG)"
        if in_obligated_industry
        else "das Unternehmen wurde im Profil als geldwäscherechtlich verpflichteter Sektor angegeben"
    )
    return GwGResult(
        applies=True,
        reason=(
            f"Das GwG ist anwendbar: {trigger}. Verpflichtete müssen umsetzen: Risikoanalyse "
            f"(§5 GwG), interne Sicherungsmaßnahmen (§6 GwG), Kundensorgfaltspflichten / "
            f"KYC-Verfahren (§10 GwG), Identifizierung wirtschaftlich Berechtigter (§11 GwG), "
            f"Transaktionsüberwachung sowie Verdachtsmeldungen an die Zentralstelle für "
            f"Finanztransaktionsuntersuchungen (§43 GwG). Für regulierte Finanzinstitute ist "
            f"ein Geldwäschebeauftragter verpflichtend zu bestellen (§7 GwG)."
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
                "Der EU Data Act ist nicht anwendbar: Das Unternehmen stellt keine vernetzten "
                "(IoT-)Produkte her und bietet keine Cloud- oder Datenverarbeitungsdienste an. "
                "Sollte eines davon zutreffen, geben Sie dies bitte im Unternehmensprofil an, "
                "um eine Prüfung nach dem EU Data Act auszulösen."
            ),
        )

    obligations = []
    if profile.produces_connected_products:
        obligations.append(
            "Hersteller vernetzter Produkte: Pflicht zur datenzugangsfreundlichen Gestaltung "
            "(Art. 3), Datenzugriff der Nutzer auf Anfrage (Art. 4), Weitergabe an Dritte auf "
            "Anweisung der Nutzer (Art. 5)"
        )
    if profile.provides_data_processing_services:
        obligations.append(
            "Anbieter von Datenverarbeitungsdiensten: Pflichten zum Anbieterwechsel "
            "(Art. 23-25), maximale Wechselfrist von 30 Werktagen, Abschaffung von "
            "Wechselhindernissen bis September 2027"
        )

    return EUDataActResult(
        applies=True,
        reason=(
            f"Der EU Data Act (Verordnung (EU) 2023/2854) ist anwendbar - gültig seit "
            f"12. September 2025. Pflichten: {'; '.join(obligations)}."
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
            key_threshold="Verarbeitet personenbezogene Daten (Art. 2 DSGVO)",
        ),
        RegulationApplicability(
            regulation=Regulation.LKSG,
            applies=lksg.applies,
            reason=lksg.reason,
            key_threshold=">= 1.000 Mitarbeitende (§1 Abs. 1 LkSG)",
        ),
        RegulationApplicability(
            regulation=Regulation.ENEFG,
            applies=enefg.applies,
            reason=enefg.reason,
            key_threshold="§8 EnEfG / §8 EDL-G: kein KMU (>=250 Mitarbeitende ODER >50 Mio. EUR Umsatz ODER >43 Mio. EUR Bilanzsumme)",
        ),
        RegulationApplicability(
            regulation=Regulation.CSRD,
            applies=csrd.applies,
            reason=csrd.reason,
            key_threshold=(
                "2 von 3: >250 Mitarbeitende, >50 Mio. EUR Umsatz, >25 Mio. EUR Bilanzsumme"
                + (f" - Welle {csrd.wave}, erstes Geschäftsjahr {csrd.first_reporting_fy}" if csrd.wave else "")
            ),
        ),
        RegulationApplicability(
            regulation=Regulation.BDSG,
            applies=bdsg.applies,
            reason=bdsg.reason,
            key_threshold="Deutsches Unternehmen verarbeitet personenbezogene Daten (§1 BDSG)",
        ),
        RegulationApplicability(
            regulation=Regulation.NIS2,
            applies=nis2.applies,
            reason=nis2.reason,
            key_threshold=">=50 Mitarbeitende in kritischem/wichtigem Sektor (Art. 3 NIS2)",
        ),
        RegulationApplicability(
            regulation=Regulation.AI_ACT,
            applies=ai_act.applies,
            reason=ai_act.reason,
            key_threshold="Entwickelt oder nutzt KI-Systeme (Art. 2 EU AI Act)",
        ),
        RegulationApplicability(
            regulation=Regulation.HINSCHG,
            applies=hinschg.applies,
            reason=hinschg.reason,
            key_threshold=">=50 Mitarbeitende (§12 Abs. 2 HinSchG)",
        ),
        RegulationApplicability(
            regulation=Regulation.ARBSCHG,
            applies=arbschg.applies,
            reason=arbschg.reason,
            key_threshold="Alle Arbeitgeber (§3 ArbSchG)",
        ),
        RegulationApplicability(
            regulation=Regulation.AGG,
            applies=agg.applies,
            reason=agg.reason,
            key_threshold="Alle Arbeitgeber (§6 Abs. 2 AGG)",
        ),
        RegulationApplicability(
            regulation=Regulation.MILOG,
            applies=milog.applies,
            reason=milog.reason,
            key_threshold="Alle Arbeitgeber, Mindestlohn 13,90 EUR/Stunde (§1 MiLoG, gültig ab Januar 2026)",
        ),
        RegulationApplicability(
            regulation=Regulation.TTDSG,
            applies=ttdsg.applies,
            reason=ttdsg.reason,
            key_threshold="Website-/App-Betreiber verarbeitet personenbezogene Daten von Nutzern in Deutschland (§25 TTDSG)",
        ),
        RegulationApplicability(
            regulation=Regulation.GWG,
            applies=gwg.applies,
            reason=gwg.reason,
            key_threshold="Geldwäscherechtlich verpflichteter Sektor nach §2 GwG (Finanzen, Krypto, Immobilien, Recht, Glücksspiel)",
        ),
        RegulationApplicability(
            regulation=Regulation.EU_DATA_ACT,
            applies=eu_data_act.applies,
            reason=eu_data_act.reason,
            key_threshold="Hersteller vernetzter Produkte oder Anbieter von Datenverarbeitungsdiensten (Art. 2 EU Data Act)",
        ),
    ]
