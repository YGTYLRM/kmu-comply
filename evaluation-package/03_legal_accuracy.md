# Complio — Legal Accuracy Assessment

This document describes the methodology for regulatory threshold logic, the citation approach, and known legal caveats that require professional review before the product is sold commercially.

---

## Methodology: How Thresholds Are Determined

All applicability thresholds are implemented in `backend/services/threshold_engine.py`. The methodology:

1. **Primary source:** Each function cites the exact statute and paragraph it implements.
2. **Verbatim text:** Where the legal trigger is ambiguous, the German/EU original text is quoted inline (e.g. "mehr als" = strictly greater than, not ≥).
3. **No LLM involvement:** Applicability decisions are never delegated to the LLM. The code is the authority.
4. **Conservative defaults:** When a threshold is uncertain (e.g. NIS2 sector classification for an unusual industry), the system returns CANNOT_ASSESS with guidance to consult the BSI sector registry rather than guessing.

---

## Regulation-by-Regulation Summary

### GDPR / DSGVO
**Threshold:** Applies to any company processing personal data of EU residents.
**DPO trigger (BDSG §38(1)):** ≥20 employees *constantly* involved in automated processing of personal data. Caveat: "constantly" (ständig) is approximated as "not purely occasional." The exact threshold is fact-specific and legally uncertain.
**Processing records (Art. 30(5)):** Required if ≥250 employees OR non-occasional processing OR special category data.
**Accuracy confidence: HIGH** — threshold is clear; DPO "constantly" caveat is flagged to users.

### BDSG
**Threshold:** Supplements GDPR for companies in Germany. DPO threshold mirrors GDPR.
**Accuracy confidence: HIGH**

### NIS2 (implemented as BSIG)
**Threshold:** Sector-based (Annex I/II) + size-based.
- *Besonders wichtige Einrichtung* (§28(6) BSIG): Annex I sector + ≥250 employees or ≥€50M revenue, OR KRITIS operator regardless of size.
- *Wichtige Einrichtung* (§28(7) BSIG): Annex I/II sector + ≥50 employees or ≥€10M revenue.
**Incident reporting:** 3-step: 24h early warning → 72h notification → 1-month final report (Art. 23 NIS2).
**Caveat:** NIS2UmsuCG (German implementation) was delayed. Current implementation reflects BSI guidance and BSIG 2023 as closest available proxy.
**Accuracy confidence: MEDIUM** — sector taxonomy is solid; KRITIS overlap needs case-by-case analysis.

### EU AI Act
**Threshold:** Applies if company uses AI systems.
**Phased rollout:** High-risk obligations active from 2 August 2026. GPAI rules from 2 August 2025. Both dates computed dynamically from `date.today()` and injected into gap analysis prompt.
**Caveat:** Digital Omnibus proposal (pending EU Official Journal) may delay some Annex III obligations to December 2027. Both dates flagged as uncertain in every analysis.
**Accuracy confidence: MEDIUM** — phasing is complex and legally uncertain; users told to watch for updates.

### HinSchG (Whistleblower Protection)
**Threshold:** §12(2) HinSchG — reporting channel required at ≥50 employees.
**3-month transition:** Companies crossing 50 employees have 3 months to implement.
**Accuracy confidence: HIGH**

### LkSG (Supply Chain Due Diligence)
**Threshold:** §1(1) LkSG — ≥1,000 employees (including Leiharbeitnehmer >6 months and group subsidiaries per §2(6)). In scope since 1 January 2024.
**Caveat:** Employee counting methodology (subsidiaries, Leiharbeitnehmer) requires case-by-case analysis for borderline companies.
**Accuracy confidence: HIGH** for companies clearly above/below threshold; MEDIUM at borderline.

### EnEfG / EDL-G (Energy Efficiency)
**Threshold:** Non-SME gate first (≥250 employees OR >€50M revenue OR >€43M balance sheet per EU Recommendation 2003/361). Then:
- ≥7.5 GWh annual consumption → EnEfG §8(1) certified EnMS (ISO 50001/EMAS) required.
- "mehr als 7,5 GWh" = strictly greater than (fixed from ≥ in session 1).
**Accuracy confidence: HIGH** — threshold text is unambiguous.

### CSRD (Sustainability Reporting)
**Threshold:** 2 of 3 size criteria: >250 employees, >€50M revenue, >€25M balance sheet.
**Wave assignment:**
- Wave 1 (FY2024): PIEs with >500 employees — not postponed
- Wave 2 (FY2027): Other large companies — postponed from FY2025 by Directive (EU) 2025/794
- Wave 3 (FY2028): Listed SMEs
**Major caveat:** EU Council February 2026 Omnibus agreement raised thresholds to >1,000 employees AND >€450M revenue. This has NOT been formally adopted into EU law as of the knowledge cutoff. Current code implements original 2/3 criteria with a ⚠️ caveat flag.
**Accuracy confidence: LOW–MEDIUM** — Omnibus uncertainty. **Must be resolved before selling CSRD assessments.**

### ArbSchG (Workplace Safety)
**Threshold:** Applies to all employers with ≥1 employee. Exception: private household employers (§1(2) ArbSchG).
**Coverage:** ArbSchG, ArbZG (working time), MuSchG (maternity), JArbSchG (youth), BUrlG (annual leave), BBiG (vocational training), AEntG.
**Accuracy confidence: HIGH**

### AGG (Anti-Discrimination)
**Threshold:** Applies to all employers.
**Leiharbeitnehmer:** Temporary workers counted as employees of the using company for AGG §6(2) purposes — implemented.
**Accuracy confidence: HIGH**

### MiLoG (Minimum Wage)
**Threshold:** Applies to all employers.
**Documentation:** Specific requirements for certain employee categories (mini-jobs, certain sectors).
**Accuracy confidence: HIGH**

### TTDSG / TDDDG (Cookie Consent)
**Threshold:** Any company operating a website.
**Cookie consent:** Opt-in required for non-essential cookies (§25 TTDSG). Distinction between opt-in and opt-out implemented in prompts.
**Accuracy confidence: HIGH**

### GwG (Anti-Money Laundering)
**Threshold:** §2 GwG obligated sectors — finance, real estate, banking, crypto, gambling, insurance auto-trigger; lawyers, notaries, accountants, tax advisors must self-declare via `is_aml_obligated_sector=true`.
**Accuracy confidence: HIGH** for auto-trigger sectors; MEDIUM for self-declaration sectors.

### EU Data Act
**Threshold:** Applies to manufacturers of connected products and digital service providers.
**Accuracy confidence: MEDIUM** — EU Data Act is new (applies from September 2025); limited enforcement guidance available.

---

## Disclaimer Architecture

**System persona (all LLM calls):** "You are a Senior Regulatory Compliance Consultant... This output is a preliminary screening, not a legal opinion."

**Gap analysis prompt:** Explicit instruction that the output is "preliminary, not a legal opinion" injected in the system persona.

**PDF cover:** "This report is a preliminary compliance screening, not legal advice. Consult a qualified Rechtsanwalt before acting on these findings."

**Document templates footer:** "Generated by Complio — preliminary template only. Have this reviewed by a qualified legal or compliance professional before use."

**CANNOT_ASSESS rule:** Only used when information is genuinely unknowable; cannot be used to avoid a finding where non-compliance is implied by the profile.

---

## Known Legal Caveats Requiring Professional Review

| Item | Status | Risk |
|------|--------|------|
| CSRD Omnibus threshold | Code flags with ⚠️; not yet resolved | HIGH — may be over-screening |
| BDSG DPO "constantly" interpretation | Approximated; flagged in code | MEDIUM |
| NIS2 / BSIG sector taxonomy for unusual industries | Returns CANNOT_ASSESS | LOW |
| LkSG employee counting at group boundaries | Profile field; user must verify | MEDIUM |
| EU AI Act phasing | Dynamically computed; Digital Omnibus uncertainty flagged | MEDIUM |
| Full threshold engine review | Not yet lawyer-reviewed | HIGH (before commercial launch) |

**Recommendation:** Engage a Rechtsanwalt for a sign-off review of `backend/services/threshold_engine.py` before the first paying customer, focused on the CSRD, BDSG, and NIS2 threshold functions.

---

## What the System Does NOT Claim

- It does not provide legal advice (stated in every output)
- It does not perform a legal audit
- It does not guarantee regulatory compliance
- It does not replace a DPO or compliance officer
- Its gap findings are based on a company profile self-assessment — they cannot account for undisclosed facts
