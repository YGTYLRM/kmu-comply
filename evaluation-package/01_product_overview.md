# Complio — Product Overview

## What It Is

Complio is an AI-powered compliance screening and monitoring platform for German SMEs. It answers the question every small business faces after reading about NIS2, GDPR, or the Supply Chain Act: **"Which of these laws actually apply to me, and what do I have to do?"**

A company fills out a 10-field profile (industry, employee count, whether they process personal data, etc.). The system runs a deterministic applicability check against 14 regulations, retrieves the relevant legal articles from a local knowledge base, runs an LLM gap analysis comparing the company's stated measures against those obligations, and produces a scored compliance report with a prioritized action plan — in under 3 minutes.

The report is available as an interactive web view and a downloadable PDF. Ongoing monitoring re-runs the analysis on a schedule and alerts the company to regulation changes.

---

## Target Market

**Primary:** German SMEs with 10–500 employees who cannot afford a compliance lawyer but face increasing regulatory obligations (GDPR, NIS2, HinSchG, etc.).

**Secondary:** Accounting firms, business advisors, and Steuerberater who want to offer compliance screening as an add-on service to SME clients.

**Market size signal:**
- NIS2 came into force in Germany in 2024 — affects an estimated 29,500+ new companies
- HinSchG (whistleblower law) requires reporting channels at all companies with 50+ employees — ~300,000 companies in Germany
- CSRD sustainability reporting obligations are expanding to mid-sized companies by 2028
- Most of these companies have no compliance function and no budget for a Rechtsanwalt

---

## The Problem It Solves

German compliance has two speed bumps for SMEs:

1. **Discovery** — Which of the 14+ relevant German/EU regulations apply to their specific company? Threshold rules are complex (NIS2 sector taxonomy, CSRD wave cohorts, LkSG employee counting with subsidiaries and Leiharbeitnehmer). Getting this wrong is expensive.

2. **Gap analysis** — Once they know which laws apply, what specifically are they missing? A generic checklist is not useful; a company needs article-level findings tailored to their profile.

Complio automates both. The deterministic threshold engine handles discovery with verbatim legal citations. The RAG + LLM pipeline handles article-level gap analysis with cross-referenced retrieved legal text.

---

## What It Produces

For each company profile, Complio generates:

**1. Compliance Score** — A deterministic 0–100 score based on gap severity and missing information. Not LLM-generated; reproducible.

**2. Gap Analysis** — Per-regulation findings, each with:
- Article number and title
- Status: COMPLIANT / PARTIALLY_COMPLIANT / NON_COMPLIANT / CANNOT_ASSESS
- Evidence: what the company's profile implies about compliance
- Deficiency description: precisely what is missing

**3. Action Plan** — Prioritized (CRITICAL/HIGH/MEDIUM/LOW) concrete steps with estimated effort and statutory deadlines where applicable.

**4. PDF Report** — Branded, A4, professional-quality PDF with cover page, score ring, gap cards, action plan, and a knowledge base audit trail showing which legal version was used.

**5. Document Templates** — 10 compliance documents generated and pre-filled for the company (GDPR privacy notice, ROPA, TOM checklist, whistleblower policy, etc.).

**6. Monitoring** — Scheduled re-analysis (weekly for Professional, monthly for Starter) with delta comparison and email alerts when regulation texts change.

---

## Regulations Covered (14)

| Regulation | What it covers | SME trigger |
|-----------|----------------|-------------|
| GDPR / DSGVO | Data protection | Any company processing personal data |
| BDSG | German data protection supplement | Same as GDPR + German specifics |
| NIS2 / BSIG | Cybersecurity | 50+ employees in critical/important sectors |
| EU AI Act | AI system obligations | Companies using AI systems |
| HinSchG | Whistleblower reporting channels | 50+ employees |
| LkSG | Supply chain due diligence | 1,000+ employees (group) |
| EnEfG / EDL-G | Energy efficiency audits | Non-SME (250+ emp or >€50M revenue) |
| CSRD | Sustainability reporting | Large companies; expanding to mid-size 2028 |
| ArbSchG / ArbZG | Workplace safety and working time | All employers |
| AGG | Anti-discrimination | All employers |
| MiLoG | Minimum wage | All employers |
| TTDSG / TDDDG | Cookie consent and digital services | Any company with a website |
| GwG | Anti-money laundering | Finance, real estate, crypto, insurance sectors |
| EU Data Act | Data sharing obligations | Device manufacturers and digital services |

---

## Pricing (Subject to Change)

| Plan | Price | Companies | Re-assessment | Templates | Expert Review |
|------|-------|-----------|--------------|-----------|--------------|
| Single Report | [TBD] | 1 | None | No | No |
| Starter | [TBD]/month | 1 | Monthly | No | No |
| Professional | [TBD]/month | 5 | Weekly | Yes | Yes |
| Enterprise | Custom | Unlimited | Weekly | Yes | Yes |

All plans include: full 14-regulation gap analysis, action plan, PDF export, knowledge base audit trail.

---

## Key Differentiators

**1. Deterministic, not LLM-driven thresholds.** Every applicability decision is hardcoded Python with verbatim legal citations. The LLM never decides whether a law applies.

**2. Citation grounding.** The LLM only sees retrieved legal text from a local vector store. It cannot hallucinate articles that aren't in the knowledge base — regulations with empty KB return CANNOT_ASSESS rather than fabricated output.

**3. German-specific.** Coverage of German-specific laws (HinSchG, LkSG, BDSG, MiLoG, AGG, ArbSchG) that EU-generic tools miss. Threshold logic follows BSIG (not just NIS2 Directive), BAFA guidance for LkSG, BSI technical standards for NIS2.

**4. SME pricing.** Aimed at the market that cannot afford DataGuard, OneTrust, or a Rechtsanwalt retainer.

**5. Audit trail.** Every report stamps the legal knowledge base version used (ChromaDB collection metadata, SHA-256 hashes). Reproducible and defensible.
