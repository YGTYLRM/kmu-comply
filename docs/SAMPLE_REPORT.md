# Complio — Sample Compliance Report

**Company:** Beispiel GmbH (Example)
**Industry:** IT Software / Digital Services
**Employees:** 85
**Revenue:** ~€4.2M
**Country:** Germany
**Generated:** [Date of analysis]
**Report Version:** Rule Engine v1.0.0 | Prompt v1.2.0

> **Disclaimer:** This report is a preliminary compliance screening, not legal advice. Consult a qualified Rechtsanwalt before acting on these findings. Complio screens against 14 German/EU regulations using deterministic applicability rules and AI-powered gap analysis grounded in retrieved legal text.

---

## Compliance Score: 62/100

**Assessment completeness:** 81%

| Regulation | Applies | Score | Status |
|-----------|---------|-------|--------|
| GDPR / DSGVO | Yes | 58/100 | Partial |
| BDSG | Yes | 65/100 | Partial |
| NIS2 | Yes | 55/100 | Partial |
| EU AI Act | Yes | 40/100 | Action required |
| HinSchG | Yes | 70/100 | Partial |
| ArbSchG / Workplace | Yes | 75/100 | Partial |
| AGG | Yes | 90/100 | Good |
| MiLoG | Yes | 95/100 | Good |
| TTDSG / TDDDG | Yes | 60/100 | Partial |
| LkSG | No | — | Not applicable (86 employees) |
| EnEfG / EDL-G | No | — | Not applicable (SME) |
| CSRD | No | — | Not applicable (below threshold) |
| GwG | No | — | Not applicable (IT sector) |
| EU Data Act | No | — | Does not apply based on profile |

---

## Applicable Regulations — Applicability Rationale

**GDPR (applies):** Beispiel GmbH processes personal data of customers and employees as part of its software services. GDPR applies to all EU-based companies processing personal data of natural persons. *(Source: Art. 2, 3 GDPR)*

**BDSG (applies):** German supplement to GDPR. Applies to all companies in Germany processing personal data. Dedicated DPO required if ≥20 employees are constantly involved in automated data processing. *(Source: BDSG §38(1))*

**NIS2 (applies — wichtige Einrichtung):** IT software sector falls within NIS2 Annex II (digital providers). With 85 employees and ~€4.2M revenue, meets the "medium enterprise" threshold (≥50 employees or ≥€10M revenue per BSIG §28(7)). Classification: *wichtige Einrichtung*. *(Source: §28(7) BSIG, NIS2 Annex II)*

**EU AI Act (applies):** Company indicated use of AI systems in product and operations. Transparency obligations (Art. 50) active from August 2025. High-risk system obligations active from August 2026. *(Source: Regulation (EU) 2024/1689)*

**HinSchG (applies):** 85 employees exceeds the §12(2) HinSchG threshold of 50 employees — internal reporting channel required. *(Source: §12(2) HinSchG)*

**ArbSchG / Workplace law (applies):** Universal — all employers in Germany. *(Source: §1 ArbSchG)*

**AGG and MiLoG (applies):** Universal — all employers.

**TTDSG / TDDDG (applies):** Company operates a website. §25 TTDSG requires opt-in consent for non-essential cookies. *(Source: §25 TTDSG)*

---

## Gap Analysis

### GDPR / DSGVO

**Art. 30 — Records of Processing Activities**
- Status: NON_COMPLIANT (HIGH priority)
- Evidence: Company has not indicated it maintains a Verarbeitungsverzeichnis. With 85 employees and regular (non-occasional) data processing, Art. 30 requires a complete record of all processing activities including purpose, categories of data, recipients, and retention periods.
- Deficiency: No processing records in place. Must document all processing activities for the company's own operations and as a data processor for customer data.
- Statutory deadline: Immediate obligation (Art. 30 GDPR has been in force since May 2018)

**Art. 13/14 — Privacy Notice**
- Status: PARTIALLY_COMPLIANT (HIGH priority)
- Evidence: Website has a privacy notice, but the company has not confirmed it covers all mandatory information elements including: legal basis for each processing purpose, retention periods, data subject rights, third-party recipients, and controller contact details.
- Deficiency: Privacy notice may be incomplete or outdated.

**Art. 32 — Technical and Organisational Measures (TOMs)**
- Status: PARTIALLY_COMPLIANT (MEDIUM priority)
- Evidence: Company has some security measures but has not documented them as TOMs. Art. 32 requires documented measures appropriate to the risk.

**Art. 37/38 — Data Protection Officer**
- Status: CANNOT_ASSESS (MEDIUM priority)
- Evidence: With 85 employees in IT/software, it is likely that more than 20 employees are "constantly" involved in automated data processing of personal data. However, the exact count of employees in automated processing roles is not provided.
- Action required: Count employees whose primary job function involves automated personal data processing. If ≥20, appoint and register a DPO.

---

### NIS2 (wichtige Einrichtung)

**Art. 21 / §30 BSIG — Cybersecurity Risk Management Measures**
- Status: NON_COMPLIANT (CRITICAL priority)
- Evidence: Company has not indicated it has implemented the mandatory NIS2 risk management framework including: risk analysis documentation, incident handling policy, business continuity measures, supply chain security policy, network security measures, and regular security assessments.
- Deficiency: As a *wichtige Einrichtung*, all measures in §30 BSIG / Art. 21 NIS2 are mandatory. Implementation deadline was October 2024.
- Statutory deadline: Overdue — October 2024

**Art. 23 / §32 BSIG — Incident Reporting**
- Status: NON_COMPLIANT (HIGH priority)
- Evidence: No incident reporting procedure indicated.
- Deficiency: Must be able to report significant incidents to BSI within 24 hours (early warning), 72 hours (notification), and 1 month (final report). Three-step process must be documented and practiced.

**Art. 24 / §30(7) BSIG — Management Liability**
- Status: CANNOT_ASSESS (MEDIUM priority)
- Evidence: NIS2 imposes personal liability on management for cybersecurity failures. Requires management-level sign-off on the cybersecurity risk management framework.

---

### EU AI Act

**Art. 50 — Transparency Obligations for AI-Generated Content**
- Status: NON_COMPLIANT (HIGH priority)
- Evidence: Company uses AI systems but has not indicated it has implemented required transparency notices. Art. 50 requires informing users when they interact with AI systems (chatbots, AI-generated content).
- Deficiency: Add AI disclosure notices in all customer-facing AI interactions.
- Statutory deadline: August 2025 (active now)

**Art. 26 — Deployer Obligations for High-Risk AI Systems**
- Status: CANNOT_ASSESS (MEDIUM priority)
- Evidence: Whether the company deploys high-risk AI systems (Annex III categories) is not determinable from the profile. If yes, extensive obligations apply from August 2026.
- Action required: Review whether any AI systems used fall under Annex III (HR, credit, law enforcement, critical infrastructure, etc.).

---

### HinSchG (Whistleblower Protection)

**§12/13 HinSchG — Internal Reporting Channel**
- Status: NON_COMPLIANT (CRITICAL priority)
- Evidence: Company has not indicated it has an internal whistleblower reporting channel. All companies with ≥50 employees are required to maintain one.
- Deficiency: Must implement an accessible, confidential, anonymous reporting channel. External providers (anonymous hotline or web form) are acceptable.
- Statutory deadline: Overdue — December 2023 for 50–249 employee companies

---

### TTDSG / TDDDG

**§25 TTDSG — Cookie Consent**
- Status: PARTIALLY_COMPLIANT (MEDIUM priority)
- Evidence: Website has a cookie banner, but it is unclear whether it correctly implements opt-in consent (not opt-out) for non-essential cookies. Consent must be freely given, specific, informed, and unambiguous.
- Deficiency: Review cookie banner implementation — pre-ticked boxes or opt-out banners are non-compliant.

---

## Action Plan (Top 8 Items)

| Priority | Action | Effort | Deadline |
|---------|--------|--------|---------|
| CRITICAL | Implement NIS2 cybersecurity risk management framework (risk analysis, incident handling, supply chain policy, network security) | 4–8 weeks | Overdue (Oct 2024) |
| CRITICAL | Set up whistleblower reporting channel (HinSchG §12) — can use external provider | 1–2 weeks | Overdue (Dec 2023) |
| HIGH | Create Records of Processing Activities (Verarbeitungsverzeichnis) — Art. 30 GDPR | 8–16 hours | Immediate |
| HIGH | Implement NIS2 incident reporting procedure (24h/72h/1-month three-step) | 4–8 hours | Overdue |
| HIGH | Update privacy notice to include all Art. 13/14 mandatory elements | 4–8 hours | Immediate |
| HIGH | Add AI transparency notices (Art. 50 EU AI Act) in all AI-user interactions | 2–4 hours | Overdue (Aug 2025) |
| MEDIUM | Document Technical and Organisational Measures (TOMs) for GDPR Art. 32 | 4–8 hours | Immediate |
| MEDIUM | Review cookie banner for correct opt-in implementation (§25 TTDSG) | 2–4 hours | Immediate |

---

## Document Templates Available

Click to generate pre-filled templates for Beispiel GmbH:

- [ ] **GDPR Privacy Notice** (Art. 13/14) — website and internal
- [ ] **Records of Processing Activities** (Art. 30) — blank form with guidance
- [ ] **TOM Checklist** (Art. 32) — 40-item technical measures checklist
- [ ] **Incident Response Plan** (NIS2 Art. 23) — with 24h/72h/1-month procedure
- [ ] **Whistleblower Policy** (HinSchG §13) — channel description + procedure
- [ ] **AI Usage Policy** (EU AI Act Art. 26/50) — internal governance + transparency
- [ ] **AI System Inventory** (EU AI Act Art. 11) — register of AI systems used
- [ ] **NIS2 Risk Register** (Art. 21) — risk assessment framework

---

## Knowledge Base Audit Trail

This report was generated using the following legal knowledge base versions:

| Regulation | Source | Version hash | Fetched |
|-----------|--------|--------------|---------|
| GDPR / DSGVO | EUR-Lex, gesetze-im-internet.de | a3f7c2b1 | 2026-05-17 |
| NIS2 | EUR-Lex + BSI guidance | 9d1e4f82 | 2026-05-17 |
| HinSchG | gesetze-im-internet.de | b8c3a097 | 2026-05-17 |
| EU AI Act | EUR-Lex | 2f4e8d5c | 2026-05-17 |
| TTDSG | gesetze-im-internet.de | e5a1b3c9 | 2026-05-17 |
| AGG | gesetze-im-internet.de | 7b2d9f14 | 2026-05-17 |
| MiLoG | gesetze-im-internet.de | 4c8e2a56 | 2026-05-17 |
| ArbSchG | gesetze-im-internet.de | 1d5f7b38 | 2026-05-17 |

*Rule Engine version v1.0.0. This report can be reproduced with the same inputs and knowledge base version.*

---

*This is a sample report for demonstration purposes. Actual reports are generated live from the submitted company profile.*
