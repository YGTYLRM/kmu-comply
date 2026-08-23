"""
Render a PDF with fake data — no LLM calls.
Run from backend/:  python scripts/preview_pdf.py
Output: preview_report.pdf in the backend directory.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.compliance_report import (
    ComplianceReport, RegulationApplicability, ComplianceGap,
    ActionItem, RegulationScore,
)
from models.enums import Regulation, ComplianceStatus, Priority
from services.pdf_generator import generate_pdf

report = ComplianceReport(
    job_id="preview-001",
    company_name="Muster GmbH",
    generated_at="2026-05-10T12:00:00",
    overall_score_percent=47.3,
    executive_summary=(
        "Die Muster GmbH zeigt eine teilweise Compliance über die acht anwendbaren Vorschriften. "
        "Kritische Lücken bestehen bei den Betroffenenrechten nach DSGVO sowie beim verpflichtenden "
        "Hinweisgebersystem nach HinSchG. Das Unternehmen verfügt über eine solide Grundlage im "
        "Arbeitsschutz, benötigt jedoch dringend Aufmerksamkeit bei Auftragsverarbeitungsverträgen und "
        "dem internen Meldesystem. Eine sofortige Umsetzung der beiden kritischen Maßnahmen wird "
        "vor dem nächsten regulatorischen Prüfzeitraum dringend empfohlen."
    ),
    applicable_regulations=[
        RegulationApplicability(regulation=Regulation.GDPR,    applies=True,  reason="DSGVO gilt: verarbeitet personenbezogene Daten von EU-Bürgern einschließlich Kunden- und Mitarbeiterdaten."),
        RegulationApplicability(regulation=Regulation.BDSG,    applies=True,  reason="BDSG gilt: Deutsches Unternehmen verarbeitet personenbezogene Daten (BDSG §1)."),
        RegulationApplicability(regulation=Regulation.HINSCHG, applies=True,  reason="HinSchG gilt: 75 Mitarbeiter >= Schwellenwert 50 - interner Hinweisgeberkanal vorgeschrieben (§12 HinSchG)."),
        RegulationApplicability(regulation=Regulation.ARBSCHG, applies=True,  reason="ArbSchG gilt für alle Arbeitgeber: 75 Mitarbeiter (ArbSchG §1 - gilt für alle Arbeitgeber in Deutschland unabhängig von der Größe)."),
        RegulationApplicability(regulation=Regulation.AGG,     applies=True,  reason="AGG gilt für alle Arbeitgeber: 75 Mitarbeiter. Antidiskriminierungsmaßnahmen (§12 AGG) und Beschwerdestellenverfahren (§13 AGG) vorgeschrieben."),
        RegulationApplicability(regulation=Regulation.MILOG,   applies=True,  reason="MiLoG gilt für alle Arbeitgeber: 75 Mitarbeiter. Gesetzlicher Mindestlohn (12,82 Euro/Stunde, 2025) vorgeschrieben."),
        RegulationApplicability(regulation=Regulation.AI_ACT,  applies=True,  reason="EU AI Act gilt: Unternehmen betreibt KI-Systeme in kundenseitigem Produkt (Art. 2)."),
        RegulationApplicability(regulation=Regulation.NIS2,    applies=False, reason="NIS2 gilt nicht: IT-Branche, aber unter dem Schwellenwert von 50 Mitarbeitern für kritische Infrastruktur."),
        RegulationApplicability(regulation=Regulation.LKSG,    applies=False, reason="LkSG gilt nicht: 75 Mitarbeiter < 1.000 Schwellenwert (§1 Abs. 1 LkSG)."),
        RegulationApplicability(regulation=Regulation.ENEFG,   applies=False, reason="EnEfG / EDL-G gelten nicht: 75 Mitarbeiter < 250 (gilt als KMU); Energieverbrauch nicht angegeben."),
        RegulationApplicability(regulation=Regulation.CSRD,    applies=False, reason="CSRD gilt nicht: nur 0/3 Größenkriterien erfüllt (2 von 3 erforderlich: >250 Mitarbeiter, >50 Mio. Euro Umsatz, >25 Mio. Euro Bilanzsumme)."),
    ],
    inferred_characteristics=[
        "KMU mit 75 Mitarbeitern im IT-Sektor",
        "Betreiber von KI-Systemen nach EU AI Act Art. 2",
        "Verarbeiter personenbezogener Daten von Kunden und Mitarbeitern",
        "Arbeitgeber mit Pflichten nach ArbSchG, AGG und MiLoG",
    ],
    missing_optional_fields=[],
    validation_warnings=[],
    retrieved_chunks=[],
    gap_analysis=[
        ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="13",
            article_title="Informationspflichten bei Erhebung personenbezogener Daten",
            status=ComplianceStatus.PARTIALLY_COMPLIANT,
            evidence="Eine Datenschutzerklärung ist auf der Website vorhanden, enthält jedoch keine Aufbewahrungsfristen je Datenkategorie und keinen Hinweis auf das Beschwerderecht bei einer Aufsichtsbehörde.",
            deficiency_description="Die Datenschutzerklärung muss um konkrete Aufbewahrungsfristen je Datenkategorie sowie das Recht auf Beschwerde bei der zuständigen Aufsichtsbehörde (z.B. LfDI) ergänzt werden.",
        ),
        ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="28",
            article_title="Auftragsverarbeiter",
            status=ComplianceStatus.NON_COMPLIANT,
            evidence="Es wurden keine Auftragsverarbeitungsverträge (AVV) mit Drittanbietern wie Cloud-Hosting, Analyse- und E-Mail-Diensten abgeschlossen. Art. 28 DSGVO schreibt dies zwingend vor.",
            deficiency_description="Mit allen Auftragsverarbeitern müssen AVVs abgeschlossen werden. Priorität: AWS, Google Analytics, Mailchimp.",
        ),
        ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="32",
            article_title="Sicherheit der Verarbeitung",
            status=ComplianceStatus.COMPLIANT,
            evidence="Das Unternehmen setzt TLS-Verschlüsselung, Zugriffskontrollen und jährliche Sicherheitsschulungen ein. Diese Maßnahmen sind dem Risiko angemessen.",
        ),
        ComplianceGap(
            regulation=Regulation.HINSCHG,
            article_number="12",
            article_title="Einrichtung interner Meldestellen",
            status=ComplianceStatus.NON_COMPLIANT,
            evidence="Es wurde kein interner Hinweisgeberkanal eingerichtet. Die HinSchG-Frist für Unternehmen ab 50 Mitarbeitern ist bereits im Dezember 2023 abgelaufen.",
            deficiency_description="Ein vertraulicher interner Meldekanal muss eingerichtet werden. Möglich als digitale Lösung (z.B. EQS, Trusty) oder als beauftragter interner Ombudsmann.",
        ),
        ComplianceGap(
            regulation=Regulation.ARBSCHG,
            article_number="5",
            article_title="Beurteilung der Arbeitsbedingungen",
            status=ComplianceStatus.COMPLIANT,
            evidence="Die Gefährdungsbeurteilung ist aktuell und deckt alle Arbeitsplätze einschließlich Homeoffice-Regelungen ab.",
        ),
        ComplianceGap(
            regulation=Regulation.AI_ACT,
            article_number="13",
            article_title="Transparenz und Bereitstellung von Informationen für Betreiber",
            status=ComplianceStatus.PARTIALLY_COMPLIANT,
            evidence="Eine interne KI-Systemdokumentation liegt vor, jedoch werden Nutzer in der Produktoberfläche nicht darüber informiert, dass sie mit einem KI-System interagieren.",
            deficiency_description="In der Produktoberfläche muss ein deutlicher Hinweis ergänzt werden, dass die Funktion durch ein KI-System betrieben wird.",
        ),
        ComplianceGap(
            regulation=Regulation.AGG,
            article_number="12",
            article_title="Maßnahmen des Arbeitgebers",
            status=ComplianceStatus.COMPLIANT,
            evidence="Eine Antidiskriminierungsrichtlinie ist vorhanden, wird beim Onboarding kommuniziert und eine Beschwerdestelle ist benannt.",
        ),
        ComplianceGap(
            regulation=Regulation.MILOG,
            article_number="17",
            article_title="Dokumentationspflicht",
            status=ComplianceStatus.CANNOT_ASSESS,
            evidence="Es kann nicht bestätigt werden, ob Arbeitszeitnachweise für alle Mitarbeiterkategorien vorliegen. Angestellte mit einem Bruttogehalt über 2.958 Euro/Monat sind ausgenommen, Nachweise für Stunden- oder Teilzeitkräfte wurden nicht eingereicht.",
        ),
    ],
    action_plan=[
        ActionItem(
            regulation=Regulation.HINSCHG,
            article_number="12",
            action="Einen vertraulichen internen Hinweisgeberkanal gemäß HinSchG einrichten. Eine Softwarelösung (EQS Integrity Line, Trusty o.Ä.) evaluieren oder einen geschulten internen Ombudsmann benennen. Der Kanal muss Anonymität technisch soweit wie möglich gewährleisten.",
            priority=Priority.CRITICAL,
            estimated_effort="1-2 Wochen Einrichtung + 2.000-5.000 Euro/Jahr für Software",
            deadline="Sofort - Frist seit Dezember 2023 überschritten",
            gap_reference="hinschg:§ 12",
            dependencies=[],
        ),
        ActionItem(
            regulation=Regulation.GDPR,
            article_number="28",
            action="Auftragsverarbeitungsverträge mit allen Drittanbietern abschließen. Priorität: AWS (Cloud-Hosting), Google Analytics (Website-Analyse) und Mailchimp (E-Mail-Marketing). Für Verarbeiter außerhalb der EU Standardvertragsklauseln (SCC) verwenden.",
            priority=Priority.CRITICAL,
            estimated_effort="2-4 Tage für Dokumentenvorbereitung und Unterzeichnung",
            deadline="Innerhalb von 30 Tagen",
            gap_reference="gdpr_dsgvo:Art. 28",
            dependencies=[],
        ),
        ActionItem(
            regulation=Regulation.GDPR,
            article_number="13",
            action="Datenschutzerklärung aktualisieren: (1) Aufbewahrungsfristen je Datenkategorie ergänzen, (2) Beschwerderecht bei der zuständigen Aufsichtsbehörde (BayLDA oder zuständige Landesbehörde) aufnehmen.",
            priority=Priority.HIGH,
            estimated_effort="4-8 Stunden inkl. rechtlicher Prüfung",
            deadline="Innerhalb von 60 Tagen",
            gap_reference="gdpr_dsgvo:Art. 13",
            dependencies=[],
        ),
        ActionItem(
            regulation=Regulation.AI_ACT,
            article_number="13",
            action="Sichtbaren KI-Hinweis in der Produktoberfläche ergänzen, wo immer die KI-Funktion aktiv ist. Beispielformulierung: 'Diese Antwort wurde von einem KI-System generiert.' Onboarding-Flow entsprechend aktualisieren.",
            priority=Priority.MEDIUM,
            estimated_effort="1-3 Tage Entwicklung",
            deadline="Innerhalb von 90 Tagen",
            gap_reference="eu_ai_act:Art. 13",
            dependencies=[],
        ),
        ActionItem(
            regulation=Regulation.MILOG,
            article_number="17",
            action="Arbeitszeitdokumentation für Stunden- und Teilzeitkräfte prüfen. Sicherstellen, dass Nachweise für das laufende und die beiden vorangegangenen Kalenderjahre vorliegen. Bei Lücken ein einfaches Zeiterfassungssystem einführen.",
            priority=Priority.LOW,
            estimated_effort="1-2 Tage Prüfung",
            deadline="Innerhalb von 90 Tagen",
            gap_reference="milog:§ 17",
            dependencies=[],
        ),
    ],
    regulation_scores=[
        RegulationScore(regulation=Regulation.GDPR,    total_requirements=3, compliant=1, partially_compliant=1, non_compliant=1, cannot_assess=0, score_percent=33.0),
        RegulationScore(regulation=Regulation.HINSCHG, total_requirements=1, compliant=0, partially_compliant=0, non_compliant=1, cannot_assess=0, score_percent=0.0),
        RegulationScore(regulation=Regulation.ARBSCHG, total_requirements=1, compliant=1, partially_compliant=0, non_compliant=0, cannot_assess=0, score_percent=100.0),
        RegulationScore(regulation=Regulation.AI_ACT,  total_requirements=1, compliant=0, partially_compliant=1, non_compliant=0, cannot_assess=0, score_percent=50.0),
        RegulationScore(regulation=Regulation.AGG,     total_requirements=1, compliant=1, partially_compliant=0, non_compliant=0, cannot_assess=0, score_percent=100.0),
        RegulationScore(regulation=Regulation.MILOG,   total_requirements=1, compliant=0, partially_compliant=0, non_compliant=0, cannot_assess=1, score_percent=50.0),
    ],
)

pdf_bytes = generate_pdf(report)
out = "preview_report.pdf"
with open(out, "wb") as f:
    f.write(pdf_bytes)
print(f"Saved: {out} ({len(pdf_bytes):,} bytes)")
