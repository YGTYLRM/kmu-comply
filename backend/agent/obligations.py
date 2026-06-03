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
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.company_profile import CompanyProfile

OBLIGATIONS_VERSION = "v1.0.0"


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


# ── Master registry ───────────────────────────────────────────────────────────

OBLIGATION_REGISTRY: dict[str, list[Obligation]] = {
    "gdpr_dsgvo":    _GDPR_OBLIGATIONS,
    "hinschg":       _HINSCHG_OBLIGATIONS,
    "nis2":          _NIS2_OBLIGATIONS,
    "agg":           _AGG_OBLIGATIONS,
    "milog":         _MILOG_OBLIGATIONS,
    "bdsg":          _BDSG_OBLIGATIONS,
    "workplace_law": _WORKPLACE_LAW_OBLIGATIONS,
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
