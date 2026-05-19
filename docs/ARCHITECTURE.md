# Complio — Architecture

## Overview

Complio is a compliance screening SaaS for German SMEs. The core design principle is **deterministic where possible, LLM only where unavoidable**. Regulatory applicability and compliance scoring are fully deterministic; gap analysis and action planning use an LLM grounded in retrieved legal text with layered hallucination guards.

---

## Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend API | FastAPI (Python) | Async-native, easy dependency injection |
| Frontend | Next.js 14 (App Router) | Server components + Vercel deployment |
| Auth + DB | Supabase (PostgreSQL) | Built-in auth, RLS, managed Postgres |
| Vector store | ChromaDB (embedded) | Local dev simplicity; server mode for prod |
| Embeddings | multilingual-e5-large (local) | German text quality; no per-query cost |
| Reranker | cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 (local) | Improves retrieval precision post-embedding |
| LLM | Anthropic claude-sonnet-4-6 | German legal text quality, structured output via tool use |
| Injection guard | claude-haiku-4-5 | Fast, cheap sweep before document processing |
| Job queue | Redis + Celery (asyncio fallback for dev) | Horizontal scaling; dev works without Redis |
| PDF generation | Playwright/Chromium | Full-fidelity HTML→PDF |
| Billing | Stripe | Subscriptions + one-time payments |
| Email | Resend | Transactional notifications |
| Error tracking | Sentry | FastAPI SDK |
| Document encryption | Fernet (AES-128-CBC) | Uploaded company files encrypted at rest |

---

## Directory Structure

```
kmu-comply/
├── backend/
│   ├── agent/
│   │   ├── compliance_agent.py   # Pipeline orchestrator (steps 1-9)
│   │   ├── planning.py           # Steps 2-5: threshold, RAG, gap analysis, action plan
│   │   ├── profiling.py          # Step 1: profile enrichment
│   │   ├── validation.py         # Steps 4b-4c: citation + evidence quote checks
│   │   ├── actions.py            # Step 6: report assembly
│   │   ├── rule_engine.py        # Declarative rule engine (wraps threshold_engine)
│   │   └── obligations.py        # Regulation-specific obligation definitions
│   ├── models/
│   │   ├── company_profile.py    # CompanyProfile Pydantic model (~50 fields)
│   │   ├── compliance_report.py  # Report/gap/action Pydantic models
│   │   └── enums.py              # Regulation, Industry, ComplianceStatus, Priority enums
│   ├── rag/
│   │   ├── ingest.py             # KB ingestion: chunk, embed, store in ChromaDB
│   │   ├── retrieval.py          # Query ChromaDB + cross-encoder reranking
│   │   ├── prompts.py            # All LLM prompt templates (single source of truth)
│   │   └── company_ingest.py     # Uploaded document indexing (per-job collection)
│   ├── routes/
│   │   ├── analysis.py           # Core pipeline endpoints (POST /analyze, GET /status, etc.)
│   │   ├── misc.py               # Health, quick-check, contact, templates
│   │   ├── billing.py            # Stripe checkout + webhook
│   │   ├── companies.py          # Company/report management + GDPR deletion
│   │   ├── scanning.py           # POST /api/scan-website
│   │   └── expert_review.py      # Expert review request workflow
│   ├── services/
│   │   ├── threshold_engine.py   # Deterministic applicability checks (14 regulations)
│   │   ├── pdf_generator.py      # Playwright HTML→PDF with embedded Inter font
│   │   ├── auth_service.py       # JWT verification via Supabase
│   │   ├── stripe_service.py     # Subscription gating
│   │   ├── redis_store.py        # Job state in Redis (hset + list + TTL)
│   │   ├── job_manager.py        # Dual-mode JobManager (Redis or asyncio)
│   │   ├── document_store.py     # Encrypted document vault (7-day TTL)
│   │   ├── scheduler.py          # APScheduler: document ageing alerts, KB cleanup
│   │   └── website_scanner.py   # Playwright website compliance scan
│   ├── db/
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── database.py           # Async session factory
│   │   └── rls_policies.sql      # Supabase Row-Level Security (REQUIRED before launch)
│   ├── scripts/
│   │   ├── kb_health.py          # Validate ChromaDB collection counts
│   │   ├── apply_rls.py          # Apply RLS via psycopg2
│   │   └── download_fonts.py     # Regenerate embedded Inter WOFF2 base64
│   ├── data/
│   │   ├── chroma_db/            # ChromaDB persistent storage (volume mount in prod)
│   │   ├── knowledge_base/       # Source regulation text files (.txt)
│   │   └── threshold_versions.json  # Machine-readable threshold registry
│   └── config.py                 # Pydantic Settings (reads .env)
├── frontend/
│   └── src/app/                  # Next.js App Router pages
│       ├── page.tsx              # Landing page
│       ├── check/page.tsx        # Free applicability check (no auth)
│       ├── analyze/page.tsx      # Full analysis form (auth required)
│       ├── report/[id]/page.tsx  # Report viewer
│       ├── dashboard/page.tsx    # Report history
│       ├── account/settings/     # GDPR rights + data deletion
│       └── impressum|datenschutz|agb/  # Legal pages
└── docs/
    ├── ARCHITECTURE.md           # This file
    ├── DEPLOY.md                 # Step-by-step deployment runbook
    ├── INVESTOR_BRIEF.md         # Business overview
    ├── LEGAL_RISK_REVIEW.md      # Pre-launch legal risk analysis
    └── SAMPLE_REPORT.md          # Example report output
```

---

## Analysis Pipeline (9 steps)

```
User submits CompanyProfile
         │
         ▼
Step 1 ─ Profile Enrichment (claude-haiku-4-5 injection guard → claude-sonnet-4-6 enrichment)
         │  Infers implicit compliance-relevant characteristics.
         │  Inferred assumptions prefixed and kept separate from confirmed fields.
         ▼
Step 2 ─ Deterministic Applicability (threshold_engine.py — NO LLM)
         │  14 separate check functions, each with verbatim legal citations.
         │  Returns RegulationApplicability list: which regulations apply and why.
         │  CSRD Omnibus caveat surfaced here for Wave 2 companies below 1,000 emp/€450M.
         ▼
Step 3 ─ RAG Retrieval (multilingual-e5-large + cross-encoder reranker)
         │  For each applicable regulation: query ChromaDB → deduplicate → rerank top-5.
         │  If 0 chunks returned: regulation added to empty_regulations list → CANNOT_ASSESS.
         │  If <5 chunks after retry: flagged as low_confidence.
         ▼
Step 4 ─ Gap Analysis (claude-sonnet-4-6, structured output via Anthropic tool use)
         │  Per regulation: retrieved chunks + profile + optional company docs → ComplianceGap list.
         │  Regulations in empty_regulations get hard CANNOT_ASSESS without LLM call.
         │  Output fields: regulation, article_number, article_title, status,
         │    evidence (German), deficiency_description (German), evidence_quote (NEW),
         │    confidence (HIGH/MEDIUM/LOW), confidence_reason.
         ▼
Step 4b ─ Citation Verification (validation.py — deterministic)
         │  Cross-checks each gap's article_number against retrieved chunk article numbers.
         │  Unverified article → confidence downgraded to LOW.
         ▼
Step 4c ─ Evidence Quote Check (validation.py — deterministic)
         │  HIGH confidence gaps without evidence_quote → downgraded to MEDIUM.
         │  A missing verbatim quote on a HIGH-confidence finding signals possible hallucination.
         ▼
Step 5 ─ Action Plan (claude-sonnet-4-6, structured output via tool use)
         │  NON_COMPLIANT + PARTIALLY_COMPLIANT gaps → ActionItem list.
         │  Batched in groups of 50 if total gaps exceed token limit.
         │  Output: action (German), priority (CRITICAL/HIGH/MEDIUM/LOW),
         │    estimated_effort, deadline, dependencies, gap_reference.
         ▼
Step 6 ─ Report Assembly (deterministic)
         │  Assembles ComplianceReport from all prior outputs.
         │  Scores: deterministic formula (deductions per gap severity, missing fields).
         │  Adds KB audit trail (rule engine version, prompt version, source URLs per regulation).
         ▼
Step 7 ─ Self-Validation (validate_report — deterministic)
         │  Checks: every NON_COMPLIANT gap has an action, no orphan actions,
         │    data-protection violations not LOW priority, disclaimer present.
         │  Failures added to requires_manual_review list.
         ▼
Step 8 ─ Report Storage
         │  JSON report stored to disk (report store) + DB record.
         │  Job status updated to COMPLETE.
         ▼
Step 9 ─ PDF Generation (on-demand, Playwright/Chromium)
          HTML template → A4 PDF with embedded Inter font (no external CDN).
          Semaphore limits to 2 concurrent renders (OOM protection on 8GB VPS).
```

---

## Hallucination Guards

The system has four independent layers:

| Layer | Mechanism | What it catches |
|-------|-----------|-----------------|
| Zero-chunks guard | If RAG returns 0 chunks for a regulation → CANNOT_ASSESS, LLM never called | Completely empty KB collection |
| Citation verification | Article number in gap cross-checked against retrieved chunk article numbers | Fabricated article citations (e.g. citing Art. 99 when only Arts. 5-38 were retrieved) |
| Evidence quote check | HIGH-confidence gaps without verbatim chunk quote → downgraded to MEDIUM | Findings where the LLM couldn't produce a quote from the chunk it claimed to use |
| Confidence marking | Every gap carries VERIFIED/SELF-REPORTED/CANNOT_ASSESS with reason | Surfaces uncertainty in the PDF so users know which findings need verification |

---

## Deterministic Scoring Formula

Score starts at 100. Deductions:

| Condition | Deduction |
|-----------|-----------|
| NON_COMPLIANT + CRITICAL | -20 |
| NON_COMPLIANT + HIGH | -12 |
| NON_COMPLIANT + MEDIUM | -6 |
| NON_COMPLIANT + LOW | -2 |
| NON_COMPLIANT + LOW confidence (extra) | -3 |
| CANNOT_ASSESS | -4 |
| Missing required field (per field, capped at 5) | -5 |

Floor: 0. The formula is version-controlled (rule_engine_version in report).

---

## Knowledge Base

**15 ChromaDB collections**, ~3,020 chunks total:

| Collection | Source | Chunks |
|-----------|--------|--------|
| gdpr_dsgvo | EUR-Lex GDPR + DSK guidance | ~114 |
| compliance_guides | DSK, BSI, BAFA, BaFin, ESRS guidance | ~1,569 |
| nis2 | EUR-Lex NIS2 Directive | ~90 |
| eu_ai_act | EUR-Lex EU AI Act | ~160 |
| hinschg | gesetze-im-internet.de | ~72 |
| workplace_law | ArbSchG, ArbZG, MuSchG, JArbSchG | ~401 |
| agg | gesetze-im-internet.de | ~99 |
| milog | gesetze-im-internet.de | ~51 |
| bdsg | gesetze-im-internet.de | ~27 |
| lksg | gesetze-im-internet.de | ~27 |
| enefg | gesetze-im-internet.de | ~22 |
| csrd | EUR-Lex CSRD Directive | ~186 |
| ttdsg | gesetze-im-internet.de | ~35 |
| gwg | gesetze-im-internet.de | ~97 |
| eu_data_act | EUR-Lex EU Data Act | ~70 |

Run `python scripts/kb_health.py` to validate collection counts. Deep health endpoint: `GET /api/health/deep`.

---

## Job Queue

Dual-mode design:

- **Development** (`REDIS_URL` not set): `asyncio.create_task()` — jobs run in-process, state in memory
- **Production** (`REDIS_URL` set): Celery workers, job state in Redis (hset + list, TTL-controlled)

`JobManager` in `services/job_manager.py` abstracts the mode. Status routing: Redis → disk → DB (fallback chain).

---

## Billing

Stripe integration in `services/stripe_service.py`:

- `STRIPE_ENABLED=false` → all routes return 200 (dev mode)
- `STRIPE_ENABLED=true` → gated endpoints check subscription status
- Webhook at `POST /api/billing/webhook` handles subscription lifecycle events

Plan config in `PLAN_CONFIG` dict: `starter` (one-time), `professional` (monthly), `enterprise` (custom).

---

## Security

| Concern | Implementation |
|---------|---------------|
| Auth | Supabase JWT verified server-side on every request |
| Multi-tenancy | RLS policies in Supabase + job_owner check in backend |
| Document encryption | Fernet (AES-128) at rest in document store |
| Injection guard | Haiku sweep of uploaded documents (beginning + middle + end) |
| Prompt sanitization | Free-text profile fields sanitized before prompt embedding |
| Rate limiting | Per-user + per-endpoint rate limiting (in-memory, Redis in prod) |
| PDF XSS | `_esc()` HTML-escapes all report content before injecting into HTML template |
| Secrets | All secrets in `.env`, never in code |

---

## Legal Architecture

Complio positions outputs as **"preliminary compliance screening, not legal advice"** throughout:

- `SYSTEM_PERSONA` in prompts.py instructs German output + screening disclaimer on every LLM call
- PDF cover page carries German disclaimer ("Keine Rechtsberatung")
- AGB §2 explicitly states reports are automated screening, not Rechtsberatung per RDG
- Confidence markers (VERIFIED/SELF-REPORTED/CANNOT_ASSESS) make uncertainty visible
- Liability in AGB §9 capped at 12 months subscription fees for ordinary negligence

**Known legal uncertainty:** Whether automated gap analysis with statutory deadlines constitutes a Rechtsdienstleistung under RDG §2 requires legal opinion before commercial launch.

---

## Known Limitations and Technical Debt

| Item | Risk | Status |
|------|------|--------|
| ChromaDB is single-node embedded | No horizontal scaling for vector queries; server mode (`CHROMA_SERVER_URL`) available | Dev default; server mode for prod |
| Playwright semaphore=2 | Hard limit of 2 concurrent PDF renders on 8GB VPS | By design |
| CSRD threshold pre-Omnibus | Omnibus adoption pending; caveat added to Wave 2 output | Code flagged, needs legal update |
| BDSG DPO approximation | "≥20 employees + non-occasional" overstates in manual-heavy industries | Conservative, flagged in code, borderline cases warned |
| E2E tests skipped | 2 golden-profile E2E tests require API credits to run | Pending API credit top-up |
| No lawyer sign-off | Threshold engine not yet reviewed by Rechtsanwalt | Required before first paying customer |
