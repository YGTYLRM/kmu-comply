"""
Run from backend/ to render a PDF with fake data — no LLM calls.
Output: preview_report.pdf in the backend directory.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

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
        "Muster GmbH shows partial compliance across the eight applicable regulations. "
        "Critical gaps exist in GDPR data subject rights and HinSchG whistleblower channel requirements. "
        "The company has a reasonable foundation in workplace safety but needs urgent attention on data "
        "processing agreements and the mandatory internal reporting system. Immediate action on the two "
        "critical items is strongly recommended before the next regulatory review period."
    ),
    applicable_regulations=[
        RegulationApplicability(regulation=Regulation.GDPR,    applies=True,  reason="Processes personal data of EU residents including customer and employee records."),
        RegulationApplicability(regulation=Regulation.BDSG,    applies=True,  reason="German federal supplement to GDPR applies to all companies processing employee data."),
        RegulationApplicability(regulation=Regulation.HINSCHG, applies=True,  reason="75 employees exceeds the 50-employee threshold for mandatory internal reporting channel."),
        RegulationApplicability(regulation=Regulation.ARBSCHG, applies=True,  reason="ArbSchG applies to all employers with at least one employee in Germany."),
        RegulationApplicability(regulation=Regulation.AGG,     applies=True,  reason="AGG applies to all employers regardless of size or sector."),
        RegulationApplicability(regulation=Regulation.MILOG,   applies=True,  reason="MiLoG applies to all employers. Minimum wage is EUR 12.82/hour."),
        RegulationApplicability(regulation=Regulation.AI_ACT,  applies=True,  reason="Company uses AI systems in customer-facing product, triggering EU AI Act obligations."),
        RegulationApplicability(regulation=Regulation.NIS2,    applies=False, reason="IT sector but below 50-employee critical infrastructure threshold for NIS2."),
        RegulationApplicability(regulation=Regulation.LKSG,    applies=False, reason="LkSG applies only from 1,000 employees. Muster GmbH has 75."),
        RegulationApplicability(regulation=Regulation.ENEFG,   applies=False, reason="EnEfG energy audit obligation requires 250+ employees or EUR 50M+ turnover."),
        RegulationApplicability(regulation=Regulation.CSRD,    applies=False, reason="CSRD sustainability reporting does not apply below 250 employees until 2026."),
    ],
    inferred_characteristics=["SME", "IT sector", "AI system operator", "Personal data processor"],
    missing_optional_fields=[],
    validation_warnings=[],
    retrieved_chunks=[],
    gap_analysis=[
        ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="13",
            article_title="Information to be provided where personal data are collected from the data subject",
            status=ComplianceStatus.PARTIALLY_COMPLIANT,
            evidence="Privacy policy exists on the website but does not include retention periods for each data category or the right to lodge a complaint with a supervisory authority.",
            deficiency_description="Add specific retention periods per data category and include the DPA complaint right in the privacy notice.",
        ),
        ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="28",
            article_title="Processor",
            status=ComplianceStatus.NON_COMPLIANT,
            evidence="No data processing agreements (DPAs) have been signed with third-party service providers including cloud hosting, analytics, and email providers.",
            deficiency_description="Execute DPAs with all processors. Priority vendors: AWS, Google Analytics, Mailchimp.",
        ),
        ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="32",
            article_title="Security of processing",
            status=ComplianceStatus.COMPLIANT,
            evidence="Company uses TLS encryption, access controls, and runs annual security training. These measures are proportionate to the risk level.",
        ),
        ComplianceGap(
            regulation=Regulation.HINSCHG,
            article_number="12",
            article_title="Einrichtung interner Meldestellen",
            status=ComplianceStatus.NON_COMPLIANT,
            evidence="No internal whistleblower reporting channel has been established. The HinSchG deadline for companies with 50+ employees passed in December 2023.",
            deficiency_description="Set up a confidential internal reporting channel. Can be digital (e.g., EQS, Trusty) or a designated internal ombudsperson.",
        ),
        ComplianceGap(
            regulation=Regulation.ARBSCHG,
            article_number="5",
            article_title="Beurteilung der Arbeitsbedingungen",
            status=ComplianceStatus.COMPLIANT,
            evidence="Risk assessment documentation (Gefaehrdungsbeurteilung) is current and covers all workplaces including remote working arrangements.",
        ),
        ComplianceGap(
            regulation=Regulation.AI_ACT,
            article_number="13",
            article_title="Transparency and provision of information to deployers",
            status=ComplianceStatus.PARTIALLY_COMPLIANT,
            evidence="AI system documentation exists internally but users are not informed that they are interacting with an AI system in the product interface.",
            deficiency_description="Add a clear disclosure in the product UI that the feature is powered by an AI system.",
        ),
        ComplianceGap(
            regulation=Regulation.AGG,
            article_number="12",
            article_title="Massnahmen des Arbeitgebers",
            status=ComplianceStatus.COMPLIANT,
            evidence="Anti-discrimination policy is in place, communicated during onboarding, and a complaints contact is designated.",
        ),
        ComplianceGap(
            regulation=Regulation.MILOG,
            article_number="17",
            article_title="Dokumentationspflicht",
            status=ComplianceStatus.CANNOT_ASSESS,
            evidence="Cannot confirm whether working time is documented for all employee categories as required. Salaried employees earning above EUR 2,958/month are exempt but documentation for hourly or part-time staff was not provided.",
        ),
    ],
    action_plan=[
        ActionItem(
            regulation=Regulation.HINSCHG,
            article_number="12",
            action="Establish a confidential internal whistleblower reporting channel compliant with HinSchG. Evaluate a software solution (EQS Integrity Line, Trusty, or equivalent) or designate a trained internal ombudsperson. Channel must guarantee anonymity where technically possible.",
            priority=Priority.CRITICAL,
            estimated_effort="1 to 2 weeks setup + EUR 2,000 to 5,000/year for software",
            deadline="Immediately — already overdue since December 2023",
            gap_reference="HinSchG Art. 12",
            dependencies=[],
        ),
        ActionItem(
            regulation=Regulation.GDPR,
            article_number="28",
            action="Sign Data Processing Agreements with all third-party processors. Start with AWS (cloud hosting), Google Analytics (website analytics), and Mailchimp (email marketing). Use standard SCCs for processors outside the EU.",
            priority=Priority.CRITICAL,
            estimated_effort="2 to 4 days for document preparation and signature",
            deadline="Within 30 days",
            gap_reference="GDPR Art. 28",
            dependencies=[],
        ),
        ActionItem(
            regulation=Regulation.GDPR,
            article_number="13",
            action="Update the privacy policy to include (1) retention periods for each data category, and (2) the right to lodge a complaint with the competent supervisory authority (BayLDA or relevant Landesbehoerde).",
            priority=Priority.HIGH,
            estimated_effort="4 to 8 hours with legal review",
            deadline="Within 60 days",
            gap_reference="GDPR Art. 13",
            dependencies=[],
        ),
        ActionItem(
            regulation=Regulation.AI_ACT,
            article_number="13",
            action="Add a visible AI disclosure label in the product UI wherever the AI feature is active. Wording example: 'This response was generated by an AI system.' Update onboarding flow to include this information.",
            priority=Priority.MEDIUM,
            estimated_effort="1 to 3 days development",
            deadline="Within 90 days",
            gap_reference="EU AI Act Art. 13",
            dependencies=[],
        ),
        ActionItem(
            regulation=Regulation.MILOG,
            article_number="17",
            action="Review working time documentation practices for hourly and part-time staff. Confirm that records exist for the current and previous two calendar years. If gaps exist, implement a simple time-tracking system.",
            priority=Priority.LOW,
            estimated_effort="1 to 2 days audit",
            deadline="Within 90 days",
            gap_reference="MiLoG Art. 17",
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
