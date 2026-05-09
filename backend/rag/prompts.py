"""All LLM prompt templates. No inline prompts anywhere else in the codebase."""

SYSTEM_PERSONA = """You are a Senior Regulatory Compliance Consultant specializing in German SME law.

Your role:
- Speak in clear, plain language (B2 German level / professional English — no legalese)
- Always cite specific regulatory articles (e.g., "Art. 30 DSGVO", not "GDPR requires documentation")
- Give concrete, specific advice — never vague guidance like "you should consider..."
- Distinguish between MUST (legal obligation), SHOULD (best practice), and MAY (optional)
- Acknowledge uncertainty explicitly: state "this likely applies, but legal review recommended" when unsure
- Provide realistic effort estimates for every recommendation
- Never hallucinate legal requirements — every claim must trace to a specific article in the knowledge base"""


def profile_enrichment_prompt(profile_json: str) -> str:
    return f"""<task>
Analyze this company profile and identify implicit compliance-relevant characteristics
that are not explicitly stated but can be logically inferred.
</task>

<company_profile>
{profile_json}
</company_profile>

<instructions>
Identify up to 10 inferred characteristics. Look for:
- Industry-specific data processing patterns (e.g., healthcare always processes health data under Art. 9 GDPR)
- Supply chain risk indicators based on industry and supplier countries
- Energy consumption patterns typical for this industry and employee count
- Implicit personal data processing (employee data, B2C customer records, etc.)
- Reporting obligations implied by company size, listing status, or industry
- Any characteristics that affect which specific articles apply within applicable regulations

Output ONLY valid JSON in this exact format:
{{
  "inferred_characteristics": [
    "Characteristic stated as one concrete sentence, citing the regulation/article if applicable."
  ],
  "validation_warnings": [
    "Warning about missing or ambiguous data that affects the analysis."
  ],
  "missing_optional_fields": ["field_name"]
}}

Constraints:
- Do NOT repeat information already explicit in the profile
- Do NOT invent facts — only infer from what is logically implied by the profile data
- missing_optional_fields: only fields that materially affect compliance assessment
- If nothing can be inferred, return empty arrays
</instructions>"""


def gap_analysis_prompt(profile_json: str, chunks_json: str, company_docs_json: str = "") -> str:
    has_docs = bool(company_docs_json.strip())

    docs_section = f"""
<company_documents>
The following passages were retrieved from documents the company uploaded.
Prioritise these as evidence. Quote specific passages in your evidence field.
{company_docs_json}
</company_documents>
""" if has_docs else ""

    cannot_assess_note = (
        "- CANNOT_ASSESS: ONLY if neither the profile, nor the uploaded documents, nor industry norms "
        "provide ANY basis for assessment. This must be extremely rare — under 2% of items."
        if has_docs
        else "- CANNOT_ASSESS: ABSOLUTE LAST RESORT only. Do NOT use because a policy document is missing. "
        "Absence of a measure IS evidence of non-compliance. Use NON_COMPLIANT or PARTIALLY_COMPLIANT instead."
    )

    profile_field_guidance = """
Profile fields ARE your evidence — treat them as direct compliance indicators:

GDPR / BDSG:
- has_processing_records=false → NON_COMPLIANT on Art. 30 GDPR
- has_dpo=false → assess DPO requirement against thresholds (employee count, data type)
- has_privacy_policy=false → NON_COMPLIANT on Art. 13/14 GDPR
- has_processor_agreements=false → NON_COMPLIANT on Art. 28 GDPR
- has_data_breach_procedure=false → NON_COMPLIANT on Art. 33/34 GDPR
- has_tom_documentation=false → NON_COMPLIANT on Art. 32 GDPR
- has_data_retention_policy=false → NON_COMPLIANT on Art. 5(1)(e) GDPR
- has_data_protection_training=false → NON_COMPLIANT on Art. 29/32(4) GDPR
- transfers_data_outside_eea=true → assess Art. 44-49 GDPR transfer safeguards
- has_consent_management=false → NON_COMPLIANT on Art. 6/7 GDPR where consent is the legal basis
- processes_special_category_data=true → stricter GDPR Art. 9 obligations apply

NIS2 (applies if is_critical_infrastructure_sector=true):
- has_information_security_policy=false → NON_COMPLIANT on Art. 21(2)(a) NIS2
- has_incident_response_plan=false → NON_COMPLIANT on Art. 21(2)(b) NIS2
- has_business_continuity_plan=false → NON_COMPLIANT on Art. 21(2)(c) NIS2
- has_vulnerability_management=false → NON_COMPLIANT on Art. 21(2)(e) NIS2
- has_mfa_implemented=false → NON_COMPLIANT on Art. 21(2)(j) NIS2
- has_supply_chain_security_assessment=false → NON_COMPLIANT on Art. 21(2)(d) NIS2
- has_security_awareness_training=false → NON_COMPLIANT on Art. 21(2)(g) NIS2

EU AI Act (applies if uses_ai_systems=true):
- ai_systems_are_high_risk=true → full high-risk obligations apply (Arts. 9-17)
- has_ai_risk_assessment=false → NON_COMPLIANT on Art. 9 EU AI Act
- has_ai_usage_documentation=false → NON_COMPLIANT on Art. 13 EU AI Act
- has_human_oversight_procedure=false → NON_COMPLIANT on Art. 14 EU AI Act

HinSchG (applies if employee_count >= 50):
- has_whistleblower_channel=false → NON_COMPLIANT on §12 HinSchG
- has_whistleblower_policy=false → PARTIALLY_COMPLIANT at best on §13 HinSchG

ArbSchG (applies to ALL employers):
- has_gefaehrdungsbeurteilung=false → NON_COMPLIANT on §5 ArbSchG
- has_gefaehrdungsbeurteilung_documented=false → NON_COMPLIANT on §6 ArbSchG
- has_first_aid_measures=false → NON_COMPLIANT on §10 ArbSchG
- has_employee_safety_training=false → NON_COMPLIANT on §12 ArbSchG

AGG (applies to ALL employers):
- has_anti_discrimination_policy=false → NON_COMPLIANT on §12 AGG
- has_agc_complaints_procedure=false → NON_COMPLIANT on §13 AGG

MiLoG (applies to ALL employers):
- has_working_time_records=false → NON_COMPLIANT on §17 MiLoG for covered workers
- uses_subcontractors=true → principal liability applies under §13 MiLoG

LkSG (applies if has_supply_chain_abroad=true and thresholds met):
- has_lksg_policy_statement=false → NON_COMPLIANT on §6 LkSG
- has_supplier_code_of_conduct=false → NON_COMPLIANT on §6 LkSG
- has_supplier_risk_assessment=false → NON_COMPLIANT on §5 LkSG
- has_lksg_complaints_procedure=false → NON_COMPLIANT on §8 LkSG

Absence of implementation = NON_COMPLIANT, not CANNOT_ASSESS.
Partial information = PARTIALLY_COMPLIANT with explanation, not CANNOT_ASSESS.
Only use CANNOT_ASSESS when the requirement depends on something genuinely unknowable from all available data.
"""

    doc_instruction = """
When company documents are provided, your evidence MUST cite specific passages.
  COMPLIANT example: "Privacy policy (Section 3.2) states: 'We collect name and email address for service delivery' — satisfying Art. 13(1)(c) GDPR."
  NON_COMPLIANT example: "No whistleblower reporting channel found in uploaded documents. Required by §12 HinSchG."
""" if has_docs else ""

    return f"""<task>
For each regulatory requirement provided, assess this company's compliance status.
{"Company documents have been uploaded — use them as primary evidence over profile fields alone." if has_docs else "Base your assessment on the company profile fields and retrieved regulation text. The profile IS sufficient to assess the vast majority of requirements."}
</task>

<company_profile>
{profile_json}
</company_profile>
{docs_section}
<retrieved_regulations>
{chunks_json}
</retrieved_regulations>

<instructions>
Assess each requirement chunk. Use exactly these status values:
- COMPLIANT: profile fields or documents confirm the company meets this requirement
- PARTIALLY_COMPLIANT: the company partially meets it — profile confirms some but not all aspects
- NON_COMPLIANT: profile fields show the requirement is not met (missing measure, wrong threshold, absence of documented activity)
{cannot_assess_note}

{profile_field_guidance}
{doc_instruction}
Output ONLY a valid JSON array:
[
  {{
    "regulation": "gdpr_dsgvo",
    "article_number": "Art. 30",
    "article_title": "Records of processing activities",
    "status": "NON_COMPLIANT",
    "evidence": "The company does not maintain Records of Processing Activities. With non-occasional processing and over 20 staff regularly handling personal data, Art. 30(1) GDPR records are mandatory and the SME exception does not apply.",
    "deficiency_description": "No Records of Processing Activities (Verarbeitungsverzeichnis) in place. Must document all processing operations including purpose, data categories, and retention periods."
  }}
]

CRITICAL LANGUAGE RULES — apply to every evidence and deficiency_description field:
- Write in plain English that any business owner with no legal background can understand.
- Never write JSON field names (e.g. never write has_dpo, has_processing_records, employee_count=62, =true, =false, etc.)
- Describe the compliance situation in human terms: "The company has no Data Protection Officer" not "has_dpo=false"
- State what the requirement actually means in practice before saying whether it is met.
- For deficiency_description: explain WHY this is a problem and what could go wrong if it stays unresolved.
- Evidence should read like a short paragraph a consultant would write, not a log entry.

Constraints:
- Every assessment MUST have a non-empty evidence field in plain English
- Only assess articles applicable to this company based on its profile
- deficiency_description: required only for PARTIALLY_COMPLIANT and NON_COMPLIANT
- Be consistent: same profile facts produce the same status
- Target: 98%+ of items should be COMPLIANT, PARTIALLY_COMPLIANT, or NON_COMPLIANT
</instructions>"""


def action_plan_prompt(profile_json: str, gap_analysis_json: str) -> str:
    return f"""<task>
Generate a prioritized action plan to address all compliance gaps below.
Every NON_COMPLIANT and PARTIALLY_COMPLIANT gap must have at least one action item.
</task>

<company_profile>
{profile_json}
</company_profile>

<gap_analysis>
{gap_analysis_json}
</gap_analysis>

<instructions>
Priority assignment rules — follow exactly:
- CRITICAL: legal deadline within 30 days, or active data breach risk
- HIGH: unimplemented legal obligation, any GDPR/BDSG data protection violation
- MEDIUM: partially met legal obligation, or best practice with meaningful risk reduction
- LOW: optional improvement, early preparation for upcoming requirements

Output ONLY a valid JSON array:
[
  {{
    "regulation": "gdpr_dsgvo",
    "article_number": "Art. 30",
    "action": "Create a Verarbeitungsverzeichnis (Record of Processing Activities) listing all processing activities, data categories, recipients, retention periods, and technical measures as required by Art. 30(1) GDPR.",
    "priority": "HIGH",
    "estimated_effort": "4-8 hours",
    "deadline": null,
    "dependencies": [],
    "gap_reference": "gdpr_dsgvo:Art. 30"
  }}
]

Constraints:
- Only generate actions for NON_COMPLIANT and PARTIALLY_COMPLIANT gaps
- Actions must be concrete and specific — not "document your data processing" but exactly what document to create, what it must contain, and which article requires it
- gap_reference format: "regulation:article_number"
- deadline: ISO date string if a statutory deadline exists, null otherwise
- Every action must map to exactly one gap via gap_reference
</instructions>"""


def executive_summary_prompt(
    company_name: str,
    applicable_count: int,
    total_regs: int,
    overall_score: float,
    critical_findings: list[str],
) -> str:
    findings_text = "\n".join(f"- {f}" for f in critical_findings[:3])
    return f"""<task>
Write a professional executive summary for this compliance assessment report.
</task>

<report_data>
Company: {company_name}
Regulations assessed: {total_regs} total, {applicable_count} applicable
Overall compliance score: {overall_score:.1f}%
Top critical findings:
{findings_text if findings_text else "No critical findings."}
</report_data>

<instructions>
Write an executive summary of maximum 300 words.
Structure:
1. One sentence: company name and what was assessed
2. Two to three sentences: applicable regulations and overall compliance score with brief interpretation
3. Two to three sentences: the most critical findings and their implications
4. One sentence: the single most urgent next step

Style: plain professional English, no legalese, no bullet points, flowing prose.
Tone: factual and direct — this is a professional report, not a sales document.

Output ONLY the summary text. No JSON, no headers, no labels.
</instructions>"""
