"""
Regenerate the PDF preview using the REAL threshold engine output (all 14 regulations,
including the EU Data Act row that previously had the "...set or ." mangling bug),
plus a long executive summary to verify the truncation fix.
Run from backend/. Output: preview_regen.pdf
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models.company_profile import CompanyProfile
from models.compliance_report import (
    ComplianceReport, ComplianceGap, ActionItem, RegulationScore,
)
from models.enums import Regulation, ComplianceStatus, Priority
from services.threshold_engine import determine_applicable_regulations
from services.pdf_generator import generate_pdf

profile = CompanyProfile(
    company_name="Muster GmbH",
    industry="manufacturing",
    country="DE",
    employee_count=75,
    annual_revenue_eur=12_000_000,
    balance_sheet_total_eur=8_000_000,
    processes_personal_data=True,
    has_supply_chain_abroad=True,
    is_critical_infrastructure_sector=False,
    uses_ai_systems=True,
    produces_connected_products=False,
    provides_data_processing_services=False,
)

applicability = determine_applicable_regulations(profile)

report = ComplianceReport(
    job_id="regen-preview-001",
    company_name=profile.company_name,
    generated_at="2026-06-07T12:00:00Z",
    overall_score_percent=47.3,
    executive_summary=(
        "Die Muster GmbH zeigt eine teilweise Compliance über die zehn anwendbaren Vorschriften "
        "hinweg. Kritische Lücken bestehen bei den Betroffenenrechten nach DSGVO und der "
        "verpflichtenden internen Meldestelle nach dem HinSchG, deren Frist bereits seit Dezember "
        "2023 verstrichen ist. Im Bereich Arbeitsschutz ist eine solide Grundlage erkennbar, "
        "jedoch besteht dringender Handlungsbedarf bei den Auftragsverarbeitungsverträgen und der "
        "Einrichtung des gesetzlich vorgeschriebenen Meldekanals. Es wird dringend empfohlen, die "
        "beiden als kritisch eingestuften Maßnahmen vor der nächsten regulatorischen Prüfung "
        "umzusetzen, um Bußgeldrisiken zu vermeiden und die Grundlage für eine nachhaltige "
        "Compliance-Struktur zu schaffen. Mittelfristig empfiehlt sich zudem die Etablierung "
        "eines kontinuierlichen Überwachungsprozesses für alle anwendbaren Vorschriften."
    ),
    applicable_regulations=applicability,
    inferred_characteristics=[
        "KMU im verarbeitenden Gewerbe",
        "Verarbeitet personenbezogene Daten von Beschäftigten und Kunden",
        "Nutzt KI-Systeme im operativen Geschäft",
        "Hat Lieferanten im Ausland",
    ],
    missing_optional_fields=["has_dpo", "has_processing_records"],
    validation_warnings=[
        "Die Felder has_privacy_policy und has_data_breach_procedure sind nicht ausgefüllt - "
        "die DSGVO-Bewertung kann unvollständig sein.",
        "Die Felder has_ai_risk_assessment, has_ai_usage_documentation und "
        "has_human_oversight_procedure sind nicht ausgefüllt.",
    ],
    retrieved_chunks=[],
    gap_analysis=[
        ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="13",
            article_title="Informationspflicht bei Erhebung von personenbezogenen Daten",
            status=ComplianceStatus.PARTIALLY_COMPLIANT,
            evidence="Eine Datenschutzerklärung ist auf der Website vorhanden, enthält jedoch keine Aufbewahrungsfristen je Datenkategorie und keinen Hinweis auf das Beschwerderecht bei einer Aufsichtsbehörde.",
            deficiency_description="Aufbewahrungsfristen je Datenkategorie ergänzen und das Beschwerderecht bei der Aufsichtsbehörde in die Datenschutzerklärung aufnehmen.",
        ),
        ComplianceGap(
            regulation=Regulation.HINSCHG,
            article_number="12",
            article_title="Einrichtung interner Meldestellen",
            status=ComplianceStatus.NON_COMPLIANT,
            evidence="Es wurde kein interner Meldekanal für Hinweisgeber eingerichtet. Die Frist für Unternehmen mit 50-249 Beschäftigten ist seit dem 17. Dezember 2023 abgelaufen.",
            deficiency_description="Einrichtung eines vertraulichen internen Meldekanals (digital oder über eine beauftragte Vertrauensperson).",
        ),
        ComplianceGap(
            regulation=Regulation.ARBSCHG,
            article_number="5",
            article_title="Beurteilung der Arbeitsbedingungen",
            status=ComplianceStatus.COMPLIANT,
            evidence="Die Gefährdungsbeurteilung ist aktuell und deckt alle Arbeitsplätze einschließlich mobiler Arbeit ab.",
        ),
    ],
    action_plan=[
        ActionItem(
            regulation=Regulation.HINSCHG,
            article_number="12",
            action="Einrichtung eines vertraulichen internen Hinweisgeber-Meldekanals gemäß HinSchG. Softwarelösung (z. B. EQS Integrity Line, Trusty) oder geschulte interne Vertrauensperson evaluieren.",
            priority=Priority.CRITICAL,
            estimated_effort="1-2 Wochen Einrichtung + 2.000-5.000 EUR/Jahr für Software",
            deadline="Sofort - bereits seit Dezember 2023 überfällig",
            gap_reference="HinSchG § 12",
            dependencies=[],
        ),
        ActionItem(
            regulation=Regulation.GDPR,
            article_number="13",
            action="Datenschutzerklärung um Aufbewahrungsfristen je Datenkategorie sowie das Beschwerderecht bei der zuständigen Aufsichtsbehörde ergänzen.",
            priority=Priority.HIGH,
            estimated_effort="4-8 Stunden mit rechtlicher Prüfung",
            deadline="Innerhalb von 60 Tagen",
            gap_reference="DSGVO Art. 13",
            dependencies=[],
        ),
    ],
    regulation_scores=[
        RegulationScore(regulation=Regulation.GDPR, total_requirements=2, compliant=0, partially_compliant=1, non_compliant=0, cannot_assess=1, score_percent=37.5),
        RegulationScore(regulation=Regulation.HINSCHG, total_requirements=1, compliant=0, partially_compliant=0, non_compliant=1, cannot_assess=0, score_percent=0.0),
        RegulationScore(regulation=Regulation.ARBSCHG, total_requirements=1, compliant=1, partially_compliant=0, non_compliant=0, cannot_assess=0, score_percent=100.0),
    ],
)

pdf_bytes = generate_pdf(report)
out = "preview_regen.pdf"
with open(out, "wb") as f:
    f.write(pdf_bytes)
print(f"Saved: {out} ({len(pdf_bytes):,} bytes)")
