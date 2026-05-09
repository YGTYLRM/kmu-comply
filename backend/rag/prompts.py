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
        "- CANNOT_ASSESS: only if both the profile AND the uploaded documents lack information needed"
        if has_docs
        else "- CANNOT_ASSESS: the profile lacks information needed to determine compliance"
    )

    doc_instruction = """
When company documents are provided, your evidence MUST cite specific passages.
  COMPLIANT example: "Privacy policy (Section 3.2) states: 'We collect name and email address for service delivery' — satisfying Art. 13(1)(c) GDPR."
  NON_COMPLIANT example: "No whistleblower reporting channel found in uploaded documents. Required by §12 HinSchG."
""" if has_docs else ""

    return f"""<task>
For each regulatory requirement provided, assess this company's compliance status.
{"Company documents have been uploaded — use them as primary evidence over profile fields alone." if has_docs else "Base your assessment on the company profile and retrieved regulation text."}
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
- COMPLIANT: evidence shows the company meets this requirement
- PARTIALLY_COMPLIANT: the company partially meets it — specific gaps exist
- NON_COMPLIANT: the company does not meet this requirement
{cannot_assess_note}
{doc_instruction}
Output ONLY a valid JSON array:
[
  {{
    "regulation": "gdpr_dsgvo",
    "article_number": "Art. 30",
    "article_title": "Records of processing activities",
    "status": "NON_COMPLIANT",
    "evidence": "Profile shows has_processing_records=false with 150 employees and non-occasional processing — Art. 30 records are mandatory.",
    "deficiency_description": "No Records of Processing Activities (Verarbeitungsverzeichnis) maintained — required under Art. 30(1) GDPR."
  }}
]

Constraints:
- Every assessment MUST have a non-empty evidence field
- Only assess articles applicable to this company
- deficiency_description: required only for PARTIALLY_COMPLIANT and NON_COMPLIANT
- Be consistent: same facts produce the same status
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
