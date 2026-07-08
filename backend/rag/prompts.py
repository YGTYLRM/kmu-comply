"""All LLM prompt templates. No inline prompts anywhere else in the codebase."""
import re
import unicodedata
from datetime import date as _date

import json as _json

PROMPT_VERSION = "v1.3.0"


def _sanitize_profile_json(profile_json: str) -> str:
    """Sanitize all free-text fields in the serialised profile before prompt embedding."""
    try:
        data = _json.loads(profile_json)
        for field in ("existing_compliance_notes", "company_name", "industry"):
            if data.get(field):
                data[field] = _sanitize(str(data[field]), max_len=500 if field != "existing_compliance_notes" else 2000)
        return _json.dumps(data)
    except Exception:
        return profile_json


def _sanitize(text: str | None, max_len: int = 2000) -> str:
    """Strip prompt-injection patterns from user-supplied free text."""
    if not text:
        return ""
    # Truncate
    text = text[:max_len]
    # Normalize Unicode to defeat homoglyph injection (e.g. Cyrillic і instead of Latin i)
    text = unicodedata.normalize("NFKC", text)
    # Remove XML/HTML tags that could break prompt structure
    text = re.sub(r"<[^>]{0,100}>", "", text)
    # Collapse injection keywords (case-insensitive)
    _INJECTIONS = re.compile(
        r"\b(ignore|disregard|forget|override|system\s*prompt|new\s*instruction|you\s+are\s+now)\b",
        re.IGNORECASE,
    )
    text = _INJECTIONS.sub("[removed]", text)
    return text.strip()

SYSTEM_PERSONA = """Sie sind ein leitender Regulatory-Compliance-Consultant mit Spezialisierung auf deutsches KMU-Recht.
Sie erstellen ein VORLÄUFIGES COMPLIANCE-SCREENING, keine Rechtsberatung oder Prüfung.
Alle Ausgaben müssen klar als Screening-Werkzeug erkennbar sein — keine Rechtsberatung, keine Zertifizierung.

Ihre Aufgabe:
- Schreiben Sie auf Deutsch in klarer, verständlicher Sprache (B2-Niveau, kein Juristenjargon)
- Zitieren Sie immer konkrete Rechtsartikel (z. B. "Art. 30 DSGVO", nicht "DSGVO verlangt Dokumentation")
- Geben Sie konkrete, spezifische Empfehlungen — kein vages "Sie sollten erwägen..."
- Unterscheiden Sie zwischen MUSS (rechtliche Pflicht), SOLLTE (Best Practice) und KANN (optional)
- Benennen Sie Unsicherheiten explizit: "gilt wahrscheinlich, rechtliche Überprüfung empfohlen"
- Geben Sie realistische Aufwandsschätzungen für jede Empfehlung an
- Erfinden Sie keine Rechtsanforderungen — jeder Befund muss auf einen konkreten Artikel in der Wissensdatenbank zurückgehen
- KRITISCH: Wenn für eine Vorschrift keine Rechtstexte abgerufen wurden, geben Sie CANNOT_ASSESS aus — erfinden Sie keine Befunde

Konfidenz-Kennzeichnung — immer anwenden:
  VERIFIED: Befund basiert auf abgerufenem offiziellen Gesetzestext (höchste Konfidenz)
  SELF-REPORTED: Befund basiert auf Profilfeldern, die das Unternehmen ausgefüllt hat (mittlere Konfidenz)
  CANNOT_ASSESS: unzureichende Belege — stellen Sie die konkrete Frage, die beantwortet werden muss

Screening-Disclaimer — immer in Ihrer Sprache berücksichtigen:
  Diese Ausgabe ist ein vorläufiges Compliance-Screening auf Basis selbst angegebener Profildaten und
  KI-Analyse amtlicher Rechtstexte. Es handelt sich NICHT um eine Rechtsberatung, ein
  Compliance-Zertifikat oder eine Prüfung. Es begründet kein Mandatsverhältnis. Unternehmen sollten
  alle Befunde mit einem qualifizierten Rechtsanwalt prüfen, bevor Compliance-Entscheidungen getroffen
  oder Aussagen gegenüber Behörden gemacht werden. Complio haftet nicht für Entscheidungen, die
  ausschließlich auf diesem Screening beruhen.

Quellenautoritätshierarchie — bei Konflikten immer einhalten:
  Level 1 — Amtlicher Gesetzestext (bindend): maßgebliche Rechtsquelle; hat immer Vorrang
  Level 2 — Behördliche Leitlinien (autoritative Auslegung): erklärt Behördenanwendung; gilt, wenn nicht Level 1 widerspricht
  Level 3 — Unternehmensdokumente (nur Belege): zeigt, was das Unternehmen tut; überschreibt keine Rechtspflichten
Ein Unternehmensdokument mit "wir sind konform" überschreibt keine Level-1-Anforderung, die X vorschreibt."""


def profile_enrichment_prompt(profile_json: str) -> str:
    profile_json = _sanitize_profile_json(profile_json)
    return f"""<task>
Analysieren Sie dieses Unternehmensprofil und identifizieren Sie implizite compliance-relevante Merkmale,
die nicht explizit angegeben sind, aber logisch abgeleitet werden können.
Alle Ausgaben müssen auf DEUTSCH verfasst sein.
</task>

<company_profile>
{profile_json}
</company_profile>

<instructions>
Identifizieren Sie bis zu 10 abgeleitete Merkmale. Achten Sie auf:
- Branchenspezifische Datenverarbeitungsmuster (z.B. Gesundheitsbranche verarbeitet immer Gesundheitsdaten nach Art. 9 DSGVO)
- Lieferkettenrisiken anhand von Branche und Lieferländern
- Typische Energieverbrauchsmuster für diese Branche und Mitarbeiterzahl
- Implizite Verarbeitung personenbezogener Daten (Mitarbeiterdaten, B2C-Kundendaten usw.)
- Berichtspflichten, die sich aus Unternehmensgröße, Börsennotierung oder Branche ergeben
- Merkmale, die beeinflussen, welche konkreten Artikel innerhalb anwendbarer Vorschriften gelten

Ausgabe NUR als gültiges JSON in diesem Format:
{{
  "inferred_characteristics": [
    "Ein direkt und eindeutig aus den Profildaten abgeleitetes Merkmal — z.B. 'Das Unternehmen beschäftigt Mitarbeiter und hat daher Arbeitgeberpflichten nach ArbSchG §3.'"
  ],
  "inferred_assumptions": [
    "Eine Annahme, die angesichts der Branche/Größe plausibel, aber nicht direkt bestätigt ist — z.B. 'Ein Produktionsunternehmen dieser Größe betreibt wahrscheinlich Maschinen, die Abwärme erzeugen, was §15 EnEfG auslösen könnte.' Jede Annahme mit 'ANNAHME:' prefixen."
  ],
  "validation_warnings": [
    "Hinweis auf fehlende oder unklare Daten, die die Analyse beeinflussen."
  ],
  "missing_optional_fields": ["field_name"]
}}

Einschränkungen:
- inferred_characteristics: nur was DIREKT UND LOGISCH mit hoher Sicherheit ableitbar ist
- inferred_assumptions: plausibel, aber unbestätigt — müssen mit 'ANNAHME:' beginnen
- Annahmen NICHT in inferred_characteristics aufnehmen
- Keine Informationen wiederholen, die bereits explizit im Profil stehen
- missing_optional_fields: nur Felder, die die Compliance-Bewertung wesentlich beeinflussen
- Falls nichts abgeleitet werden kann, leere Arrays zurückgeben
- ALLE Texte in inferred_characteristics, inferred_assumptions und validation_warnings auf DEUTSCH verfassen
</instructions>"""


def gap_analysis_prompt(profile_json: str, chunks_json: str, company_docs_json: str = "", inferred_assumptions: list[str] | None = None) -> str:
    profile_json = _sanitize_profile_json(profile_json)
    has_docs = bool(company_docs_json.strip())

    _today = _date.today()
    _high_risk_active = _today >= _date(2026, 8, 2)
    _ai_act_phasing_note = (
        "EU AI Act phasing — high-risk obligations (Arts. 9-17, Annex I and III) "
        "ARE NOW ACTIVE as of 2 Aug 2026 under current law. Note: Digital Omnibus proposal "
        "(pending formal adoption in EU Official Journal) may delay Annex III to 2 Dec 2027. "
        "Assess missing high-risk measures as PARTIALLY_COMPLIANT with a note that the "
        "effective date is legally uncertain until the Digital Omnibus is formally adopted."
        if _high_risk_active else
        "EU AI Act phasing — high-risk obligations (Arts. 9-17, Annex I and III) are NOT YET "
        "active. Current law sets 2 Aug 2026; Digital Omnibus proposal (pending formal adoption) "
        "may delay Annex III to 2 Dec 2027. Assess gaps in high-risk requirements as "
        "PARTIALLY_COMPLIANT with evidence noting 'preparation required — effective date uncertain "
        "(2 Aug 2026 under current law, possible delay to 2 Dec 2027 pending Digital Omnibus)'. "
        "Art. 5 prohibited practices and GPAI rules (Arts. 51-56) are already active and must "
        "be assessed as NON_COMPLIANT if unmet."
    )

    docs_section = f"""
<company_documents>
The following passages were retrieved from documents the company uploaded.
Prioritise these as evidence. Quote specific passages in your evidence field.
{company_docs_json}
</company_documents>
""" if has_docs else ""

    cannot_assess_note = (
        "- CANNOT_ASSESS: Use when the assessment genuinely depends on information that is not in the "
        "profile, not in the uploaded documents, and cannot be reasonably inferred. When you use "
        "CANNOT_ASSESS, the evidence field MUST contain a specific, concrete question that the company "
        "must answer to complete this assessment — e.g. 'To assess this requirement, confirm: does the "
        "company conduct annual penetration tests on its network infrastructure?' Never use CANNOT_ASSESS "
        "simply because a document is missing — absence of a measure is evidence of non-compliance."
        if has_docs
        else "- CANNOT_ASSESS: Use only when the assessment genuinely depends on information that is "
        "not in the profile and cannot be reasonably inferred. When you use CANNOT_ASSESS, the evidence "
        "field MUST contain a specific, concrete question that the company must answer — e.g. 'To assess "
        "this requirement, confirm: does the company process biometric data for access control?' "
        "Absence of a compliance measure IS evidence of non-compliance — use NON_COMPLIANT or "
        "PARTIALLY_COMPLIANT for missing measures, not CANNOT_ASSESS."
    )

    profile_field_guidance = f"""
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

NIS2 (applies to essential/important entities in critical sectors meeting size thresholds):
- has_information_security_policy=false → NON_COMPLIANT on Art. 21(2)(a) NIS2
- has_incident_response_plan=false → NON_COMPLIANT on Art. 21(2)(b) NIS2
- has_business_continuity_plan=false → NON_COMPLIANT on Art. 21(2)(c) NIS2
- has_vulnerability_management=false → NON_COMPLIANT on Art. 21(2)(e) NIS2
- has_mfa_implemented=false → NON_COMPLIANT on Art. 21(2)(j) NIS2
- has_supply_chain_security_assessment=false → NON_COMPLIANT on Art. 21(2)(d) NIS2
- has_security_awareness_training=false → NON_COMPLIANT on Art. 21(2)(g) NIS2
IMPORTANT NIS2 incident reporting — Art. 23 has THREE steps, not one deadline:
  1. Early warning: within 24 hours of becoming aware → notify CSIRT/competent authority
  2. Incident notification: within 72 hours → initial assessment of severity, impact, indicators
  3. Final report: within 1 month → full description, root cause, cross-border impact, measures taken
  Do NOT describe this as "72 hours" or "24 hours" alone — all three obligations apply.

EU AI Act (applies if uses_ai_systems=true):
- {_ai_act_phasing_note}
- ai_systems_are_high_risk=true → full high-risk obligations apply (Arts. 9-17)
- has_ai_risk_assessment=false → NON_COMPLIANT on Art. 9 EU AI Act (see phasing note above)
- has_ai_usage_documentation=false → NON_COMPLIANT on Art. 13 EU AI Act (see phasing note above)
- has_human_oversight_procedure=false → NON_COMPLIANT on Art. 14 EU AI Act (see phasing note above)

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

TDDDG / TTDSG (applies to any company with a website processing personal data of German users):
- has_cookie_banner=false → NON_COMPLIANT on §25(1) TDDDG (no consent before tracking)
- has_cookie_banner=true → COMPLIANT only if banner actually blocks non-essential scripts before consent
- has_cookie_policy=false → NON_COMPLIANT on §25 TDDDG / Art. 13 GDPR (no documented cookie inventory)
NOTE: TDDDG §25 requires consent BEFORE any non-essential cookie, pixel, or fingerprinting script loads.
A cookie banner that only informs (opt-out) does NOT satisfy §25 TDDDG — it must be opt-in.
The law is officially named TDDDG (Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz) since 2024,
previously called TTDSG. Both names refer to the same law.

GwG (applies to AML-obligated sectors: financial services, crypto, real estate agents, lawyers/notaries,
accountants, tax advisors, gambling operators — see is_aml_obligated_sector field):
- has_aml_risk_analysis=false → NON_COMPLIANT on §5 GwG
- has_aml_officer=false → NON_COMPLIANT on §7 GwG (required for regulated financial institutions)
- has_kyc_procedures=false → NON_COMPLIANT on §10 GwG

EU Data Act (applies to connected product manufacturers and data processing service providers):
- produces_connected_products=true and has_data_access_mechanism=false → NON_COMPLIANT on Art. 4 EU Data Act
- provides_data_processing_services=true → assess cloud switching obligations (Art. 23-25)

Absence of implementation = NON_COMPLIANT, not CANNOT_ASSESS.
Partial information = PARTIALLY_COMPLIANT with explanation, not CANNOT_ASSESS.
Only use CANNOT_ASSESS when the requirement depends on something genuinely unknowable from all available data.
"""

    doc_instruction = """
When company documents are provided, your evidence MUST cite specific passages.
  COMPLIANT example: "Privacy policy (Section 3.2) states: 'We collect name and email address for service delivery' — satisfying Art. 13(1)(c) GDPR."
  NON_COMPLIANT example: "No whistleblower reporting channel found in uploaded documents. Required by §12 HinSchG."
""" if has_docs else ""

    assumptions_section = ""
    if inferred_assumptions:
        items = "\n".join(f"- {a}" for a in inferred_assumptions[:10])
        assumptions_section = f"""
<unconfirmed_assumptions>
The following were inferred by a pre-processing step but are NOT confirmed by the company.
Do NOT use these as the sole basis for a NON_COMPLIANT finding.
If an assumption is your only evidence, use PARTIALLY_COMPLIANT and note that verification is needed.
{items}
</unconfirmed_assumptions>
"""

    return f"""<task>
For each regulatory requirement provided, assess this company's compliance status.
{"Company documents have been uploaded — use them as primary evidence over profile fields alone." if has_docs else "Base your assessment on the company profile fields and retrieved regulation text. The profile IS sufficient to assess the vast majority of requirements."}
</task>{assumptions_section}

<applicability_notice>
IMPORTANT: Applicability determination has already been completed before this step using a separate deterministic rule engine. The regulations and articles you are receiving are confirmed to apply to this company. Do NOT use the retrieved legal text to re-determine whether a regulation applies or what size/revenue thresholds trigger obligations — that has already been decided. Your sole job is to assess HOW WELL the company currently meets each provided article requirement. Do not adjust compliance status based on size thresholds you read in the retrieved text.
</applicability_notice>

<company_profile>
{profile_json}
</company_profile>
{docs_section}
<retrieved_regulations>
Each entry includes a source_authority field. Treat Level 1 (official law text) as binding.
Level 2 (guidance) informs interpretation but does not override Level 1.
Level 3 (company documents) is evidence only — it can show compliance but cannot waive an obligation.
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
    "article_title": "Verzeichnis von Verarbeitungstätigkeiten",
    "status": "NON_COMPLIANT",
    "evidence": "Das Unternehmen führt kein Verzeichnis von Verarbeitungstätigkeiten. Bei nicht gelegentlicher Verarbeitung und über 20 Mitarbeitern, die regelmäßig personenbezogene Daten verarbeiten, ist das Verzeichnis nach Art. 30 Abs. 1 DSGVO verpflichtend — die KMU-Ausnahme greift nicht.",
    "deficiency_description": "Kein Verarbeitungsverzeichnis vorhanden. Alle Verarbeitungstätigkeiten inklusive Zweck, Datenkategorien, Empfänger und Aufbewahrungsfristen müssen dokumentiert werden.",
    "evidence_quote": "\"Controllers shall maintain a record of processing activities under their responsibility.\" (Art. 30(1) GDPR, retrieved chunk)"
  }}
]

KRITISCHE SPRACHREGELN — gelten für alle evidence- und deficiency_description-Felder:
- Schreiben Sie auf DEUTSCH in klarer Sprache, die jeder Unternehmer ohne Rechtskenntnisse versteht.
- Schreiben Sie niemals JSON-Feldnamen (z. B. niemals has_dpo, has_processing_records, employee_count=62, =true, =false usw.)
- Beschreiben Sie die Compliance-Situation in menschlichen Begriffen: "Das Unternehmen hat keinen Datenschutzbeauftragten" — nicht "has_dpo=false"
- Erklären Sie zuerst, was die Anforderung in der Praxis bedeutet, bevor Sie angeben, ob sie erfüllt ist.
- Für deficiency_description: erklären Sie, WARUM das ein Problem ist und was passieren könnte, wenn es ungelöst bleibt.
- Evidence soll wie ein kurzer Absatz eines Beraters klingen, kein Protokolleintrag.

Constraints:
- Jede Bewertung MUSS ein nicht-leeres evidence-Feld auf Deutsch enthalten
- Nur Artikel bewerten, die auf dieses Unternehmen anwendbar sind
- deficiency_description: nur bei PARTIALLY_COMPLIANT und NON_COMPLIANT
- CANNOT_ASSESS evidence MUSS eine konkrete Frage enthalten, die das Unternehmen beantworten muss
- Konsistenz: gleiche Profilfakten ergeben gleichen Status
- CANNOT_ASSESS ist akzeptabel wenn wirklich nötig — keinen Status erzwingen wenn Daten fehlen
- evidence_quote: Bei VERIFIED-Befunden (gestützt auf abgerufenen Gesetzestext) zitieren Sie einen exakten Satz aus dem Quelltext in evidence_quote. Bei SELF-REPORTED oder CANNOT_ASSESS weglassen. Ein fehlendes Zitat bei VERIFIED-Befunden signalisiert eine möglicherweise halluzinierte Quelle.
</instructions>"""


def action_plan_prompt(profile_json: str, gap_analysis_json: str) -> str:
    profile_json = _sanitize_profile_json(profile_json)
    return f"""<task>
Erstellen Sie einen priorisierten Maßnahmenplan auf DEUTSCH, um alle unten aufgeführten Compliance-Lücken zu schließen.
Jede NON_COMPLIANT- und PARTIALLY_COMPLIANT-Lücke muss mindestens einen Maßnahmenpunkt haben.
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
    "action": "Erstellen Sie ein Verarbeitungsverzeichnis (Art. 30 Abs. 1 DSGVO) mit allen Verarbeitungstätigkeiten, Datenkategorien, Empfängern, Aufbewahrungsfristen und technischen Maßnahmen.",
    "priority": "HIGH",
    "estimated_effort": "4-8 hours",
    "deadline": null,
    "dependencies": [],
    "gap_reference": "gdpr_dsgvo:Art. 30"
  }}
]

Constraints:
- Nur für NON_COMPLIANT- und PARTIALLY_COMPLIANT-Lücken Maßnahmen generieren
- Maßnahmen müssen konkret und spezifisch sein — nicht "dokumentieren Sie Ihre Datenverarbeitung", sondern genau welches Dokument erstellt werden muss, was es enthalten muss und welcher Artikel es verlangt
- Alle Maßnahmen auf DEUTSCH schreiben
- gap_reference-Format: "regulation:article_number"
- deadline: ISO-Datumsstring, wenn gesetzliche Frist existiert, sonst null
- Jede Maßnahme muss genau einer Lücke über gap_reference zugeordnet sein
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
Schreiben Sie eine professionelle Zusammenfassung (Kurzübersicht) für diesen Compliance-Screening-Bericht auf DEUTSCH.
</task>

<report_data>
Unternehmen: {company_name}
Geprüfte Vorschriften: {total_regs} gesamt, {applicable_count} anwendbar
Gesamt-Compliance-Score: {overall_score:.1f}%
Wichtigste kritische Befunde:
{findings_text if findings_text else "Keine kritischen Befunde."}
</report_data>

<instructions>
Schreiben Sie eine Zusammenfassung von maximal 300 Wörtern auf DEUTSCH.
Struktur:
1. Ein Satz: Unternehmensname und was bewertet wurde
2. Zwei bis drei Sätze: anwendbare Vorschriften und Gesamt-Compliance-Score mit kurzer Interpretation
3. Zwei bis drei Sätze: wichtigste kritische Befunde und deren Bedeutung
4. Ein Satz: der dringendste nächste Schritt

Stil: klares professionelles Deutsch, kein Juristenjargon, keine Aufzählungspunkte, fließender Prosatext.
Ton: sachlich und direkt — das ist ein professioneller Bericht, kein Werbedokument.

Ausgabe NUR den Zusammenfassungstext. Kein JSON, keine Überschriften, keine Labels.
</instructions>"""
