from services.pdf_generator import generate_pdf
from models.compliance_report import (
    ComplianceReport, RegulationApplicability,
    ComplianceGap, ActionItem, RegulationScore,
)
from models.enums import Regulation, ComplianceStatus, Priority

report = ComplianceReport(
    job_id="test-123",
    company_name="Muster GmbH",
    generated_at="2026-05-09T00:00:00Z",
    applicable_regulations=[
        RegulationApplicability(
            regulation=Regulation.GDPR, applies=True,
            reason="Company processes personal data of EU residents on a non-occasional basis. GDPR applies in full.",
            key_threshold="Processes personal data",
        ),
        RegulationApplicability(
            regulation=Regulation.BDSG, applies=True,
            reason="German company (country=DE) processing personal data. BDSG supplements GDPR with German-specific requirements including a lower DPO threshold of 20 employees.",
            key_threshold="German company + personal data",
        ),
        RegulationApplicability(
            regulation=Regulation.HINSCHG, applies=True,
            reason="75 employees exceeds the 50-employee threshold under section 12(1) HinSchG. An internal whistleblower reporting channel is mandatory.",
            key_threshold=">=50 employees",
        ),
        RegulationApplicability(
            regulation=Regulation.ARBSCHG, applies=True,
            reason="ArbSchG applies to all employers. The company has 75 employees and is subject to all occupational health and safety obligations including the Gefaehrdungsbeurteilung.",
            key_threshold="All employers",
        ),
        RegulationApplicability(
            regulation=Regulation.LKSG, applies=False,
            reason="LkSG does not apply: 75 employees is below the 1,000-employee threshold effective since January 2024.",
            key_threshold=">=1000 employees",
        ),
        RegulationApplicability(
            regulation=Regulation.CSRD, applies=False,
            reason="CSRD does not apply: 0 of 3 size criteria met (need 2 of 3: >250 employees, >50M revenue, >25M balance sheet).",
            key_threshold="2 of 3 size criteria",
        ),
    ],
    inferred_characteristics=[
        "As an IT/software company, the company almost certainly processes employee personal data (payroll, HR) and customer/user personal data, triggering full GDPR and BDSG obligations.",
        "Software companies typically use third-party cloud services which may constitute data processing agreements requiring documentation under Art. 28 GDPR.",
        "With 75 employees, a Data Protection Officer (DPO) is required under BDSG section 38(1) if data processing is non-occasional - which this profile indicates.",
    ],
    missing_optional_fields=["annual_revenue_eur", "balance_sheet_total_eur"],
    validation_warnings=[
        "Annual revenue was not provided - CSRD and EnEfG applicability may be incomplete.",
        "Balance sheet total was not provided - CSRD applicability assessment may be incomplete.",
    ],
    retrieved_chunks=[],
    gap_analysis=[
        ComplianceGap(
            regulation=Regulation.HINSCHG,
            article_number="§ 12",
            article_title="Interne Meldestellen",
            status=ComplianceStatus.NON_COMPLIANT,
            evidence=(
                "The company has 75 employees which exceeds the 50-employee threshold in § 12(1) HinSchG. "
                "No internal whistleblower reporting channel is mentioned in the profile or uploaded documents. "
                "This obligation has been mandatory for companies with 50-249 employees since 17 December 2023."
            ),
            deficiency_description=(
                "No internal whistleblower reporting channel established. This is a legal obligation that is "
                "overdue since December 2023. The channel must accept reports in written and oral form, must be "
                "operated by an independent person or unit, and must guarantee full confidentiality of the reporting person."
            ),
        ),
        ComplianceGap(
            regulation=Regulation.HINSCHG,
            article_number="§ 25",
            article_title="Verbot von Repressalien",
            status=ComplianceStatus.CANNOT_ASSESS,
            evidence=(
                "§ 25 HinSchG prohibits retaliation against whistleblowers and requires employers to have a clear "
                "policy against retaliation. Without a whistleblower channel in place, it is not possible to assess "
                "whether an anti-retaliation policy exists. Upload your HR policies or employee handbook for assessment."
            ),
            deficiency_description=None,
        ),
        ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="Art. 30",
            article_title="Records of processing activities",
            status=ComplianceStatus.NON_COMPLIANT,
            evidence=(
                "Profile shows has_processing_records=False. With 75 employees and non-occasional processing, "
                "the Art. 30(5) exemption for SMEs does not apply (it only applies where processing is occasional "
                "AND poses no special risk). Records of Processing Activities are mandatory."
            ),
            deficiency_description=(
                "No Records of Processing Activities (Verarbeitungsverzeichnis) maintained. "
                "The document must list all processing activities including: purposes, categories of data subjects "
                "and personal data, recipients, international transfers, retention periods, and security measures."
            ),
        ),
        ComplianceGap(
            regulation=Regulation.GDPR,
            article_number="Art. 37",
            article_title="Designation of the data protection officer",
            status=ComplianceStatus.NON_COMPLIANT,
            evidence=(
                "Profile shows has_dpo=False. With 75 employees and non-occasional processing of personal data, "
                "a Data Protection Officer is required under BDSG § 38(1) which sets a threshold of 20 employees "
                "regularly processing personal data - this company clearly meets this threshold."
            ),
            deficiency_description=(
                "No Data Protection Officer (Datenschutzbeauftragter) appointed. Under BDSG § 38(1), a DPO is "
                "mandatory for companies with 20 or more employees regularly processing personal data. "
                "The DPO must have expert knowledge of data protection law and practices."
            ),
        ),
        ComplianceGap(
            regulation=Regulation.ARBSCHG,
            article_number="§ 5",
            article_title="Beurteilung der Arbeitsbedingungen",
            status=ComplianceStatus.CANNOT_ASSESS,
            evidence=(
                "ArbSchG § 5 requires all employers to conduct a workplace risk assessment (Gefaehrdungsbeurteilung) "
                "covering physical, chemical, biological, and psychological hazards at all workplaces. "
                "The profile does not indicate whether such an assessment has been conducted. "
                "Upload your risk assessment documentation for a definitive evaluation."
            ),
            deficiency_description=None,
        ),
    ],
    action_plan=[
        ActionItem(
            regulation=Regulation.HINSCHG,
            article_number="§ 12",
            action=(
                "Immediately establish an internal whistleblower reporting channel. The channel must: "
                "(1) accept reports in both written form (secure web form or post) and oral form (telephone hotline or in-person meeting on request); "
                "(2) be operated by an independent person or unit with no conflicts of interest; "
                "(3) guarantee strict confidentiality of the identity of reporting persons and any persons named in reports; "
                "(4) send a receipt confirmation within 7 calendar days; and "
                "(5) provide feedback on actions taken within 3 months of receipt. "
                "External providers can be commissioned if they guarantee independence and confidentiality."
            ),
            priority=Priority.CRITICAL,
            estimated_effort="1 to 3 weeks (setup + documentation + staff training)",
            deadline="2026-06-09",
            dependencies=[],
            gap_reference="hinschg:§ 12",
        ),
        ActionItem(
            regulation=Regulation.GDPR,
            article_number="Art. 37",
            action=(
                "Appoint a Data Protection Officer (DPO). The DPO must have expert knowledge of data protection law and practices. "
                "The DPO can be an employee or an external service provider. "
                "Notify the Supervisory Authority (Landesdatenschutzbehoerde) of the DPO appointment. "
                "Publish the DPO contact details on your website and in your privacy policy."
            ),
            priority=Priority.HIGH,
            estimated_effort="1 to 2 weeks (recruitment or external provider selection)",
            deadline=None,
            dependencies=[],
            gap_reference="gdpr_dsgvo:Art. 37",
        ),
        ActionItem(
            regulation=Regulation.GDPR,
            article_number="Art. 30",
            action=(
                "Create and maintain a Records of Processing Activities (Verarbeitungsverzeichnis). "
                "For each processing activity, document: (1) name and contact details of the controller and DPO; "
                "(2) purposes of the processing; (3) categories of data subjects and personal data; "
                "(4) categories of recipients; (5) international transfers and safeguards; "
                "(6) retention periods; and (7) technical and organisational security measures. "
                "Keep this document up to date and make it available to supervisory authorities on request."
            ),
            priority=Priority.HIGH,
            estimated_effort="4 to 12 hours depending on the number of processing activities",
            deadline=None,
            dependencies=["gdpr_dsgvo:Art. 37"],
            gap_reference="gdpr_dsgvo:Art. 30",
        ),
    ],
    regulation_scores=[
        RegulationScore(
            regulation=Regulation.GDPR,
            total_requirements=2, compliant=0, partially_compliant=0,
            non_compliant=2, cannot_assess=0, score_percent=0.0,
        ),
        RegulationScore(
            regulation=Regulation.HINSCHG,
            total_requirements=2, compliant=0, partially_compliant=0,
            non_compliant=1, cannot_assess=1, score_percent=0.0,
        ),
        RegulationScore(
            regulation=Regulation.ARBSCHG,
            total_requirements=1, compliant=0, partially_compliant=0,
            non_compliant=0, cannot_assess=1, score_percent=50.0,
        ),
        RegulationScore(
            regulation=Regulation.BDSG,
            total_requirements=0, compliant=0, partially_compliant=0,
            non_compliant=0, cannot_assess=0, score_percent=50.0,
        ),
    ],
    overall_score_percent=16.7,
    executive_summary=(
        "Muster GmbH, a 75-person IT and software company based in Germany, was assessed against 6 German and EU regulations. "
        "Four regulations are applicable. The overall compliance score of 16.7% reflects serious gaps in two critical areas. "
        "\n\n"
        "The most urgent finding is the complete absence of an internal whistleblower reporting channel under HinSchG. "
        "This obligation has been legally mandatory since December 2023 and the company is now more than two years overdue. "
        "German enforcement of HinSchG has been increasing and penalties of up to EUR 20,000 for failing to establish a channel "
        "and up to EUR 50,000 for retaliation against whistleblowers are applicable. "
        "\n\n"
        "Under GDPR and BDSG, two critical obligations are unmet: no Data Protection Officer has been appointed (mandatory "
        "for companies with 20+ employees regularly processing personal data) and no Records of Processing Activities "
        "(Verarbeitungsverzeichnis) are maintained. Both are among the most commonly enforced GDPR requirements in Germany, "
        "with significant fines issued by German supervisory authorities for non-compliance. "
        "\n\n"
        "The company should immediately prioritise establishing the whistleblower channel, appointing a DPO, and creating "
        "the Records of Processing Activities. These three actions will address the most critical legal exposure."
    ),
    disclaimer=(
        "This report is generated by an AI system and does not constitute legal advice. "
        "It is based solely on the information provided in the company profile and does not take into account "
        "internal documents, contracts, processes, or other evidence not submitted to the system. "
        "The findings should be reviewed and validated by a qualified legal or compliance professional "
        "before any compliance decisions are made. Complio cannot be held liable for the accuracy or "
        "completeness of this screening."
    ),
    requires_manual_review=[],
)

pdf = generate_pdf(report)
with open("test_report_v2.pdf", "wb") as f:
    f.write(pdf)
print(f"PDF generated: {len(pdf):,} bytes -> test_report_v2.pdf")
