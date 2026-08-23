# Complio — Technical Architecture Summary

> Full detail in `../ARCHITECTURE.md`. This document is a structured summary for reviewers.

---

## Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Python 3.14, FastAPI, Uvicorn |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind |
| Vector database | ChromaDB (embedded or server mode) |
| Relational database | PostgreSQL via Supabase |
| Auth | Supabase JWT |
| Embeddings | `intfloat/multilingual-e5-large` (local, 1024-dim) |
| Reranker | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (local) |
| LLM | Anthropic Claude claude-sonnet-4-6 (gap analysis, action plan, enrichment) |
| Injection guard | Anthropic Claude Haiku 4.5 (fast classification sweep) |
| PDF generation | Playwright (headless Chromium) |
| Job queue | Celery + Redis (dev: asyncio fallback) |
| Payments | Stripe |
| Email | Resend |
| Monitoring | Sentry |

---

## Analysis Pipeline (6 Steps)

```
CompanyProfile (form input)
        │
        ▼
Step 1: Profile Enrichment (agent/profiling.py)
  - Validates required vs optional fields
  - LLM infers implicit characteristics
  - Fallback: deterministic-only if API unavailable
        │
        ▼
Step 2: Applicability Determination (services/threshold_engine.py + agent/rule_engine.py)
  - 14 deterministic regulation checks — NEVER LLM
  - Each function has verbatim statute citations as thresholds
  - RuleEngine adds: required_fields, missing_fields, confidence grade
  - Output: list[RegulationApplicability] with reasons
        │
        ▼
Step 3: RAG Retrieval (rag/retrieval.py)
  - Per applicable regulation: embed query → ChromaDB search
  - Hybrid: dense (70%) + BM25 (30%)
  - Cross-encoder reranking (top_n=5 per regulation)
  - Zero chunks → CANNOT_ASSESS (no LLM call)
  - 1-4 chunks → flagged for manual review
        │
        ▼
Step 4: Gap Analysis (agent/planning.py)
  - One LLM call per regulation (not global)
  - Retrieved chunks presented with source authority labels (Level 1/2/3)
  - Structured output via Anthropic tool use (enforces JSON schema)
  - Citation verification: LLM citations cross-checked against retrieved text
        │
Step 4b: Citation Verification (agent/validation.py)
  - Unverified citations downgraded + flagged for review
        │
        ▼
Step 5: Action Plan (agent/planning.py)
  - One LLM call for all NON_COMPLIANT + PARTIALLY_COMPLIANT gaps
  - Auto-batches if >50k estimated tokens
  - Sorted by priority: CRITICAL → HIGH → MEDIUM → LOW
        │
        ▼
Step 6: Report Assembly (agent/actions.py)
  - Deterministic score formula (no LLM)
  - KB version audit trail from ChromaDB metadata
  - rule_engine_version + prompt_version stamped
  - PDF generated via Playwright
        │
        ▼
ComplianceReport (JSON + PDF)
```

---

## Knowledge Base

**15 ChromaDB collections, 3,020 chunks** (as of 2026-05-17 ingest)

| Collection | Chunks | Key Sources |
|-----------|--------|-------------|
| compliance_guides | 1,569 | DSK orientations, CJEU rulings (Schrems II, Planet49), sector guides |
| workplace_law | 401 | ArbSchG, ArbZG, MuSchG, BBiG, BUrlG (all employers) |
| eu_ai_act | 160 | EU AI Act official text |
| csrd | 186 | CSRD + ESRS sector standards (not yet ingested) |
| gdpr_dsgvo | 114 | GDPR official text |
| agg | 99 | AGG |
| gwg | 97 | GwG + BaFin AML guidance (not yet ingested) |
| nis2 | 90 | NIS2 + BSI technical requirements (not yet ingested) |
| hinschg | 72 | HinSchG |
| eu_data_act | 70 | EU Data Act |
| milog | 51 | MiLoG |
| enefg | 22 | EnEfG + DENA guidance (not yet ingested) |
| lksg | 27 | LkSG + BAFA guidance (not yet ingested) |
| bdsg | 27 | BDSG |
| ttdsg | 35 | TTDSG/TDDDG |

**Note:** 7 new expanded guidance files are present in `backend/data/regulations/` but not yet ingested into ChromaDB. Ingestion requires the Anthropic API key to be active. After ingest, collections for NIS2, EnEfG, GwG, LkSG, CSRD, and compliance_guides will grow significantly.

**Chunking:** Regulation-specific parsers for German law (§N format), EU law (Article N format), and guidance documents. Deduplication handles the table-of-contents + body-text duplication from gesetze-im-internet.de. Oversized articles split on Absatz markers.

**Embedding prefix:** E5 requires `"passage: "` prefix on documents, `"query: "` on queries — both applied correctly.

---

## Deterministic vs LLM Boundaries

A key design decision: the LLM is strictly forbidden from applicability decisions.

| Decision type | Who decides | Why |
|--------------|-------------|-----|
| Does regulation X apply? | Deterministic Python | Legal thresholds cannot be LLM-guessed |
| What are the thresholds? | Hardcoded with citations | Reproducibility, no hallucination |
| Which articles are relevant? | RAG retrieval | Groundedness |
| What does the company's profile imply about compliance? | LLM (with retrieved context) | Requires contextual reasoning |
| What actions should be taken? | LLM (with gap context) | Requires practical judgment |
| What is the compliance score? | Deterministic formula | Reproducibility |

---

## Test Coverage

| Test suite | Count | Status |
|------------|-------|--------|
| Regulation threshold unit tests | 44 | All pass |
| Golden company profiles (deterministic) | 9 | Pass; 2 skipped (need API credits) |
| Rule engine (all 14 regulations) | 32 | All pass |
| Celery/Redis job state | 12 | All pass |
| Pipeline retrieval integration | 4 | All pass |
| CI retrieval quality | 42 | All pass |
| Website scanner | 21 | All pass |
| Citation verification | 6 | All pass |
| **Total (default run)** | **219 pass** | **1 skipped, 0 fail** |

Full retrieval eval suite (`-m retrieval_eval`, 261 cases): 248/261 pass. 13 failures are pre-existing retrieval quality gaps that will improve after KB ingest of the 7 new guidance files.

---

## Job Queue Architecture

**Dual mode:**
- **Production** (`REDIS_URL` set): Celery workers handle analysis and website scan tasks. Job state stored in Redis with TTL. Multiple workers can scale horizontally.
- **Development** (no `REDIS_URL`): Jobs run as asyncio tasks in-process. Same interface, no Redis dependency.

**Job lifecycle:** create → pending (DB row written) → running (step transitions persisted) → completed/failed. Crash recovery: on startup, jobs in `running` state are set to `failed`.

---

## Deployment Model

```
Frontend (Vercel)
    │
    ├── Next.js 14
    └── Supabase JS client (auth)

Backend (Any container platform with persistent volumes)
    │
    ├── FastAPI web server (port 8000)
    ├── Worker process (APScheduler — regulation monitoring, re-assessment)
    └── Celery worker (optional, when REDIS_URL set)

Shared storage
    ├── ChromaDB volume (chroma_db/)
    └── Report store volume (data/reports/)

External services
    ├── Supabase (PostgreSQL + Auth)
    ├── Anthropic API (LLM)
    ├── Stripe (billing)
    └── Resend (email)
```

**Minimum persistent volume mounts:** `backend/data/chroma_db/`, `backend/data/reports/`, `backend/data/section_hashes.json`
