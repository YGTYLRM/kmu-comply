# Complio — Investor Brief

**Stage:** Pre-revenue, product complete, seeking first customers
**Market:** German B2B SaaS — compliance automation for SMEs
**Pricing:** [TBD — see pricing section]

---

## The Problem

Germany has over 3.5 million SMEs. Most have between 10 and 500 employees. Every single one of them is now subject to multiple layers of German and EU compliance law — and most don't know it.

In the last 3 years alone:
- **NIS2** entered German law in 2024 — affects an estimated 29,500+ companies, most of which have never done cybersecurity compliance
- **HinSchG** (Whistleblower Protection) — mandatory reporting channels for all companies with 50+ employees (~300,000 German companies)
- **LkSG** — Supply chain due diligence for 1,000+ employee companies since January 2024
- **EU AI Act** — phased obligations starting August 2025, applying to any company using AI systems
- **CSRD** — sustainability reporting expanding to mid-size companies by 2028

The typical SME reaction: ignore it and hope enforcement doesn't come. The alternative: hire a Rechtsanwalt at €300–500/hour, or a compliance consultant at €5–15k for a manual audit.

**There is no affordable automated option. Complio is building it.**

---

## The Solution

Complio answers two questions for any German SME:
1. **Which laws apply to us?** (deterministic, statute-cited, never AI-guessed)
2. **What are we missing?** (AI-powered gap analysis grounded in retrieved legal text)

A company fills in a 10-field profile. In under 3 minutes, they receive:
- A compliance score (0–100, deterministic)
- Article-level gap analysis across all applicable regulations
- A prioritized action plan with concrete steps and effort estimates
- A PDF report they can show to investors, auditors, or their board
- Compliance document templates pre-filled for their company

Ongoing monitoring re-runs the analysis on a schedule and alerts when regulations change.

---

## Market Size

**Total Addressable Market (TAM):** ~3.5M German SMEs with legal compliance obligations

**Serviceable Addressable Market (SAM):** ~500,000 SMEs with 10–500 employees who are actively subject to 3+ relevant regulations and have sufficient digital maturity to use a SaaS tool

**Serviceable Obtainable Market (SOM, Year 1–2):** ~5,000 customers at €[TBD]/month

**Market catalysts:**
- NIS2 enforcement starting 2024 (enforcement phase 2025–2026)
- HinSchG was poorly understood — many companies still non-compliant
- CSRD expanding to mid-size companies 2027–2028
- EU AI Act phased obligations create new uncertainty 2025–2026

---

## Business Model

**SaaS subscriptions** — monthly and annual billing via Stripe

| Plan | Price | Target customer |
|------|-------|----------------|
| Single Report | [TBD] | One-time compliance check; accountant run on behalf of client |
| Starter | [TBD]/month | 1–50 employee company, basic monitoring |
| Professional | [TBD]/month | 50–500 employee company, multi-company, weekly monitoring |
| Enterprise | Custom | Law firms, Steuerberater, compliance consultants (white-label potential) |

**Channel 1 — Direct (self-serve):** SMEs find Complio via search/content when researching NIS2, HinSchG, GDPR updates.

**Channel 2 — Accountants and Steuerberater (B2B2B):** Germany has ~100,000 Steuerberater who serve SME clients. A Steuerberater offering a Complio report as an add-on service to their existing SME clients is a high-leverage distribution channel.

**Channel 3 — Industry associations:** German Mittelstand organizations (BVMW, IHK, Handwerk) are actively looking for affordable compliance tools for their members.

---

## Competitive Landscape

| Competitor | Position | Why Complio wins |
|-----------|---------|-----------------|
| DataGuard | DPO tooling for compliance teams | Complio targets companies with NO compliance function; different buyer |
| Enactia | German GDPR/BaFin/NIS2, DPO-focused | Same narrow buyer; Complio covers 14 regulations in one tool |
| BRYTER | Enterprise no-code automation | Out of SME budget range |
| ComplyOne | EU-wide regulation identification | Pan-EU generic; Complio is German-specific and generates action plans |
| Law firms | Rechtsanwalt engagement | 100x more expensive; Complio is the screening before engaging a lawyer |
| Manual checklists | Spreadsheets and PDFs | No gap analysis, no monitoring, no ongoing updates |

**Complio's moat:**
- Proprietary knowledge base of German legal texts + regulatory guidance (DSK, BAFA, BSI, BaFin, ESRS)
- Deterministic threshold engine with verbatim legal citations — built once, hard to replicate correctly
- German-specific regulation coverage breadth (14 regulations, including German-only laws no EU-generic tool covers)

---

## Traction

**Product state:** Complete — 6 months of engineering, feature-complete, 219/220 tests passing

**Technical validation:** Three independent AI evaluations of the codebase (May 2026):
- Technical architecture: 7.5/10
- Product completeness: 6/10
- Legal reliability: 4/10 (⚠️ pre-security and legal accuracy fixes — current state significantly higher)
- Production readiness: 3.5/10 (pre-deploy)

**Note:** These scores were obtained before sessions 4-6 which added 17 security controls, the rule engine, 7 knowledge base expansions, and all architecture fixes. A re-evaluation would be expected to score significantly higher.

**Revenue:** Pre-revenue — seeking first 10 customers

---

## Roadmap

**Q2 2026 (immediate):**
- Restore Anthropic API credits → test live pipeline
- Deploy to production (Railway/Fly.io)
- First 10 customers

**Q3 2026:**
- Rechtsanwalt sign-off on threshold engine
- White-label tier for Steuerberater
- CSRD Omnibus resolution → update thresholds

**Q4 2026:**
- Mobile-friendly report view
- Direct API for accounting software integration (DATEV-compatible)
- First enterprise deal

**2027:**
- Austria and Switzerland expansion (similar regulatory framework)
- CSDDD (EU Corporate Sustainability Due Diligence) coverage as it enters force

---

## Ask

[Placeholder — founder to specify funding amount, use of funds, equity offer]

**Use of funds:**
- Legal: Rechtsanwalt threshold review (€5–10k)
- Marketing: Content and SEO targeting NIS2/HinSchG keywords
- Sales: First enterprise channel development (Steuerberater partnerships)
- Infrastructure: Production hosting, monitoring, backup systems

---

## Team

[Founder to fill in]

---

## Contact

[Founder to fill in]
