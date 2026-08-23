"""
Structured obligation database — Layer 2 of the compliance architecture.

Each Obligation fully describes ONE specific legal requirement. This database
lets the rule engine identify exactly which obligations apply to a company
and which CompanyProfile fields are needed to assess each one.

Regulation coverage:
  GDPR (15+ obligations)        — Arts. 5, 6, 13/14, 17, 28, 30, 32, 33/34, 35, 37, 44
  HinSchG (5 obligations)       — §§12, 13, 14, 16, 17
  NIS2 (8 obligations)          — Arts. 18, 20, 21, 23, 24, 26, 27
  AGG (5 obligations)           — §§3, 6, 12, 13, 14
  MiLoG (4 obligations)         — §§1, 2, 13, 17
  BDSG (4 obligations)          — §§1, 26, 37, 38
  workplace_law (5 obligations) — §§5, 6, 10, 12 ArbSchG + ArbZG
  LkSG (10 obligations)         — §§4, 5, 6(2), 6(1,3), 6(4), 7, 8, 9, 10(1), 10(2)+12
  EnEfG (7 obligations)         — §§8(1-2), 8(3), 9, 10, 16, 17 EnEfG + §8 EDL-G
  GwG (8 obligations)           — §§4-5, 6, 7, 8, 10-13, 15, 20, 43+45
  TTDSG (4 obligations)         — §25(1), §25(2), banner design (DSK), transparency
  CSRD (10 obligations)         — Art. 19a/29a Accounting Directive, ESRS 1/E1/S1/S2/G1, assurance, phase-in
  EU AI Act (8 obligations)     — Art. 5, 6+Annex III, 26(1,5,6,9), 50(1,4)
  EU Data Act (6 obligations)   — Art. 3, 4, 5-6, 13, 23, 25
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.company_profile import CompanyProfile

OBLIGATIONS_VERSION = "v1.2.0"


@dataclass
class Obligation:
    """
    A single, fully described legal requirement.

    Attributes
    ----------
    id : str
        Unique identifier, e.g. "gdpr_art30_ropa".
    regulation : str
        Regulation key (matches Regulation enum value), e.g. "gdpr_dsgvo".
    article : str
        Specific article / paragraph, e.g. "Art. 30 DSGVO".
    title : str
        Short human-readable title in English.
    applies_when : list[str]
        Human-readable conditions under which this obligation is active.
    required_profile_fields : list[str]
        CompanyProfile field names needed to assess this obligation.
    severity : str
        "CRITICAL", "HIGH", "MEDIUM", or "LOW".
    actions : list[str]
        Concrete steps the company must take to satisfy this obligation.
    effort_estimate : str
        Realistic effort estimate, e.g. "4-8 Stunden".
    needs_expert_review : bool
        True if legal / professional review is strongly recommended.
    """
    id: str
    regulation: str
    article: str
    title: str
    applies_when: list[str]
    required_profile_fields: list[str]
    severity: str
    actions: list[str]
    effort_estimate: str
    needs_expert_review: bool = False


# ── GDPR / DSGVO ─────────────────────────────────────────────────────────────

_GDPR_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="gdpr_art5_principles",
        regulation="gdpr_dsgvo",
        article="Art. 5 DSGVO",
        title="Data Processing Principles",
        applies_when=["Company processes personal data"],
        required_profile_fields=["processes_personal_data", "has_data_retention_policy"],
        severity="CRITICAL",
        actions=[
            "Document a data retention policy specifying maximum retention periods for each data category.",
            "Implement data minimisation — collect only data strictly necessary for the stated purpose.",
            "Ensure all personal data processing has a documented legal basis under Art. 6 GDPR.",
            "Conduct a data mapping exercise to inventory all processing activities.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gdpr_art6_lawful_basis",
        regulation="gdpr_dsgvo",
        article="Art. 6 DSGVO",
        title="Lawful Basis for Processing",
        applies_when=["Company processes personal data"],
        required_profile_fields=["processes_personal_data", "has_consent_management"],
        severity="CRITICAL",
        actions=[
            "For each processing activity, document the specific legal basis (consent, contract, legal obligation, legitimate interest, etc.).",
            "Implement consent management for processing activities based on consent (Art. 6(1)(a)).",
            "Conduct legitimate interest assessments (LIA) where Art. 6(1)(f) is relied upon.",
            "Document legal bases in the Records of Processing Activities (Art. 30).",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gdpr_art13_14_transparency",
        regulation="gdpr_dsgvo",
        article="Art. 13-14 DSGVO",
        title="Transparency — Privacy Notice",
        applies_when=["Company processes personal data", "Company has a website or collects data from individuals"],
        required_profile_fields=["processes_personal_data", "has_privacy_policy"],
        severity="HIGH",
        actions=[
            "Publish a compliant Datenschutzerklärung (privacy notice) covering all processing activities.",
            "Include: identity of controller, DPO contact, purposes and legal bases, recipients, retention periods, and data subject rights.",
            "For data collected indirectly (Art. 14), provide notice within 1 month of collection.",
            "Update privacy notice whenever processing activities change.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="gdpr_art17_erasure",
        regulation="gdpr_dsgvo",
        article="Art. 17 DSGVO",
        title="Right to Erasure (Right to be Forgotten)",
        applies_when=["Company processes personal data"],
        required_profile_fields=["processes_personal_data", "has_data_retention_policy"],
        severity="HIGH",
        actions=[
            "Establish a documented process for handling erasure requests within 1 month (extendable by 2 months).",
            "Identify and document all systems where personal data is stored to enable complete erasure.",
            "Implement automated or semi-automated deletion workflows for common data categories.",
            "Train staff responsible for handling data subject requests.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="gdpr_art28_dpa_contracts",
        regulation="gdpr_dsgvo",
        article="Art. 28 DSGVO",
        title="Data Processing Agreements (AVV)",
        applies_when=["Company uses third-party processors (cloud, SaaS, payroll, etc.)"],
        required_profile_fields=["processes_personal_data", "has_processor_agreements"],
        severity="HIGH",
        actions=[
            "Execute a written Auftragsverarbeitungsvertrag (AVV) with every vendor that processes personal data on your behalf.",
            "Ensure each AVV contains all mandatory clauses from Art. 28(3) GDPR.",
            "Maintain a register of all processors and their AVV status.",
            "Review processor AVVs at least annually for continued compliance.",
        ],
        effort_estimate="4-12 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="gdpr_art30_ropa",
        regulation="gdpr_dsgvo",
        article="Art. 30 DSGVO",
        title="Records of Processing Activities (ROPA)",
        applies_when=[
            "Company processes personal data",
            "Exempt only if: <250 employees AND occasional processing AND no special category data",
        ],
        required_profile_fields=["processes_personal_data", "has_processing_records", "employee_count"],
        severity="HIGH",
        actions=[
            "Create and maintain a Verarbeitungsverzeichnis listing all processing activities.",
            "For each activity, document: name/contact of controller, purposes, data categories, recipient categories, third-country transfers, retention periods, and security measures.",
            "Keep the ROPA updated whenever new processing activities begin.",
            "Make the ROPA available to the supervisory authority on request.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="gdpr_art32_security",
        regulation="gdpr_dsgvo",
        article="Art. 32 DSGVO",
        title="Security of Processing (TOMs)",
        applies_when=["Company processes personal data"],
        required_profile_fields=["processes_personal_data", "has_tom_documentation"],
        severity="HIGH",
        actions=[
            "Document all technical and organisational security measures (TOMs) in writing.",
            "Implement encryption for personal data at rest and in transit.",
            "Implement access controls and role-based permissions for systems processing personal data.",
            "Review and update security measures at least annually or after any significant change.",
        ],
        effort_estimate="8-24 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="gdpr_art33_34_breach_notification",
        regulation="gdpr_dsgvo",
        article="Art. 33-34 DSGVO",
        title="Personal Data Breach Notification",
        applies_when=["Company processes personal data"],
        required_profile_fields=["processes_personal_data", "has_data_breach_procedure"],
        severity="CRITICAL",
        actions=[
            "Establish a documented data breach detection and response procedure.",
            "Notify the supervisory authority (BfDI or Landesbehörde) within 72 hours of becoming aware of a breach.",
            "Assess whether affected individuals must be notified (Art. 34) based on risk to rights/freedoms.",
            "Maintain an internal breach register documenting all breaches including non-reportable ones.",
            "Train staff on breach identification and escalation.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gdpr_art35_dpia",
        regulation="gdpr_dsgvo",
        article="Art. 35 DSGVO",
        title="Data Protection Impact Assessment (DPIA)",
        applies_when=[
            "Processing likely to result in high risk to individuals",
            "Large-scale processing of special category data (Art. 9)",
            "Systematic monitoring of publicly accessible areas",
            "Processing using new technologies",
        ],
        required_profile_fields=["processes_special_category_data", "processes_personal_data"],
        severity="HIGH",
        actions=[
            "Identify processing activities that require a DPIA (consult the supervisory authority's list).",
            "For each high-risk processing activity, conduct a formal DPIA documenting: description, necessity assessment, risk assessment, and mitigation measures.",
            "Consult the supervisory authority before proceeding if residual risk remains high after mitigation.",
            "Review DPIAs periodically and when processing activities change significantly.",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gdpr_art37_dpo",
        regulation="gdpr_dsgvo",
        article="Art. 37 DSGVO + BDSG §38",
        title="Data Protection Officer (DPO) Appointment",
        applies_when=[
            ">=20 persons constantly engaged in automated processing of personal data (BDSG §38)",
            "Large-scale processing of special category data (Art. 9 GDPR)",
            "Public authority or body",
        ],
        required_profile_fields=["employee_count", "has_dpo", "processes_special_category_data"],
        severity="HIGH",
        actions=[
            "Appoint a qualified Data Protection Officer (internally or externally).",
            "Register the DPO with the relevant supervisory authority.",
            "Publish the DPO's contact details on the company website and in the privacy notice.",
            "Ensure the DPO has sufficient resources, independence, and access to management.",
        ],
        effort_estimate="4-8 Stunden (appointment process)",
        needs_expert_review=False,
    ),
    Obligation(
        id="gdpr_art44_third_country_transfers",
        regulation="gdpr_dsgvo",
        article="Art. 44-49 DSGVO",
        title="Third Country Data Transfers",
        applies_when=["Company transfers personal data outside the EEA"],
        required_profile_fields=["transfers_data_outside_eea"],
        severity="HIGH",
        actions=[
            "Identify all data flows to recipients outside the EEA (including SaaS providers with US parent companies).",
            "Ensure each transfer relies on an adequacy decision, Standard Contractual Clauses (SCCs), or another Art. 46 mechanism.",
            "Conduct a Transfer Impact Assessment (TIA) for transfers to countries without adequacy decisions.",
            "Document all third-country transfer mechanisms in the ROPA.",
        ],
        effort_estimate="16-32 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gdpr_art5e_retention",
        regulation="gdpr_dsgvo",
        article="Art. 5(1)(e) DSGVO",
        title="Data Retention Limitation",
        applies_when=["Company processes personal data"],
        required_profile_fields=["processes_personal_data", "has_data_retention_policy"],
        severity="HIGH",
        actions=[
            "Define and document retention periods for each category of personal data.",
            "Implement automated deletion or anonymisation workflows at the end of retention periods.",
            "Include retention periods in the ROPA and privacy notice.",
            "Conduct periodic data purges and document them.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="gdpr_art29_32_4_training",
        regulation="gdpr_dsgvo",
        article="Art. 29, 32(4) DSGVO",
        title="Data Protection Training for Staff",
        applies_when=["Company processes personal data with employee involvement"],
        required_profile_fields=["processes_personal_data", "has_data_protection_training"],
        severity="MEDIUM",
        actions=[
            "Provide data protection training to all employees who handle personal data.",
            "Document training completion records per employee.",
            "Repeat training at least annually and whenever processing activities change significantly.",
            "Include training on: lawful bases, data subject rights, breach reporting, and data minimisation.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="gdpr_art6_7_consent",
        regulation="gdpr_dsgvo",
        article="Art. 6-7 DSGVO",
        title="Consent Management",
        applies_when=["Company processes personal data based on consent (e.g. marketing, cookies)"],
        required_profile_fields=["processes_personal_data", "has_consent_management"],
        severity="HIGH",
        actions=[
            "Implement a consent management platform (CMP) for cookie consent on the website.",
            "Ensure consent is freely given, specific, informed, and unambiguous (Art. 7).",
            "Record and store consent with timestamps and the exact wording shown.",
            "Provide an equally easy withdrawal mechanism as the consent mechanism.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="gdpr_art9_special_category",
        regulation="gdpr_dsgvo",
        article="Art. 9 DSGVO",
        title="Special Category Data Processing",
        applies_when=["Company processes health, biometric, racial, political, religious, or other special category data"],
        required_profile_fields=["processes_special_category_data"],
        severity="CRITICAL",
        actions=[
            "Identify an explicit Art. 9(2) legal basis for each special category processing activity.",
            "Implement enhanced security measures for special category data.",
            "Conduct a DPIA (Art. 35) for large-scale special category data processing.",
            "Appoint a DPO if required under Art. 37(1)(c) GDPR.",
            "Document Art. 9 processing prominently in the ROPA.",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
]


# ── HinSchG ──────────────────────────────────────────────────────────────────

_HINSCHG_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="hinschg_12_internal_channel",
        regulation="hinschg",
        article="§12 HinSchG",
        title="Internal Whistleblower Reporting Channel",
        applies_when=["Company has >= 50 employees"],
        required_profile_fields=["employee_count", "has_whistleblower_channel"],
        severity="CRITICAL",
        actions=[
            "Establish a confidential internal reporting channel (digital, phone, or in-person).",
            "Ensure the channel is accessible to all employees, including those working remotely.",
            "For companies with 50-249 employees: may share a channel with other companies (§12(3) HinSchG).",
            "For companies with >= 250 employees: must operate own dedicated channel.",
            "Document the channel's operational procedures.",
        ],
        effort_estimate="8-24 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="hinschg_13_external_channel_info",
        regulation="hinschg",
        article="§13 HinSchG",
        title="Information about External Reporting Channels",
        applies_when=["Company has >= 50 employees"],
        required_profile_fields=["employee_count", "has_whistleblower_policy"],
        severity="MEDIUM",
        actions=[
            "Publish clear information about the availability of external reporting channels (e.g. Federal Office of Justice).",
            "Include external channel information in the internal whistleblower policy document.",
            "Make the information accessible on the company intranet or notice board.",
        ],
        effort_estimate="2-4 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="hinschg_14_documentation",
        regulation="hinschg",
        article="§14 HinSchG",
        title="Whistleblower Case Documentation",
        applies_when=["Company has >= 50 employees"],
        required_profile_fields=["employee_count"],
        severity="HIGH",
        actions=[
            "Maintain confidential records of all reports received through the whistleblower channel.",
            "Document: receipt date, nature of violation reported, follow-up actions, outcome.",
            "Retain records for 3 years after case closure (§14(2) HinSchG).",
            "Ensure only authorised persons have access to case documentation.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="hinschg_16_confidentiality",
        regulation="hinschg",
        article="§16 HinSchG",
        title="Confidentiality of Reporter Identity",
        applies_when=["Company has >= 50 employees"],
        required_profile_fields=["employee_count"],
        severity="CRITICAL",
        actions=[
            "Implement technical and organisational measures to protect reporter identity.",
            "Restrict access to reports to only the person(s) responsible for follow-up.",
            "Document confidentiality procedures in the whistleblower policy.",
            "Train channel managers on the confidentiality obligations under §16 HinSchG.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="hinschg_17_no_retaliation",
        regulation="hinschg",
        article="§17 HinSchG",
        title="Prohibition of Retaliation",
        applies_when=["Company has >= 50 employees"],
        required_profile_fields=["employee_count"],
        severity="CRITICAL",
        actions=[
            "Publish a clear anti-retaliation policy protecting whistleblowers from dismissal, demotion, harassment, or other adverse treatment.",
            "Train managers on the prohibition of retaliation under §17 HinSchG.",
            "Include anti-retaliation provisions in employment contracts or staff handbook.",
            "Establish a process for whistleblowers to report suspected retaliation.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=True,
    ),
]


# ── NIS2 ─────────────────────────────────────────────────────────────────────

_NIS2_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="nis2_art18_risk_management",
        regulation="nis2",
        article="Art. 18 NIS2 / §30 BSIG",
        title="Cybersecurity Risk Management Measures",
        applies_when=["Company is an essential or important entity under NIS2 (Annex I or II, size thresholds met)"],
        required_profile_fields=["has_information_security_policy", "is_critical_infrastructure_sector"],
        severity="CRITICAL",
        actions=[
            "Adopt a comprehensive written information security policy covering all systems and processes.",
            "Implement a risk management framework: identify, assess, treat, and monitor cybersecurity risks.",
            "Document the risk management process and results at least annually.",
            "Ensure management body approves and oversees the cybersecurity risk management measures.",
        ],
        effort_estimate="40-80 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="nis2_art21a_incident_response",
        regulation="nis2",
        article="Art. 21(2)(b) NIS2",
        title="Incident Handling and Response Plan",
        applies_when=["Company is an essential or important entity under NIS2"],
        required_profile_fields=["has_incident_response_plan"],
        severity="CRITICAL",
        actions=[
            "Develop and document an incident response plan covering detection, classification, containment, eradication, and recovery.",
            "Define roles and responsibilities for incident response (CISO, IT team, management).",
            "Conduct at least one incident response exercise per year.",
            "Integrate the incident response plan with the Art. 23 reporting procedure.",
        ],
        effort_estimate="16-32 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="nis2_art21c_business_continuity",
        regulation="nis2",
        article="Art. 21(2)(c) NIS2",
        title="Business Continuity and Disaster Recovery",
        applies_when=["Company is an essential or important entity under NIS2"],
        required_profile_fields=["has_business_continuity_plan"],
        severity="HIGH",
        actions=[
            "Develop a business continuity plan (BCP) and disaster recovery plan (DRP) for critical IT systems.",
            "Define Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) for all critical systems.",
            "Test the BCP/DRP at least annually through tabletop or live exercises.",
            "Maintain offline or air-gapped backups of critical data and configurations.",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="nis2_art21d_supply_chain_security",
        regulation="nis2",
        article="Art. 21(2)(d) NIS2",
        title="Supply Chain Cybersecurity",
        applies_when=["Company is an essential or important entity under NIS2"],
        required_profile_fields=["has_supply_chain_security_assessment"],
        severity="HIGH",
        actions=[
            "Conduct cybersecurity risk assessments of key suppliers and service providers.",
            "Include cybersecurity requirements in contracts with critical suppliers.",
            "Maintain an inventory of all critical suppliers and their security posture.",
            "Review supply chain security at least annually.",
        ],
        effort_estimate="16-32 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="nis2_art21e_vulnerability_management",
        regulation="nis2",
        article="Art. 21(2)(e) NIS2",
        title="Vulnerability Management",
        applies_when=["Company is an essential or important entity under NIS2"],
        required_profile_fields=["has_vulnerability_management"],
        severity="HIGH",
        actions=[
            "Implement a vulnerability management programme: regular scanning, patching, and prioritisation.",
            "Conduct penetration tests at least annually on critical systems.",
            "Establish a patch management process with defined SLAs for critical vulnerabilities.",
            "Maintain vulnerability tracking documentation.",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="nis2_art21g_security_training",
        regulation="nis2",
        article="Art. 21(2)(g) NIS2",
        title="Cybersecurity Awareness Training",
        applies_when=["Company is an essential or important entity under NIS2"],
        required_profile_fields=["has_security_awareness_training"],
        severity="MEDIUM",
        actions=[
            "Deliver mandatory cybersecurity awareness training to all employees at least annually.",
            "Include phishing simulation exercises in the training programme.",
            "Provide specialist training for IT and security staff.",
            "Document training completion records per employee.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="nis2_art21j_mfa",
        regulation="nis2",
        article="Art. 21(2)(j) NIS2",
        title="Multi-Factor Authentication (MFA)",
        applies_when=["Company is an essential or important entity under NIS2"],
        required_profile_fields=["has_mfa_implemented"],
        severity="HIGH",
        actions=[
            "Implement MFA for all remote access to the network (VPN, RDP, cloud portals).",
            "Implement MFA for privileged access to critical systems and data.",
            "Document MFA coverage and any exceptions with compensating controls.",
            "Review MFA implementation at least annually.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="nis2_art23_incident_reporting",
        regulation="nis2",
        article="Art. 23 NIS2 / §32 BSIG",
        title="Significant Incident Reporting (3-Step Process)",
        applies_when=["Company is an essential or important entity under NIS2"],
        required_profile_fields=["has_incident_response_plan"],
        severity="CRITICAL",
        actions=[
            "STEP 1 (within 24 hours): Submit early warning to BSI/CSIRT upon becoming aware of a significant incident.",
            "STEP 2 (within 72 hours): Submit incident notification with initial severity assessment, estimated impact, and indicators of compromise.",
            "STEP 3 (within 1 month): Submit a final report with full incident description, root cause analysis, cross-border impact, and corrective measures taken.",
            "Designate a person responsible for NIS2 incident reporting and ensure BSI contact details are maintained.",
            "Document all incidents and notifications in the internal incident log.",
        ],
        effort_estimate="4-8 Stunden (process setup; actual reporting per incident)",
        needs_expert_review=True,
    ),
]


# ── AGG ──────────────────────────────────────────────────────────────────────

_AGG_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="agg_sec3_prohibition",
        regulation="agg",
        article="§3 AGG",
        title="Prohibition of Direct and Indirect Discrimination",
        applies_when=["Company employs any workers (all employers)"],
        required_profile_fields=["employee_count"],
        severity="HIGH",
        actions=[
            "Review all HR processes (recruitment, promotion, dismissal, pay) for potential discriminatory impact.",
            "Ensure job advertisements and selection criteria are free from discriminatory language or requirements.",
            "Train all managers on direct and indirect discrimination under AGG.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="agg_sec6_protected_grounds",
        regulation="agg",
        article="§6 AGG",
        title="Employer Definition and Protected Persons",
        applies_when=["Company employs any workers, uses temporary agency workers, or engages freelancers"],
        required_profile_fields=["employee_count"],
        severity="MEDIUM",
        actions=[
            "Understand that AGG protects employees, trainees, job applicants, and persons in training-like relationships.",
            "Extend anti-discrimination policies to cover temporary agency workers and freelancers engaged by the company.",
            "Include anti-discrimination provisions in contractor agreements.",
        ],
        effort_estimate="2-4 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="agg_sec12_preventive_measures",
        regulation="agg",
        article="§12 AGG",
        title="Preventive Anti-Discrimination Measures",
        applies_when=["Company employs any workers (all employers)"],
        required_profile_fields=["employee_count", "has_anti_discrimination_policy"],
        severity="HIGH",
        actions=[
            "Adopt and publish a written anti-discrimination and equal treatment policy.",
            "Conduct regular anti-discrimination training for all employees, especially managers.",
            "Post the AGG provisions (§§12-14) prominently at the workplace or company intranet.",
            "Include anti-discrimination provisions in the staff handbook / Arbeitsordnung.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="agg_sec13_complaints_procedure",
        regulation="agg",
        article="§13 AGG",
        title="Discrimination Complaints Procedure",
        applies_when=["Company employs any workers (all employers)"],
        required_profile_fields=["employee_count", "has_agc_complaints_procedure"],
        severity="HIGH",
        actions=[
            "Establish and document a formal complaints procedure for discrimination cases.",
            "Designate a responsible person (e.g. HR, Betriebsrat, or external) to receive and handle complaints.",
            "Communicate the complaints procedure clearly to all employees.",
            "Document all complaints received and actions taken.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="agg_sec14_right_to_refuse",
        regulation="agg",
        article="§14 AGG",
        title="Right to Refuse Discriminatory Conduct",
        applies_when=["Company employs any workers (all employers)"],
        required_profile_fields=["employee_count"],
        severity="MEDIUM",
        actions=[
            "Ensure employees are aware of their right to refuse work where they are exposed to discrimination or harassment.",
            "Include this right in the staff handbook and anti-discrimination policy.",
            "Ensure managers understand they cannot penalise employees for exercising this right.",
        ],
        effort_estimate="2-4 Stunden",
        needs_expert_review=False,
    ),
]


# ── MiLoG ────────────────────────────────────────────────────────────────────

_MILOG_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="milog_sec1_minimum_wage",
        regulation="milog",
        article="§1 MiLoG",
        title="Statutory Minimum Wage",
        applies_when=["Company employs any workers in Germany (all employers)"],
        required_profile_fields=["employee_count"],
        severity="CRITICAL",
        actions=[
            "Verify that all employees (including part-time, mini-job, student) receive at least EUR 12.82/hour gross (2025 rate).",
            "Review payroll systems to ensure the current minimum wage rate is applied correctly.",
            "Note: the minimum wage rate changes periodically — set a calendar reminder to verify after each Mindestlohnkommission announcement.",
        ],
        effort_estimate="2-4 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="milog_sec2_payment_timing",
        regulation="milog",
        article="§2 MiLoG",
        title="Timely Payment of Minimum Wage",
        applies_when=["Company employs any workers in Germany"],
        required_profile_fields=["employee_count"],
        severity="HIGH",
        actions=[
            "Ensure minimum wage is paid by the last bank working day of the month following the month in which the work was performed.",
            "Review payroll cycles and cut-off dates to confirm compliance.",
        ],
        effort_estimate="1-2 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="milog_sec13_subcontractor_liability",
        regulation="milog",
        article="§13 MiLoG",
        title="Principal Employer Liability for Subcontractors",
        applies_when=["Company uses subcontractors who provide labour"],
        required_profile_fields=["employee_count", "uses_subcontractors"],
        severity="HIGH",
        actions=[
            "Include minimum wage compliance warranties in all subcontracting agreements.",
            "Request regular written confirmations from subcontractors that they are paying the minimum wage.",
            "Implement supplier auditing or self-declaration processes for labour compliance.",
            "Document due diligence steps in case of a customs authority (Zollamt) investigation.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="milog_sec17_working_time_records",
        regulation="milog",
        article="§17 MiLoG",
        title="Working Time Records",
        applies_when=[
            "Company employs workers earning <= EUR 2,000/month gross",
            "Company employs workers in specific covered sectors (construction, hospitality, etc.)",
        ],
        required_profile_fields=["employee_count", "has_working_time_records"],
        severity="HIGH",
        actions=[
            "Record the start, end, and duration of working time for all employees earning at or near the minimum wage.",
            "Retain working time records for 2 years (subject to customs authority inspection).",
            "Implement a time recording system (digital or written) accessible per employee.",
            "Ensure timesheets are signed or otherwise authenticated by the employee.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
]


# ── BDSG ─────────────────────────────────────────────────────────────────────

_BDSG_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="bdsg_sec1_scope",
        regulation="bdsg",
        article="§1 BDSG",
        title="BDSG Applicability and Supplementary Rules",
        applies_when=["German company processing personal data (supplements GDPR)"],
        required_profile_fields=["processes_personal_data"],
        severity="MEDIUM",
        actions=[
            "Understand that BDSG supplements and specifies GDPR requirements for Germany — obligations are additive.",
            "Review BDSG-specific rules for employee data processing (§26 BDSG).",
            "Check sector-specific BDSG provisions for banking, insurance, or healthcare if applicable.",
        ],
        effort_estimate="2-4 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="bdsg_sec26_employee_data",
        regulation="bdsg",
        article="§26 BDSG",
        title="Processing of Employee Personal Data",
        applies_when=["Company employs workers and processes employee personal data"],
        required_profile_fields=["processes_personal_data", "employee_count"],
        severity="HIGH",
        actions=[
            "Ensure processing of employee data has a legal basis under §26(1) BDSG (performance of employment relationship, legal obligation, or consent).",
            "Obtain valid consent (§26(2) BDSG) where consent is the basis — note: consent must be truly voluntary given the power imbalance.",
            "Implement purpose limitation for employee data — do not use HR data for other purposes without a separate legal basis.",
            "Document all employee data processing activities in the ROPA.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="bdsg_sec37_restriction_of_access",
        regulation="bdsg",
        article="§37 BDSG",
        title="Data Subject Access Request — Restrictions",
        applies_when=["Company processes personal data in Germany"],
        required_profile_fields=["processes_personal_data"],
        severity="MEDIUM",
        actions=[
            "Establish a process for handling data subject access requests (Auskunftsersuchen) under Art. 15 GDPR / §34 BDSG.",
            "Respond within 1 month (extendable by 2 months for complex cases).",
            "Apply §34/37 BDSG restrictions appropriately where disclosure would harm legitimate interests (document reasoning).",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="bdsg_sec38_dpo",
        regulation="bdsg",
        article="§38 BDSG",
        title="DPO Requirement — BDSG Threshold",
        applies_when=[">=20 persons constantly engaged in automated processing of personal data (BDSG §38(1))"],
        required_profile_fields=["employee_count", "has_dpo"],
        severity="HIGH",
        actions=[
            "Assess whether >=20 staff are constantly engaged in automated personal data processing.",
            "If threshold is met: appoint a qualified Data Protection Officer (internal or external) under §38 BDSG.",
            "The DPO must be registered with the relevant supervisory authority (Landesbehörde).",
            "Provide the DPO with sufficient resources, access, and independence.",
        ],
        effort_estimate="4-8 Stunden (appointment process)",
        needs_expert_review=False,
    ),
]


# ── Workplace Law (ArbSchG) ───────────────────────────────────────────────────

_WORKPLACE_LAW_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="workplace_sec5_gefaehrdungsbeurteilung",
        regulation="workplace_law",
        article="§5 ArbSchG",
        title="Workplace Hazard Risk Assessment (Gefährdungsbeurteilung)",
        applies_when=["Company employs any workers (all employers in Germany)"],
        required_profile_fields=["employee_count", "has_gefaehrdungsbeurteilung"],
        severity="CRITICAL",
        actions=[
            "Conduct a comprehensive Gefährdungsbeurteilung (workplace risk assessment) covering all activities, workstations, and work equipment.",
            "Involve the Betriebsrat (works council) if one exists.",
            "Address all hazard categories: physical, chemical, biological, psychological, ergonomic.",
            "Update the assessment whenever working conditions change significantly.",
        ],
        effort_estimate="8-24 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="workplace_sec6_documentation",
        regulation="workplace_law",
        article="§6 ArbSchG",
        title="Documentation of Hazard Assessment",
        applies_when=["Company employs any workers"],
        required_profile_fields=["employee_count", "has_gefaehrdungsbeurteilung_documented"],
        severity="HIGH",
        actions=[
            "Document the Gefährdungsbeurteilung in writing (required from 10+ employees; best practice for all).",
            "Record: identified hazards, assessed risks, protective measures, implementation responsibility, and review date.",
            "Keep the documentation available for inspection by the Arbeitsschutzbehörde.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="workplace_sec10_first_aid",
        regulation="workplace_law",
        article="§10 ArbSchG",
        title="First Aid and Emergency Measures",
        applies_when=["Company employs any workers"],
        required_profile_fields=["employee_count", "has_first_aid_measures"],
        severity="HIGH",
        actions=[
            "Appoint a sufficient number of trained first aiders (Ersthelfer): at least 1 per 10 employees in low-risk workplaces (DGUV Vorschrift 1).",
            "Provide and maintain first aid kits appropriate for the workplace.",
            "Post emergency contact numbers and procedures in the workplace.",
            "Conduct first aid training and refresher courses for designated first aiders.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="workplace_sec12_safety_instruction",
        regulation="workplace_law",
        article="§12 ArbSchG",
        title="Employee Safety Instructions",
        applies_when=["Company employs any workers"],
        required_profile_fields=["employee_count", "has_employee_safety_training"],
        severity="HIGH",
        actions=[
            "Provide occupational safety instruction to every employee before they start work and repeat regularly (at least annually for most sectors).",
            "Tailor instructions to the specific hazards of each role.",
            "Document instruction completion: employee name, date, content, and signature.",
            "Provide instruction in a language the employee understands.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="workplace_arbzg_working_time",
        regulation="workplace_law",
        article="§3-9 ArbZG",
        title="Working Time Compliance",
        applies_when=["Company employs any workers"],
        required_profile_fields=["employee_count"],
        severity="HIGH",
        actions=[
            "Ensure maximum daily working time of 8 hours (extendable to 10 hours if the average over 6 months does not exceed 8 hours — §3 ArbZG).",
            "Implement mandatory rest periods: 30 minutes after 6 hours, 45 minutes after 9 hours (§4 ArbZG).",
            "Ensure minimum daily rest of 11 consecutive hours between shifts (§5 ArbZG).",
            "Maintain working time records sufficient to demonstrate compliance (supported by the CJEU ruling).",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=True,
    ),
]


# ── LkSG ─────────────────────────────────────────────────────────────────────
# Applies to companies with ≥1 000 employees in Germany (§1 LkSG, threshold since
# 2024-01-01; group headcount is aggregated per §1(3)). Smaller companies are
# frequently affected INDIRECTLY as direct suppliers of obligated customers —
# the rule engine handles that distinction; these obligations describe the
# statutory duties of directly obligated companies (§3(1) duty catalog).

_LKSG_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="lksg_p4_risk_management",
        regulation="lksg",
        article="§ 4 LkSG",
        title="Supply Chain Risk Management System",
        applies_when=["Company is directly obligated under §1 LkSG (≥1 000 employees in Germany)"],
        required_profile_fields=["employee_count", "has_supply_chain_abroad"],
        severity="CRITICAL",
        actions=[
            "Establish an appropriate and effective risk management system anchored in all relevant business processes (§4(1) LkSG).",
            "Designate internal responsibility for monitoring the risk management, e.g. appoint a Menschenrechtsbeauftragter (§4(3) LkSG).",
            "Ensure top management is informed about the responsible person's work at least annually (§4(3) LkSG).",
            "Take the interests of own employees, supply chain workers, and other directly affected parties into account when designing the system (§4(4) LkSG).",
        ],
        effort_estimate="40-80 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="lksg_p5_risk_analysis",
        regulation="lksg",
        article="§ 5 LkSG",
        title="Annual and Ad-hoc Supply Chain Risk Analysis",
        applies_when=["Company is directly obligated under §1 LkSG"],
        required_profile_fields=["has_supply_chain_abroad", "supply_chain_countries"],
        severity="CRITICAL",
        actions=[
            "Conduct a risk analysis covering the own business area and all direct suppliers to identify human-rights and environmental risks (§5(1) LkSG).",
            "Weight and prioritise identified risks using the appropriateness criteria of §3(2) LkSG (§5(2)).",
            "Communicate risk analysis results to relevant decision-makers, e.g. board and purchasing department (§5(3) LkSG).",
            "Repeat the analysis annually and ad hoc whenever the supply chain risk profile changes materially, e.g. new products, projects, or business fields (§5(4) LkSG).",
        ],
        effort_estimate="40-80 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="lksg_p6_2_policy_statement",
        regulation="lksg",
        article="§ 6 Abs. 2 LkSG",
        title="Human Rights Policy Statement (Grundsatzerklärung)",
        applies_when=["Company is directly obligated under §1 LkSG"],
        required_profile_fields=["has_supply_chain_abroad"],
        severity="HIGH",
        actions=[
            "Issue a Grundsatzerklärung on the company's human rights strategy, adopted by top management (§6(2) LkSG).",
            "Describe the procedures used to fulfil the due diligence duties of §§4-10 LkSG.",
            "Name the priority human-rights and environmental risks identified in the risk analysis.",
            "State the human-rights and environment-related expectations towards employees and suppliers in the supply chain.",
        ],
        effort_estimate="16-24 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="lksg_p6_3_prevention_own_business",
        regulation="lksg",
        article="§ 6 Abs. 1, 3 LkSG",
        title="Preventive Measures in Own Business Area",
        applies_when=["Company is directly obligated under §1 LkSG", "Risk analysis identified risks"],
        required_profile_fields=["has_supply_chain_abroad", "industry"],
        severity="HIGH",
        actions=[
            "Implement the human rights strategy from the Grundsatzerklärung in relevant business processes (§6(3) Nr. 1 LkSG).",
            "Develop procurement strategies and purchasing practices that prevent or minimise identified risks (§6(3) Nr. 2 LkSG).",
            "Conduct training in the relevant business areas (§6(3) Nr. 3 LkSG).",
            "Perform risk-based control measures verifying compliance with the human rights strategy in the own business area (§6(3) Nr. 4 LkSG).",
            "Review effectiveness of preventive measures annually and ad hoc (§6(5) LkSG).",
        ],
        effort_estimate="40-80 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="lksg_p6_4_prevention_suppliers",
        regulation="lksg",
        article="§ 6 Abs. 4 LkSG",
        title="Preventive Measures Towards Direct Suppliers",
        applies_when=["Company is directly obligated under §1 LkSG", "Company has direct suppliers"],
        required_profile_fields=["has_supply_chain_abroad", "supply_chain_countries"],
        severity="HIGH",
        actions=[
            "Consider human-rights and environmental expectations when selecting direct suppliers (§6(4) Nr. 1 LkSG).",
            "Obtain contractual assurances from direct suppliers that they comply with and address these expectations along the supply chain (§6(4) Nr. 2 LkSG).",
            "Conduct training to enforce the contractual assurances (§6(4) Nr. 3 LkSG).",
            "Agree and perform risk-based contractual control mechanisms to verify supplier compliance (§6(4) Nr. 4 LkSG).",
        ],
        effort_estimate="24-60 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="lksg_p7_remediation",
        regulation="lksg",
        article="§ 7 LkSG",
        title="Remedial Action on Detected Violations",
        applies_when=["Company is directly obligated under §1 LkSG", "A violation occurred or is imminent in own business or at a direct supplier"],
        required_profile_fields=["has_supply_chain_abroad"],
        severity="CRITICAL",
        actions=[
            "Take immediate appropriate remedial action when a violation has occurred or is imminent; in the domestic own business area the action must END the violation (§7(1) LkSG).",
            "Where a violation at a direct supplier cannot be ended in the foreseeable future, create and implement a time-bound corrective action plan (§7(2) LkSG).",
            "Consider industry initiatives or temporary suspension of the business relationship as escalation steps (§7(2) LkSG).",
            "Terminate the business relationship only as ultima ratio under the conditions of §7(3) LkSG.",
            "Review effectiveness of remedial measures annually and ad hoc (§7(4) LkSG).",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="lksg_p8_complaints_procedure",
        regulation="lksg",
        article="§ 8 LkSG",
        title="Supply Chain Complaints Procedure",
        applies_when=["Company is directly obligated under §1 LkSG"],
        required_profile_fields=["has_whistleblower_channel"],
        severity="HIGH",
        actions=[
            "Establish an internal complaints procedure (or join an external one) allowing persons to report human-rights and environmental risks and violations in the own business area and at direct suppliers (§8(1) LkSG).",
            "Publish written rules of procedure that are publicly accessible (§8(2) LkSG).",
            "Ensure the persons handling complaints are impartial, independent, not bound by instructions, and sworn to confidentiality (§8(3) LkSG).",
            "Publish clear, understandable information on accessibility, responsibility, and procedure; guarantee confidentiality and protection from retaliation (§8(4) LkSG).",
            "Review effectiveness at least annually and ad hoc (§8(5) LkSG). The channel may be combined with the HinSchG internal reporting channel if both requirement sets are met.",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="lksg_p9_indirect_suppliers",
        regulation="lksg",
        article="§ 9 LkSG",
        title="Duties Regarding Indirect Suppliers",
        applies_when=["Company is directly obligated under §1 LkSG", "Company has substantiated knowledge of a possible violation at an indirect supplier"],
        required_profile_fields=["has_supply_chain_abroad", "supply_chain_countries"],
        severity="MEDIUM",
        actions=[
            "Extend the complaints procedure to cover risks and violations caused by indirect suppliers (§9(1) LkSG).",
            "Upon substantiated knowledge (substantiierte Kenntnis) of a possible violation at an indirect supplier, immediately conduct an ad-hoc risk analysis (§9(3) Nr. 1 LkSG).",
            "Implement appropriate preventive measures towards the party responsible (§9(3) Nr. 2 LkSG).",
            "Create and implement a prevention/termination/minimisation concept and update the Grundsatzerklärung if needed (§9(3) Nr. 3-4 LkSG).",
        ],
        effort_estimate="8-24 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="lksg_p10_1_documentation",
        regulation="lksg",
        article="§ 10 Abs. 1 LkSG",
        title="Continuous Internal Documentation (7 Years)",
        applies_when=["Company is directly obligated under §1 LkSG"],
        required_profile_fields=["has_supply_chain_abroad"],
        severity="MEDIUM",
        actions=[
            "Continuously document the fulfilment of all due diligence duties under §3 LkSG internally (§10(1) LkSG).",
            "Retain the documentation for at least seven years from creation (§10(1) LkSG).",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="lksg_p10_2_annual_report",
        regulation="lksg",
        article="§ 10 Abs. 2, § 12 LkSG",
        title="Annual Public Due Diligence Report",
        applies_when=["Company is directly obligated under §1 LkSG"],
        required_profile_fields=["has_supply_chain_abroad", "has_sustainability_report"],
        severity="HIGH",
        actions=[
            "Prepare an annual report on the fulfilment of due diligence duties in the past financial year (§10(2) LkSG).",
            "Publish the report free of charge on the company website no later than four months after the end of the financial year, for seven years (§10(2) LkSG).",
            "Cover at minimum: identified risks/violations, measures taken (incl. Grundsatzerklärung elements and complaint-triggered measures), effectiveness assessment, and conclusions (§10(2) Nr. 1-4 LkSG).",
            "Submit the report electronically in German via the BAFA portal within the same four-month deadline (§12 LkSG).",
        ],
        effort_estimate="24-60 Stunden",
        needs_expert_review=True,
    ),
]


# ── EnEfG ────────────────────────────────────────────────────────────────────
# Thresholds are based on the average annual total final energy consumption of
# the last three completed calendar years: >7.5 GWh triggers §8 (EnMS/UMS),
# >2.5 GWh triggers §9 (implementation plans) and §§16-17 (waste heat duties).
# Independent of EnEfG, non-SMEs (≥250 employees or >€50M revenue / >€43M
# balance sheet) must conduct energy audits every 4 years under §8 EDL-G.

_ENEFG_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="enefg_p8_energy_management_system",
        regulation="enefg",
        article="§ 8 Abs. 1-2 EnEfG",
        title="Energy or Environmental Management System (>7.5 GWh)",
        applies_when=["Average annual total final energy consumption over the last 3 calendar years exceeds 7.5 GWh"],
        required_profile_fields=["annual_energy_consumption_mwh", "has_energy_management_system"],
        severity="HIGH",
        actions=[
            "Implement an energy management system (ISO 50001) or environmental management system (EMAS) (§8(1) EnEfG).",
            "Meet the deadline: companies over the threshold since 17 Nov 2023 needed the system by 18 July 2025; companies crossing it later have 20 months from that point (§8(2) EnEfG).",
            "Until the system is verified, the EDL-G §8 energy audit obligation continues to apply (§8(2) S. 3 EnEfG).",
        ],
        effort_estimate="80-200 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="enefg_p8_3_enms_requirements",
        regulation="enefg",
        article="§ 8 Abs. 3 EnEfG",
        title="Extended EnMS Requirements (Waste Heat, DIN EN 17463)",
        applies_when=["Company is obligated under §8(1) EnEfG to run an EnMS/UMS"],
        required_profile_fields=["annual_energy_consumption_mwh", "has_energy_management_system"],
        severity="MEDIUM",
        actions=[
            "Record energy inflows/outflows, process temperatures, waste-heat-carrying media (temperatures, heat quantities, constituents), and distinguish technically avoidable from unavoidable waste heat (§8(3) Nr. 1 EnEfG).",
            "Identify and document technically feasible final-energy-saving measures and waste heat recovery/utilisation measures (§8(3) Nr. 2 EnEfG).",
            "Evaluate the economic viability of identified measures per DIN EN 17463 (ValERI) (§8(3) Nr. 3 EnEfG).",
        ],
        effort_estimate="24-60 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="enefg_p9_implementation_plans",
        regulation="enefg",
        article="§ 9 EnEfG",
        title="Publication of Implementation Plans (>2.5 GWh)",
        applies_when=["Average annual total final energy consumption over the last 3 calendar years exceeds 2.5 GWh"],
        required_profile_fields=["annual_energy_consumption_mwh"],
        severity="MEDIUM",
        actions=[
            "Create and publish concrete, feasible implementation plans for all energy-saving measures identified as economic in the EnMS/UMS or energy audit, within 3 years (§9 S. 1 EnEfG).",
            "Apply the economic test: positive net present value per DIN EN 17463 within max. 50% of useful life, capped at 15 years, using BMF depreciation tables (§9 S. 2-3 EnEfG).",
            "Have completeness and correctness of the plans confirmed by certifiers, environmental verifiers, or energy auditors before publication (§9 S. 5 EnEfG).",
            "Be prepared to prove the confirmation to BAFA via its electronic template on request (§9 S. 6 EnEfG).",
        ],
        effort_estimate="24-60 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="enefg_p10_bafa_audit_readiness",
        regulation="enefg",
        article="§ 10 EnEfG",
        title="BAFA Spot-Check Readiness (4-Week Evidence Deadline)",
        applies_when=["Company is obligated under §8 or §9 EnEfG"],
        required_profile_fields=["annual_energy_consumption_mwh"],
        severity="MEDIUM",
        actions=[
            "Maintain evidence per Anlage 2 EnEfG (certificates, implementation plans, confirmations) ready for submission (§10 EnEfG).",
            "Be able to submit the evidence electronically to BAFA within four weeks of a spot-check request (§10 S. 2 EnEfG).",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="enefg_p16_waste_heat_avoidance",
        regulation="enefg",
        article="§ 16 EnEfG",
        title="Waste Heat Avoidance and Reuse (>2.5 GWh)",
        applies_when=["Average annual total final energy consumption over the last 3 calendar years exceeds 2.5 GWh (§16(4) exemption below)"],
        required_profile_fields=["annual_energy_consumption_mwh", "industry"],
        severity="MEDIUM",
        actions=[
            "Avoid waste heat according to the state of the art and reduce it to the technically unavoidable share, where possible and reasonable (§16(1) EnEfG).",
            "Reuse arising waste heat through energy-saving measures, considering uses beyond the individual installation — on the company site and by external third parties (§16(2) EnEfG).",
            "Prefer cascading reuse of recovered waste heat according to its exergy content (§16(2) S. 4 EnEfG).",
            "Check the §16(3) carve-out for installations requiring BImSchG permits with more specific waste heat requirements.",
        ],
        effort_estimate="24-80 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="enefg_p17_waste_heat_platform",
        regulation="enefg",
        article="§ 17 EnEfG",
        title="Waste Heat Platform Reporting (Annual, by 31 March)",
        applies_when=["Average annual total final energy consumption over the last 3 calendar years exceeds 2.5 GWh (§17(4) exemption below)"],
        required_profile_fields=["annual_energy_consumption_mwh"],
        severity="MEDIUM",
        actions=[
            "Report waste heat information (site address, annual heat quantity, max. thermal output, availability profiles, control options, average temperature level) to the Bundesstelle für Energieeffizienz by 31 March each year via the federal electronic template (§17(2) EnEfG).",
            "Update the reported information without undue delay when it changes (§17(2) S. 1 EnEfG).",
            "Provide the same information on request to heat network operators, district heating suppliers, and other potential heat off-takers (§17(1) EnEfG).",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="enefg_edlg_p8_energy_audit",
        regulation="enefg",
        article="§ 8 EDL-G",
        title="Energy Audit Every 4 Years (Non-SME)",
        applies_when=["Company is not an SME (≥250 employees, or >€50M revenue and >€43M balance sheet total)", "No EnMS/UMS exemption applies"],
        required_profile_fields=["employee_count", "annual_revenue_eur", "has_conducted_energy_audit", "has_energy_management_system"],
        severity="HIGH",
        actions=[
            "Conduct an energy audit compliant with DIN EN 16247-1 at least every four years (§8 EDL-G).",
            "Use a qualified, BAFA-registered energy auditor.",
            "Exemption: companies operating a certified ISO 50001 EnMS or EMAS system are exempt from the audit duty (§8(3) EDL-G); companies newly obligated under §8(1) EnEfG are temporarily exempt until their EnMS is verified (§8(2) S. 3 EnEfG).",
        ],
        effort_estimate="24-60 Stunden",
        needs_expert_review=True,
    ),
]


# ── GwG ──────────────────────────────────────────────────────────────────────
# Duties apply to Verpflichtete per §2 GwG (financial services, insurance,
# real estate agents, legal/tax professions, gambling, crypto, goods dealers
# at cash thresholds ≥€10 000 / €2 000 for precious metals). The transparency
# register duty (§20) applies to ALL German legal entities regardless of §2.

_GWG_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="gwg_p4_5_risk_management",
        regulation="gwg",
        article="§§ 4-5 GwG",
        title="AML Risk Management and Documented Risk Analysis",
        applies_when=["Company is an obligated party (Verpflichteter) under §2 GwG"],
        required_profile_fields=["is_aml_obligated_sector", "industry"],
        severity="CRITICAL",
        actions=[
            "Establish an effective risk management system covering money laundering and terrorist financing risks, with responsibility assigned to a management board member (§4 GwG).",
            "Create a documented risk analysis of the business-specific ML/TF risks, considering the risk factors in Anlagen 1 und 2 GwG (§5(1) GwG).",
            "Review and update the risk analysis regularly, at minimum annually, and have it approved by management (§5(2) GwG).",
            "Provide the risk analysis to the supervisory authority on request (§5(2) GwG).",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gwg_p6_internal_safeguards",
        regulation="gwg",
        article="§ 6 GwG",
        title="Internal AML Safeguards",
        applies_when=["Company is an obligated party under §2 GwG"],
        required_profile_fields=["is_aml_obligated_sector", "employee_count"],
        severity="HIGH",
        actions=[
            "Implement internal policies, procedures, and controls proportionate to the risk analysis (§6(1) GwG).",
            "Verify the reliability (Zuverlässigkeit) of employees in AML-relevant roles (§6(2) Nr. 5 GwG).",
            "Train employees regularly on ML/TF typologies, current methods, and applicable duties (§6(2) Nr. 6 GwG).",
            "Provide a channel allowing employees to report GwG violations confidentially (§6(5) GwG) — may be combined with the HinSchG internal reporting channel.",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gwg_p7_aml_officer",
        regulation="gwg",
        article="§ 7 GwG",
        title="Money Laundering Officer (Geldwäschebeauftragter)",
        applies_when=["Company is a financial-sector obligated party under §2 GwG", "Or the supervisory authority has ordered an appointment"],
        required_profile_fields=["is_aml_obligated_sector", "industry"],
        severity="HIGH",
        actions=[
            "Appoint a Geldwäschebeauftragter at management level and a deputy (§7(1) GwG) — mandatory for financial-sector obligated parties; other sectors upon supervisory order (§7(3) GwG).",
            "Notify the supervisory authority of the appointment and any dismissal in advance (§7(4) GwG).",
            "Ensure the officer has sufficient authority, resources, and unrestricted access to all relevant information (§7(5) GwG).",
            "Protect the officer from discrimination due to the exercise of their duties (§7(7) GwG).",
        ],
        effort_estimate="8-24 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gwg_p10_customer_due_diligence",
        regulation="gwg",
        article="§§ 10-13 GwG",
        title="Customer Due Diligence (KYC)",
        applies_when=["Company is an obligated party under §2 GwG", "Business relationship is established, or transaction thresholds are met (goods dealers: cash ≥€10 000, precious metals ≥€2 000)"],
        required_profile_fields=["is_aml_obligated_sector", "industry"],
        severity="CRITICAL",
        actions=[
            "Identify the contracting party and any person acting on their behalf before establishing a business relationship or executing a threshold transaction (§10(1) Nr. 1, §11 GwG).",
            "Determine whether a wirtschaftlich Berechtigter (beneficial owner) exists and identify them (§10(1) Nr. 2, §11(5) GwG).",
            "Establish the purpose and intended nature of the business relationship where not evident (§10(1) Nr. 3 GwG).",
            "Continuously monitor the business relationship and keep customer data current (§10(1) Nr. 5 GwG).",
            "If due diligence cannot be completed: do not establish the relationship or execute the transaction, and assess a suspicious activity report (§10(9) GwG).",
        ],
        effort_estimate="24-60 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gwg_p15_enhanced_due_diligence",
        regulation="gwg",
        article="§ 15 GwG",
        title="Enhanced Due Diligence (PEPs, High-Risk Countries)",
        applies_when=["Company is an obligated party under §2 GwG", "Higher risk is identified: politically exposed persons, high-risk third countries, or unusual transactions"],
        required_profile_fields=["is_aml_obligated_sector"],
        severity="HIGH",
        actions=[
            "Screen contracting parties and beneficial owners against PEP status; treat PEP relationships as higher-risk (§15(3) Nr. 1 GwG).",
            "Apply enhanced measures for business involving high-risk third countries per EU list (§15(3) Nr. 2, §15(5a) GwG).",
            "Obtain senior management approval before establishing or continuing higher-risk relationships (§15(4) GwG).",
            "Investigate background and purpose of unusual or suspicious transactions and intensify monitoring (§15(6) GwG).",
        ],
        effort_estimate="8-24 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gwg_p8_records",
        regulation="gwg",
        article="§ 8 GwG",
        title="AML Record-Keeping (5 Years)",
        applies_when=["Company is an obligated party under §2 GwG"],
        required_profile_fields=["is_aml_obligated_sector", "has_data_retention_policy"],
        severity="MEDIUM",
        actions=[
            "Record and retain all data collected under the due diligence duties, including identification documents and transaction records (§8(1)-(2) GwG).",
            "Retain records for five years after the end of the business relationship or transaction, then delete without undue delay (§8(4) GwG).",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="gwg_p43_45_suspicious_reports",
        regulation="gwg",
        article="§§ 43, 45 GwG",
        title="Suspicious Activity Reports and goAML Registration",
        applies_when=["Company is an obligated party under §2 GwG"],
        required_profile_fields=["is_aml_obligated_sector"],
        severity="CRITICAL",
        actions=[
            "Report facts indicating possible money laundering or terrorist financing to the FIU (Zentralstelle für Finanztransaktionsuntersuchungen) without undue delay, regardless of amount (§43(1) GwG).",
            "Register electronically with the FIU's goAML portal — registration is mandatory for all obligated parties independent of ever filing a report (§45(1) GwG).",
            "Do not execute the transaction until FIU consent or expiry of the waiting period (§46 GwG).",
            "Observe the tipping-off prohibition: the customer must not be informed of a filed report (§47 GwG).",
        ],
        effort_estimate="4-16 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="gwg_p20_transparency_register",
        regulation="gwg",
        article="§ 20 GwG",
        title="Transparency Register Notification (All Legal Entities)",
        applies_when=["Company is a German legal entity (GmbH, AG, etc.) — applies regardless of §2 GwG obligated-party status"],
        required_profile_fields=["company_name"],
        severity="HIGH",
        actions=[
            "Determine the wirtschaftlich Berechtigte (beneficial owners: natural persons holding >25% capital, voting rights, or comparable control) (§3 GwG).",
            "Notify their data (name, birth date, residence, nature and extent of interest, nationality) to the Transparenzregister without undue delay (§20(1) GwG).",
            "Keep the register entry current — update on every change in beneficial ownership (§20(1) GwG).",
            "Note: the former Mitteilungsfiktion was abolished in 2021 — an entry in the Handelsregister no longer substitutes the notification.",
        ],
        effort_estimate="2-8 Stunden",
        needs_expert_review=False,
    ),
]


# ── TTDSG ────────────────────────────────────────────────────────────────────
# Renamed TDDDG in May 2024 (Digitale-Dienste-Gesetz reform) — section numbers
# unchanged; the KB and enum keep the ttdsg key. For typical SMEs the relevant
# duties are the §25 endpoint/cookie consent rules; §§19-24 target telco and
# digital service providers specifically.

_TTDSG_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="ttdsg_p25_endpoint_consent",
        regulation="ttdsg",
        article="§ 25 Abs. 1 TTDSG",
        title="Consent Before Storing or Accessing Data on End Devices",
        applies_when=["Company operates a website or app that stores or reads information on user devices (cookies, pixels, localStorage, fingerprinting)"],
        required_profile_fields=["has_website", "has_cookie_banner"],
        severity="HIGH",
        actions=[
            "Obtain consent BEFORE storing information on or reading information from the user's end device — this covers cookies, tracking pixels, localStorage, and device fingerprinting regardless of whether personal data is involved (§25(1) TTDSG).",
            "Base the consent on clear and comprehensive information, meeting the GDPR consent standard (freely given, specific, informed, unambiguous) (§25(1) S. 2 TTDSG i.V.m. Art. 4 Nr. 11, Art. 7 DSGVO).",
            "Block all non-essential cookies and scripts technically until consent is given — loading them before the banner interaction violates §25(1).",
            "Log and store consent decisions so they can be demonstrated (Art. 7(1) DSGVO).",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="ttdsg_p25_2_exemption_scope",
        regulation="ttdsg",
        article="§ 25 Abs. 2 TTDSG",
        title="Correct Use of the Strictly-Necessary Exemption",
        applies_when=["Company relies on consent-free cookies or storage for parts of its website or app"],
        required_profile_fields=["has_website", "has_cookie_banner"],
        severity="MEDIUM",
        actions=[
            "Classify each cookie/storage item: consent-free only if solely needed for message transmission (§25(2) Nr. 1) or strictly necessary to provide a digital service the user explicitly requested (§25(2) Nr. 2 TTDSG).",
            "Typical exempt examples: session cookies for shopping carts, login state, consent storage itself, load balancing. NOT exempt: analytics, marketing, A/B testing, reach measurement.",
            "Document the classification per cookie so the exemption reasoning is auditable.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="ttdsg_banner_design_dsk",
        regulation="ttdsg",
        article="§ 25 TTDSG / DSK OH Telemedien",
        title="Compliant Cookie Banner Design",
        applies_when=["Company uses a consent banner to satisfy §25(1) TTDSG"],
        required_profile_fields=["has_website", "has_cookie_banner"],
        severity="MEDIUM",
        actions=[
            "Offer 'reject all' with the same prominence and effort as 'accept all' on the first banner layer — hiding rejection behind a second layer invalidates the consent per DSK guidance (Orientierungshilfe Telemedien).",
            "Do not use dark patterns: no pre-ticked boxes, no misleading button colors or wording, no consent walls for services that work without tracking.",
            "Enable withdrawal of consent at any time as easily as it was given (Art. 7(3) DSGVO), e.g. a persistent floating icon or footer link.",
            "Ensure continued site use is possible without consent to non-essential processing.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="ttdsg_cookie_policy_transparency",
        regulation="ttdsg",
        article="§ 25 TTDSG i.V.m. Art. 13 DSGVO",
        title="Cookie Policy and Transparency",
        applies_when=["Company operates a website that uses cookies or similar technologies"],
        required_profile_fields=["has_website", "has_cookie_policy"],
        severity="MEDIUM",
        actions=[
            "Maintain a cookie policy (standalone or within the Datenschutzerklärung) naming each cookie/technology, its provider, purpose, storage duration, and legal basis.",
            "Keep the policy synchronized with what the website actually sets — audit deployed cookies regularly (e.g. after adding new tools).",
            "Name third-country transfers triggered by third-party cookies (e.g. US-based analytics) including the transfer mechanism (Art. 13(1)(f) DSGVO).",
        ],
        effort_estimate="2-6 Stunden",
        needs_expert_review=False,
    ),
]


# ── CSRD ─────────────────────────────────────────────────────────────────────
# Applies per §check_csrd threshold logic (2 of 3: >250 employees, >€50M
# revenue, >€25M balance sheet; or listed). Sources: Directive (EU) 2022/2464
# (Art. 1, inserting Art. 19a/29a into the Accounting Directive 2013/34/EU) and
# Commission Delegated Regulation (EU) 2023/2772 (ESRS 1/2 + topical standards
# E1/S1/S2/G1), per data/regulations/csrd/csrd_directive_de.txt and
# esrs_sector_standards_expanded.txt.

_CSRD_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="csrd_art19a_sustainability_statement",
        regulation="csrd",
        article="Art. 19a/29a Bilanzrichtlinie (eingefügt durch Art. 1 RL (EU) 2022/2464)",
        title="Sustainability Statement in the Management Report",
        applies_when=["Company meets 2 of 3 CSRD size criteria (>250 employees, >€50M revenue, >€25M balance sheet) or is listed on an EU-regulated market"],
        required_profile_fields=["employee_count", "annual_revenue_eur", "balance_sheet_total_eur", "is_listed_company"],
        severity="CRITICAL",
        actions=[
            "Prepare a sustainability statement as a distinct, clearly identifiable section of the management report (Lagebericht), not a separate voluntary report.",
            "File the sustainability statement with the German Federal Gazette (Bundesanzeiger) alongside the financial statements, within the same statutory deadline.",
            "Determine the correct reporting wave and first reporting year (Wave 1/2/3) via the rule engine's CSRD threshold check — note the ongoing Omnibus threshold uncertainty flagged there.",
            "Consult legal/audit counsel given the actively changing scope (Omnibus simplification package, Stop-the-Clock Directive (EU) 2025/794).",
        ],
        effort_estimate="80-200 Stunden (erstmalige Berichtserstellung)",
        needs_expert_review=True,
    ),
    Obligation(
        id="csrd_esrs1_double_materiality",
        regulation="csrd",
        article="ESRS 1, Kapitel 3 (Doppelte Wesentlichkeit)",
        title="Double Materiality Assessment (DMA)",
        applies_when=["CSRD applies to the company — DMA is the mandatory first step before determining which ESRS topics must be disclosed"],
        required_profile_fields=["has_sustainability_report"],
        severity="CRITICAL",
        actions=[
            "Systematically identify sustainability matters and assess each against both materiality dimensions: financial materiality (inside-out — risk/opportunity to cash flows, performance, cost of capital) and impact materiality (outside-in — the company's actual/potential impact on people and the environment).",
            "Consult stakeholders (employees, affected communities, value chain partners, users of sustainability reporting) as part of the assessment process.",
            "Document the assessment methodology and results; disclose which topics are material and which are not, with rationale for exclusions.",
            "Review and update the DMA at least annually — external assurance of the DMA process and results is required from the first reporting year (2024 for large PIEs).",
        ],
        effort_estimate="40-100 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="csrd_esrs1_value_chain_scope",
        regulation="csrd",
        article="ESRS 1 (Value Chain Scope)",
        title="Full Value Chain Reporting Scope",
        applies_when=["CSRD applies to the company"],
        required_profile_fields=["has_sustainability_report", "has_supply_chain_abroad"],
        severity="HIGH",
        actions=[
            "Map the full value chain: upstream (suppliers), own operations (all consolidated entities), and downstream (distributors, retailers, product use and end-of-life).",
            "Apply the proportionality principle — extend data collection into the value chain in proportion to materiality and practical feasibility; use estimates, sector averages, or proxy data where primary data is unavailable, with the estimation methodology disclosed.",
            "Use the transitional relief for Scope 3 GHG emissions and other value chain datapoints in the first reporting years while building data collection capability.",
            "For German companies with a supply chain also in scope of LkSG: align data collection to avoid duplicating supplier due diligence effort.",
        ],
        effort_estimate="40-80 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="csrd_esrs_e1_governance_transition",
        regulation="csrd",
        article="ESRS E1 (Governance & Transition Plan)",
        title="Climate Governance and Transition Plan Disclosures",
        applies_when=["Climate change is a material topic per the DMA (typically material for most large companies)"],
        required_profile_fields=["has_sustainability_report"],
        severity="HIGH",
        actions=[
            "Disclose board-level oversight of climate risk (responsible committee/board member, briefing frequency, link to executive remuneration) and management roles for day-to-day climate risk management — this is a mandatory ESRS 2 cross-cutting requirement regardless of materiality outcome.",
            "Conduct climate scenario analysis covering physical and transition risks, including at minimum a 1.5°C-aligned scenario and a current-policies scenario, across short/medium/long-term horizons.",
            "Disclose whether a climate transition plan has been adopted; if so, include decarbonisation targets (2030/2050), CapEx/OpEx allocated to the transition, locked-in emissions, and fossil fuel exposure — cross-reference EU Taxonomy alignment.",
            "If no transition plan exists, disclose that fact plus a timeline and process for developing one.",
        ],
        effort_estimate="40-100 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="csrd_esrs_e1_ghg_physical_risk",
        regulation="csrd",
        article="ESRS E1 (GHG Emissions & Physical Risk)",
        title="GHG Emissions (Scope 1-3) and Physical Climate Risk",
        applies_when=["Climate change is a material topic per the DMA"],
        required_profile_fields=["has_sustainability_report"],
        severity="HIGH",
        actions=[
            "Disclose Scope 1 (direct) and Scope 2 (purchased energy, both market- and location-based) GHG emissions per the GHG Protocol methodology, by gas and by category.",
            "Identify the most material Scope 3 (value chain) categories via the DMA and disclose them; full 15-category Scope 3 reporting is required from year 3, with phase-in relief in earlier years.",
            "Disclose at least one sector-relevant GHG intensity metric, and report gross/net emissions separately — carbon offsets must not be presented as emissions reductions.",
            "Assess acute (extreme weather) and chronic (long-term climate pattern shift) physical risks to assets, operations, and supply chain, including estimated financial impact and adaptation measures implemented.",
        ],
        effort_estimate="40-100 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="csrd_esrs_s1_workforce",
        regulation="csrd",
        article="ESRS S1 (Own Workforce)",
        title="Own Workforce Disclosures (Headcount, Conditions, Equal Treatment)",
        applies_when=["Own workforce is a material topic per the DMA (typically material for all employers)"],
        required_profile_fields=["has_sustainability_report", "employee_count"],
        severity="HIGH",
        actions=[
            "Disclose headcount by employment type, working time, gender, and country, plus non-employee workers whose work the company directs.",
            "Disclose the gender pay gap (median hourly pay ratio), collective bargaining coverage, employee turnover, and average training hours per employee.",
            "Disclose health and safety performance: work-related fatalities, recordable accidents, lost time injury rate (LTIR), and occupational disease cases — align with DGUV/Berufsgenossenschaft data where available.",
            "Disclose equal treatment and non-discrimination policies, pay equity measures, and parental leave return-to-work rates by gender; align with existing AGG §12/§13 preventive measures and complaints procedure for consistency.",
        ],
        effort_estimate="40-80 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="csrd_esrs_s2_value_chain_workers",
        regulation="csrd",
        article="ESRS S2 (Value Chain Workers)",
        title="Value Chain Worker Rights Due Diligence",
        applies_when=["Value chain worker rights are material per the DMA (typically manufacturing, textiles, agriculture, electronics)"],
        required_profile_fields=["has_sustainability_report", "has_supply_chain_abroad"],
        severity="HIGH",
        actions=[
            "Disclose due diligence policies covering child labour, forced labour, freedom of association, safe working conditions, and adequate wages in the value chain (upstream and downstream).",
            "Describe the risk assessment methodology (questionnaires, audits, certification schemes) and how supplier compliance is monitored and enforced.",
            "Describe grievance mechanisms accessible to value chain workers and the remediation process for identified violations, including escalation and last-resort supplier termination.",
            "For companies also in scope of LkSG (≥1,000 employees): integrate existing LkSG risk analysis and complaints-procedure evidence into ESRS S2 disclosures to avoid duplicate effort.",
        ],
        effort_estimate="24-60 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="csrd_esrs_g1_business_conduct",
        regulation="csrd",
        article="ESRS G1 (Business Conduct)",
        title="Anti-Corruption, Anti-Bribery, and Fair Competition Disclosures",
        applies_when=["Business conduct is material per the DMA (typically material for all large companies)"],
        required_profile_fields=["has_sustainability_report"],
        severity="MEDIUM",
        actions=[
            "Disclose anti-corruption and anti-bribery policies, the reporting channel for suspected corruption (may reuse the HinSchG whistleblower channel), and confirmed incidents/sanctions during the reporting period.",
            "Disclose lobbying activities, political contributions, and fair-competition compliance including any confirmed anti-competitive-behaviour incidents.",
            "Disclose supplier payment practices (average payment period, share of invoices paid beyond agreed terms) — particularly relevant given the EU Late Payments Regulation's 30-day B2B payment term.",
            "Cross-reference existing GwG AML compliance and HinSchG whistleblower channel documentation where relevant to anti-corruption governance.",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="csrd_assurance",
        regulation="csrd",
        article="Bilanzrichtlinie (Assurance) / UDRG",
        title="External Assurance of the Sustainability Statement",
        applies_when=["CSRD applies to the company"],
        required_profile_fields=["has_sustainability_report"],
        severity="CRITICAL",
        actions=[
            "Engage a statutory auditor or independent assurance service provider for limited assurance of the sustainability statement from the first reporting period (2024 for large PIEs).",
            "Prepare for the transition to reasonable assurance from reporting periods starting 1 January 2028 (or earlier if formally adopted by the EU Commission).",
            "Ensure the assurance engagement covers ESRS compliance, the double materiality assessment process, and the tagging of information in the European Single Electronic Format (ESEF/XBRL).",
            "Be aware that non-compliant or materially misleading sustainability reporting is enforced under the same regime as financial reporting violations (Deutsche Prüfstelle für Rechnungslegung / BaFin for listed companies), per the German UDRG transposition.",
        ],
        effort_estimate="24-60 Stunden (Koordination mit Prüfer)",
        needs_expert_review=True,
    ),
    Obligation(
        id="csrd_phase_in",
        regulation="csrd",
        article="ESRS 1 (Phase-in/Übergangsbestimmungen)",
        title="First-Year Reporting Relief (Phase-In Provisions)",
        applies_when=["Company is reporting under CSRD for the first time (reporting periods 2024, 2025, or 2026)"],
        required_profile_fields=["has_sustainability_report"],
        severity="LOW",
        actions=[
            "Identify which phase-in reliefs apply: Scope 3 GHG category omissions with disclosed timeline, ESRS E4 (biodiversity) omission in year 1, and value chain datapoint reliefs under ESRS S1/S2/S3/S4.",
            "For companies with fewer than 750 employees: apply the additional ESRS S1 (employee data) phase-in relief available in years 1-2.",
            "Plan for full Scope 3 GHG disclosure across all 15 categories from year 3 of reporting.",
            "For SME suppliers being asked for data by large customers: reference the EFRAG VSME (Voluntary SME) standard as the appropriate simplified disclosure level rather than full ESRS.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
]


# ── EU AI Act ────────────────────────────────────────────────────────────────
# Source: Regulation (EU) 2024/1689, per threshold_engine.py::check_ai_act
# (verified) and data/regulations/eu_ai_act/eu_ai_act_expanded.txt. Applies to
# any company that develops (provider) or uses (deployer) AI systems in the EU
# — no size threshold (Art. 2(1) EU AI Act).

_AI_ACT_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="ai_act_art5_prohibited_practices",
        regulation="eu_ai_act",
        article="Art. 5(1)(a)-(e) EU AI Act",
        title="Prohibited AI Practices",
        applies_when=["Company develops, procures, or deploys any AI system — applies regardless of sector or size, in force since 2 Feb 2025"],
        required_profile_fields=["uses_ai_systems"],
        severity="CRITICAL",
        actions=[
            "Ensure no AI system uses subliminal, manipulative, or deceptive techniques that materially distort a person's behaviour and cause significant harm (Art. 5(1)(a)).",
            "Ensure no AI system exploits vulnerabilities due to age, disability, or socioeconomic situation (Art. 5(1)(b)).",
            "Ensure no AI system performs biometric categorisation to infer race, political opinion, trade union membership, religious belief, or sexual orientation (Art. 5(1)(c)).",
            "Do not use real-time remote biometric identification in publicly accessible spaces, or social scoring systems — these are prohibited outright with narrow law-enforcement exceptions only (Art. 5(1)(d)-(e)).",
        ],
        effort_estimate="4-8 Stunden (Prüfung bestehender/geplanter KI-Systeme)",
        needs_expert_review=True,
    ),
    Obligation(
        id="ai_act_art6_annex3_classification",
        regulation="eu_ai_act",
        article="Art. 6(1)-(2) i.V.m. Anhang III EU AI Act",
        title="High-Risk AI System Classification",
        applies_when=["Company develops, procures, or deploys an AI system whose classification (high-risk vs. limited/minimal risk) is not yet confirmed"],
        required_profile_fields=["uses_ai_systems", "ai_systems_are_high_risk"],
        severity="HIGH",
        actions=[
            "Classify each AI system against Annex III: employment/HR decisions, creditworthiness assessment, education/training access, law enforcement, migration, critical infrastructure, and safety components are always high-risk, independent of the perceived actual impact.",
            "For AI systems used as a safety component of a product subject to third-party conformity assessment, treat as high-risk per Art. 6(1).",
            "Document the classification rationale — this determines which downstream obligations (Art. 9-17 for providers, Art. 26 for deployers) apply.",
            "Re-assess classification whenever the AI system's purpose or deployment context changes materially.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="ai_act_art26_deployer_use_and_oversight",
        regulation="eu_ai_act",
        article="Art. 26(1) EU AI Act",
        title="Deployer Obligations — Use per Instructions and Human Oversight",
        applies_when=["Company deploys a high-risk AI system developed by another party"],
        required_profile_fields=["uses_ai_systems", "ai_systems_are_high_risk"],
        severity="HIGH",
        actions=[
            "Use the high-risk AI system strictly in accordance with the provider's instructions for use (Art. 26(1)).",
            "Assign a natural person with the competence, training, and authority to provide human oversight of the system during use.",
            "Monitor the operation of the AI system and suspend use if it presents a risk to health, safety, or fundamental rights.",
            "Retain the technical documentation and instructions for use provided by the AI system's provider.",
        ],
        effort_estimate="8-16 Stunden (Prozess-Einrichtung)",
        needs_expert_review=False,
    ),
    Obligation(
        id="ai_act_art26_5_log_retention",
        regulation="eu_ai_act",
        article="Art. 26(5) EU AI Act",
        title="Retention of Automatically Generated Logs (≥6 Months)",
        applies_when=["Company deploys a high-risk AI system that generates automatic logs under its control"],
        required_profile_fields=["uses_ai_systems", "ai_systems_are_high_risk"],
        severity="MEDIUM",
        actions=[
            "Retain logs automatically generated by the high-risk AI system for at least six months, unless a longer period is required under other applicable law (e.g. GDPR, sector-specific rules).",
            "Ensure logs are accessible for audit and incident investigation purposes.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="ai_act_art26_6_inform_workers",
        regulation="eu_ai_act",
        article="Art. 26(6) EU AI Act",
        title="Inform Workers' Representatives Before Deployment",
        applies_when=["Company is an employer deploying a high-risk AI system that affects workers"],
        required_profile_fields=["uses_ai_systems", "ai_systems_are_high_risk"],
        severity="HIGH",
        actions=[
            "Inform workers' representatives and affected workers that they will be subject to the use of the high-risk AI system, before it is put into use in the workplace.",
            "Coordinate with the Betriebsrat (works council) where one exists — this obligation intersects with German co-determination (Mitbestimmung) requirements under BetrVG §87.",
        ],
        effort_estimate="4-8 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="ai_act_art26_9_fria",
        regulation="eu_ai_act",
        article="Art. 26(9) EU AI Act",
        title="Fundamental Rights Impact Assessment (Public Sector / HR Context)",
        applies_when=["Company is a public-sector body, or deploys high-risk AI in HR/employment decision-making"],
        required_profile_fields=["uses_ai_systems", "ai_systems_are_high_risk"],
        severity="HIGH",
        actions=[
            "Conduct a fundamental rights impact assessment (FRIA) before deploying the high-risk AI system, covering the processes it will be used in, the categories of affected persons, specific risks of harm, and mitigation measures.",
            "Notify the market surveillance authority of the FRIA outcome where required.",
            "Review and update the FRIA when the deployment context changes materially.",
        ],
        effort_estimate="16-32 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="ai_act_art50_1_chatbot_transparency",
        regulation="eu_ai_act",
        article="Art. 50(1) EU AI Act",
        title="Transparency — AI Systems Interacting With Humans",
        applies_when=["Company deploys an AI system that interacts directly with natural persons (e.g. chatbots, voice assistants)"],
        required_profile_fields=["uses_ai_systems"],
        severity="MEDIUM",
        actions=[
            "Ensure the AI system discloses to users that they are interacting with an AI system, unless this is obvious from the circumstances or context of use.",
            "Provide this disclosure in a clear and distinguishable manner at the latest at the time of first interaction.",
        ],
        effort_estimate="2-8 Stunden",
        needs_expert_review=False,
    ),
    Obligation(
        id="ai_act_art50_4_synthetic_content",
        regulation="eu_ai_act",
        article="Art. 50(4) EU AI Act",
        title="Transparency — AI-Generated Synthetic Content",
        applies_when=["Company deploys AI to generate or manipulate image, audio, or video content (synthetic content / deepfakes)"],
        required_profile_fields=["uses_ai_systems"],
        severity="MEDIUM",
        actions=[
            "Disclose that generated or manipulated content has been artificially created or altered (AI origin), in a clear and machine-readable manner where technically feasible.",
            "Apply this to marketing, communications, and any published synthetic media — exceptions exist for evidently artistic, satirical, or fictional content with appropriate disclosure.",
        ],
        effort_estimate="2-8 Stunden",
        needs_expert_review=False,
    ),
]


# ── EU Data Act ──────────────────────────────────────────────────────────────
# Source: Regulation (EU) 2023/2854, applicable from 12 September 2025, per
# threshold_engine.py::check_eu_data_act (verified) and
# data/regulations/eu_data_act/eu_data_act_de.txt (Art. 3-6, 13, 23, 25 read
# directly from the fetched source text).

_EU_DATA_ACT_OBLIGATIONS: list[Obligation] = [
    Obligation(
        id="data_act_art3_access_by_design",
        regulation="eu_data_act",
        article="Art. 3 EU Data Act",
        title="Connected Products Designed for Data Access",
        applies_when=["Company manufactures connected (IoT) products placed on the EU market"],
        required_profile_fields=["produces_connected_products"],
        severity="HIGH",
        actions=[
            "Design and manufacture connected products so that product data and related service data — including the metadata needed to interpret and use them — are accessible to the user by default, easily, securely, free of charge, in a comprehensive, structured, commonly used, and machine-readable format (Art. 3(1)).",
            "Before a purchase, rental, or lease contract, inform the user of the type, format, and estimated volume of data the product can generate, whether it is generated continuously/in real time, and how the user can access, retrieve, or delete it (Art. 3(2)).",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="data_act_art4_user_access_on_request",
        regulation="eu_data_act",
        article="Art. 4 EU Data Act",
        title="Data Access on User Request",
        applies_when=["Company is a data holder for a connected product or related service where the user cannot access data directly from the product"],
        required_profile_fields=["produces_connected_products"],
        severity="HIGH",
        actions=[
            "Where the user cannot access data directly from the connected product or related service, make readily available data (including necessary metadata) available to the user without undue delay, free of charge, in a comprehensive, commonly used, machine-readable format, on simple electronic request.",
            "Provide the data in the same quality as available to the data holder, continuously and in real time where technically feasible.",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="data_act_art5_6_third_party_sharing",
        regulation="eu_data_act",
        article="Art. 5-6 EU Data Act",
        title="Third-Party Data Sharing on User Instruction / No Exclusive Use",
        applies_when=["Company is a data holder for a connected product or related service"],
        required_profile_fields=["produces_connected_products"],
        severity="HIGH",
        actions=[
            "On a user's request, make readily available data and necessary metadata available to a designated third party without undue delay, free of charge to the user, in the same quality available to the data holder (Art. 5(1)).",
            "Do not prevent, discourage, or restrict the user's own use of the data for lawful purposes, and do not use the data to derive insights that undermine the user's commercial position (no exclusive-use restriction, Art. 6).",
            "Ensure any third party receiving data under Art. 5 processes it only for the purposes and conditions agreed with the user and deletes it once no longer needed (Art. 6 obligations of the receiving third party).",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="data_act_art13_unfair_contract_terms",
        regulation="eu_data_act",
        article="Art. 13 EU Data Act",
        title="Unfair Data-Sharing Contract Terms",
        applies_when=["Company is party to a B2B contract governing data access, use, liability, or remedies for breach of data-related obligations"],
        required_profile_fields=["produces_connected_products", "provides_data_processing_services"],
        severity="MEDIUM",
        actions=[
            "Review data-sharing contract clauses unilaterally imposed on another company — such clauses are not binding on the other company if they are unfair (Art. 13(1)).",
            "Ensure contract clauses do not unreasonably deviate from good commercial practice or breach good faith and fair dealing (the statutory unfairness test).",
            "Note that clauses reflecting mandatory EU law, or default rules that would apply absent a contrary agreement, are not considered unfair (Art. 13(2)) — legal review recommended for standard-form data-sharing agreements.",
        ],
        effort_estimate="8-16 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="data_act_art23_switching_obstacles",
        regulation="eu_data_act",
        article="Art. 23 EU Data Act",
        title="Removal of Cloud/Data-Processing Switching Obstacles",
        applies_when=["Company provides data processing services (cloud, edge, or similar)"],
        required_profile_fields=["provides_data_processing_services"],
        severity="HIGH",
        actions=[
            "Take the measures required under Art. 25-27, 29, and 30 to enable customers to switch to another provider of the same service type, or to on-premises ICT infrastructure, or to use multiple providers concurrently.",
            "Do not impose pre-commercial, commercial, technical, contractual, or organisational obstacles that hinder customers from switching — remove any such obstacles that currently exist.",
        ],
        effort_estimate="24-60 Stunden",
        needs_expert_review=True,
    ),
    Obligation(
        id="data_act_art25_switching_contract",
        regulation="eu_data_act",
        article="Art. 25 EU Data Act",
        title="Switching Contract Clauses, 30-Business-Day Limit, Fee Phase-Out",
        applies_when=["Company provides data processing services (cloud, edge, or similar)"],
        required_profile_fields=["provides_data_processing_services"],
        severity="HIGH",
        actions=[
            "Set out customer switching rights and provider switching obligations clearly in a written contract, provided to the customer before signature in a storable and reproducible form.",
            "Enable the switching process to complete within a maximum of 30 business days of the customer's request, per the contractually specified transitional period.",
            "Phase out and eliminate switching fees by 12 September 2027; until then, any switching charges must not exceed the provider's actual costs incurred.",
        ],
        effort_estimate="16-40 Stunden",
        needs_expert_review=True,
    ),
]


# ── Master registry ───────────────────────────────────────────────────────────

OBLIGATION_REGISTRY: dict[str, list[Obligation]] = {
    "gdpr_dsgvo":    _GDPR_OBLIGATIONS,
    "hinschg":       _HINSCHG_OBLIGATIONS,
    "nis2":          _NIS2_OBLIGATIONS,
    "agg":           _AGG_OBLIGATIONS,
    "milog":         _MILOG_OBLIGATIONS,
    "bdsg":          _BDSG_OBLIGATIONS,
    "workplace_law": _WORKPLACE_LAW_OBLIGATIONS,
    "lksg":          _LKSG_OBLIGATIONS,
    "enefg":         _ENEFG_OBLIGATIONS,
    "gwg":           _GWG_OBLIGATIONS,
    "ttdsg":         _TTDSG_OBLIGATIONS,
    "csrd":          _CSRD_OBLIGATIONS,
    "eu_ai_act":     _AI_ACT_OBLIGATIONS,
    "eu_data_act":   _EU_DATA_ACT_OBLIGATIONS,
}


def get_obligations(regulation: str) -> list[Obligation]:
    """Return all obligations for a given regulation key."""
    return OBLIGATION_REGISTRY.get(regulation, [])


def get_obligation_by_id(obligation_id: str) -> Obligation | None:
    """Look up a single obligation by its id across all regulations."""
    for obligations in OBLIGATION_REGISTRY.values():
        for ob in obligations:
            if ob.id == obligation_id:
                return ob
    return None


def obligations_for_profile(regulation: str, profile: "CompanyProfile") -> list[Obligation]:
    """
    Return obligations for a regulation that are relevant to the given profile.

    Currently returns all obligations for the regulation — future iterations
    may filter by applies_when conditions deterministically.
    """
    from models.company_profile import CompanyProfile  # noqa: F401 (type hint only)
    return get_obligations(regulation)
