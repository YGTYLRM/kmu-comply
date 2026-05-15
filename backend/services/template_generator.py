"""
Compliance document template generator.

Generates company-specific compliance document drafts based on the company
profile and applicable regulations. Each template is produced by an LLM call
with the company context injected. Templates are returned as plain Markdown.

Available templates:
  privacy_notice          — GDPR Art. 13/14 Datenschutzerklärung
  processing_records      — GDPR Art. 30 Verarbeitungsverzeichnis
  tom_checklist           — GDPR Art. 32 Technical & Organisational Measures
  incident_response_plan  — NIS2/GDPR incident response procedure
  ai_usage_policy         — EU AI Act internal AI usage policy
  ai_inventory            — EU AI Act AI system inventory form
  whistleblower_policy    — HinSchG §13 internal whistleblower procedure
  safety_instruction      — ArbSchG §12 employee safety instruction template
  supplier_code_of_conduct — LkSG §6 supplier code of conduct
  nis2_risk_register      — NIS2 Art. 21 cybersecurity risk register template
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import anthropic

from config import settings
from rag.prompts import SYSTEM_PERSONA

logger = logging.getLogger(__name__)

TEMPLATES: dict[str, dict[str, Any]] = {
    "privacy_notice": {
        "title": "Privacy Notice (Datenschutzerklärung)",
        "regulation": "GDPR Art. 13/14",
        "description": "Customer-facing privacy notice explaining what data is collected and why.",
        "prompt_instruction": (
            "Generate a professional GDPR-compliant privacy notice (Datenschutzerklärung) in English "
            "for this company. Include: identity of the controller, purposes and legal bases for processing, "
            "categories of personal data, recipients, retention periods, data subject rights (Art. 15-22), "
            "right to lodge a complaint with a supervisory authority, and contact details for the DPO if required. "
            "Format as structured Markdown with clear section headings. Be specific to this company profile."
        ),
    },
    "processing_records": {
        "title": "Record of Processing Activities (Verarbeitungsverzeichnis)",
        "regulation": "GDPR Art. 30",
        "description": "Internal record listing all personal data processing activities.",
        "prompt_instruction": (
            "Generate a Record of Processing Activities template (Verarbeitungsverzeichnis) compliant with "
            "GDPR Art. 30. Create a Markdown table with columns: Activity Name, Purpose, Legal Basis, "
            "Data Categories, Data Subjects, Recipients, Retention Period, Transfer to Third Country, "
            "Technical/Organisational Measures. Pre-fill 5-8 realistic processing activities based on "
            "this company's industry and size. Include instructions for completing and maintaining the record."
        ),
    },
    "tom_checklist": {
        "title": "Technical & Organisational Measures (TOMs)",
        "regulation": "GDPR Art. 32",
        "description": "Documentation of security measures protecting personal data.",
        "prompt_instruction": (
            "Generate a Technical and Organisational Measures (TOMs) documentation template compliant with "
            "GDPR Art. 32. Organise by category: Physical security, Access controls, Network security, "
            "Data encryption, Backup and recovery, Employee training, Pseudonymisation/anonymisation, "
            "Third-party management. For each measure: describe what it is, mark as Implemented/Planned/N.A., "
            "and leave a notes field. Pre-fill with measures appropriate for this company's size and industry."
        ),
    },
    "incident_response_plan": {
        "title": "Incident Response Plan",
        "regulation": "NIS2 Art. 21 / GDPR Art. 33",
        "description": "Documented procedure for detecting and responding to cybersecurity or data incidents.",
        "prompt_instruction": (
            "Generate a concise Incident Response Plan in Markdown covering: "
            "1. Purpose and scope, 2. Incident classification (severity levels), "
            "3. Detection and initial triage steps, 4. Escalation chain (roles and contacts — use placeholders), "
            "5. Containment steps, 6. GDPR 72-hour breach notification procedure (Art. 33), "
            "7. NIS2 24-hour early warning and 72-hour incident report requirements (Art. 23), "
            "8. Recovery and post-incident review, 9. Communication templates. "
            "Make the plan practical and specific to this company's sector and size."
        ),
    },
    "ai_usage_policy": {
        "title": "AI Usage Policy",
        "regulation": "EU AI Act Art. 26 / Art. 50",
        "description": "Internal policy governing how employees may use AI systems.",
        "prompt_instruction": (
            "Generate an internal AI Usage Policy in Markdown for this company. Include: "
            "1. Scope (which AI tools are covered), 2. Permitted uses, 3. Prohibited uses "
            "(especially aligned with EU AI Act Art. 5 prohibited practices), "
            "4. Human oversight requirements for AI-assisted decisions, "
            "5. Transparency obligations when AI interacts with third parties (Art. 50), "
            "6. Data protection and confidentiality requirements when using AI tools, "
            "7. Reporting mechanism for AI incidents or concerns, "
            "8. Training requirements for employees who use AI. "
            "Make it practical for employees, not just legal boilerplate."
        ),
    },
    "ai_inventory": {
        "title": "AI System Inventory",
        "regulation": "EU AI Act Art. 11 / Art. 26",
        "description": "Register of all AI systems used or developed by the company.",
        "prompt_instruction": (
            "Generate an AI System Inventory template in Markdown. Create a table with columns: "
            "AI System Name, Vendor/Provider, Purpose, Department, Role (Provider/Deployer/Both), "
            "Risk Level (Minimal/Limited/High-risk/Prohibited), Data Used, Human Oversight Measure, "
            "Date Deployed, Responsible Owner. Include guidance on how to classify each system "
            "against EU AI Act Annex III high-risk categories. Pre-fill 3-5 example entries "
            "realistic for this company's industry."
        ),
    },
    "whistleblower_policy": {
        "title": "Whistleblower Reporting Policy",
        "regulation": "HinSchG §13",
        "description": "Internal policy describing the whistleblower channel and protection measures.",
        "prompt_instruction": (
            "Generate a Whistleblower Reporting Policy compliant with HinSchG §13 in Markdown. Include: "
            "1. Purpose and scope, 2. What can be reported (§2 HinSchG scope), "
            "3. How to submit a report (channel description), 4. Anonymity and confidentiality protections, "
            "5. Non-retaliation commitment (§36 HinSchG), 6. Process after submission "
            "(acknowledgement within 7 days, feedback within 3 months per §17), "
            "7. Who handles reports and their independence, 8. Record-keeping. "
            "The policy should be employee-friendly and clear, not legal boilerplate."
        ),
    },
    "safety_instruction": {
        "title": "Employee Safety Instruction Template",
        "regulation": "ArbSchG §12",
        "description": "Documented safety instruction template for employee onboarding and regular training.",
        "prompt_instruction": (
            "Generate an Employee Occupational Safety Instruction template (Sicherheitsunterweisung) "
            "compliant with ArbSchG §12 in Markdown. Include: "
            "1. General workplace safety rules, 2. Emergency procedures (fire, first aid, evacuation), "
            "3. Specific hazards relevant to this company's industry, 4. Equipment safety, "
            "5. Reporting of accidents and near-misses, 6. Signature/acknowledgement section "
            "with employee name, date, instructor name, and signature lines. "
            "Make the instruction practical and readable for all employees."
        ),
    },
    "supplier_code_of_conduct": {
        "title": "Supplier Code of Conduct",
        "regulation": "LkSG §6",
        "description": "Code of conduct for suppliers covering human rights and environmental standards.",
        "prompt_instruction": (
            "Generate a Supplier Code of Conduct compliant with LkSG §6 in Markdown. Cover: "
            "1. Purpose and scope, 2. Human rights standards (no forced labor, child labor, "
            "freedom of association, fair wages), 3. Environmental standards (hazardous substances, "
            "waste, emissions), 4. Anti-corruption and business ethics, "
            "5. Working conditions and occupational safety, 6. Supplier monitoring and audit rights, "
            "7. Reporting mechanism for violations, 8. Consequences of non-compliance, "
            "9. Signature section. Reference specific LkSG obligations throughout."
        ),
    },
    "nis2_risk_register": {
        "title": "Cybersecurity Risk Register",
        "regulation": "NIS2 Art. 21",
        "description": "Template for documenting and tracking cybersecurity risks.",
        "prompt_instruction": (
            "Generate a Cybersecurity Risk Register template in Markdown compliant with NIS2 Art. 21. "
            "Create a risk register table with: Risk ID, Risk Description, Asset Affected, "
            "Likelihood (1-5), Impact (1-5), Risk Score, Current Controls, "
            "Additional Measures Required, Owner, Review Date, Status. "
            "Pre-fill 8-10 realistic cybersecurity risks for this company's sector and size, "
            "covering the NIS2 Art. 21 security measure categories "
            "(network security, access control, supply chain, incident handling, "
            "business continuity, cryptography, MFA). Include a risk scoring guide."
        ),
    },
}


@lru_cache(maxsize=1)
def _llm_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.llm_api_key)


def generate_template(template_id: str, profile_json: str) -> str:
    """
    Generate a compliance document template for the given template ID,
    personalised to the company profile. Returns Markdown text.
    """
    tmpl = TEMPLATES.get(template_id)
    if not tmpl:
        raise ValueError(f"Unknown template: {template_id}")

    if not settings.llm_api_key:
        raise RuntimeError("LLM API key not configured")

    prompt = f"""<task>
Generate a compliance document template for this company.
</task>

<company_profile>
{profile_json}
</company_profile>

<template_instructions>
{tmpl["prompt_instruction"]}

Output ONLY the document content in Markdown. Do not include any preamble,
meta-commentary, or explanation outside the document itself.
Start directly with the document title as an H1 heading.
Include a footer note: "Generated by Complio — preliminary template only.
Have this reviewed by a qualified legal or compliance professional before use."
</template_instructions>"""

    import time
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            response = _llm_client().messages.create(
                model=settings.llm_model,
                max_tokens=4096,
                temperature=0,
                system=SYSTEM_PERSONA,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as exc:
            logger.warning("template_generator: attempt %d failed: %s", attempt + 1, exc)
            last_exc = exc
            if attempt < 2:
                time.sleep(2 ** attempt)

    raise RuntimeError(f"Template generation failed after 3 attempts: {last_exc}")
