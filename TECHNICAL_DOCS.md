# Complio — Technical Documentation

> Autonomous regulatory compliance screening agent for German SMEs.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Repository Structure](#4-repository-structure)
5. [Data Models](#5-data-models)
6. [Analysis Pipeline](#6-analysis-pipeline)
7. [Knowledge Base (RAG)](#7-knowledge-base-rag)
8. [API Reference](#8-api-reference)
9. [Authentication](#9-authentication)
10. [Local Development Setup](#10-local-development-setup)
11. [Environment Variables](#11-environment-variables)
12. [Running the Services](#12-running-the-services)
13. [Database Migrations](#13-database-migrations)
14. [CI/CD](#14-cicd)
15. [Deployment](#15-deployment)
16. [Known Constraints & Watch-outs](#16-known-constraints--watch-outs)

---

## 1. System Overview

Complio takes a company profile (size, industry, activities, existing measures) and produces a full regulatory compliance screening report. It covers 11 German/EU regulations, determines applicability via hardcoded deterministic logic, retrieves relevant legal articles from a local vector database, runs an LLM gap analysis, and generates a scored PDF report.

**What it is:** A preliminary screening tool. Every report carries a legal disclaimer — it is not legal advice.

**What it is not:** A legal audit system, a law firm substitute, or a real-time regulation tracker.

---

## 2. Architecture

### 2.1 High-Level Components

```
Browser
  └── Next.js Frontend (port 3001)
        └── REST calls → FastAPI Backend (port 8000)
                          ├── Job Manager (async queue)
                          ├── Analysis Pipeline (6 steps)
                          │     ├── Threshold Engine (deterministic)
                          │     ├── RAG Retrieval (ChromaDB)
                          │     └── LLM Calls (Anthropic API)
                          ├── PDF Generator (Playwright/Chromium)
                          ├── Auth (Supabase JWT)
                          ├── Database (PostgreSQL via Supabase)
                          └── Stripe (subscriptions)

Worker Process (separate)
  └── APScheduler
        ├── Daily regulation change detection
        └── Scheduled re-assessments
```

### 2.2 Four-Module Agent Design

Following the Wang et al. (2024) agent architecture:

| Module | Role | Implementation |
|--------|------|----------------|
| **Profiling** | System persona + profile ingestion | `rag/prompts.py` SYSTEM_PERSONA, `agent/profiling.py` |
| **Memory** | Short-term (context) + Long-term (ChromaDB) | `rag/ingest.py`, `rag/retrieval.py` |
| **Planning** | Fixed 6-step pipeline, no freestyle | `agent/planning.py` |
| **Action** | Report assembly + PDF generation | `agent/actions.py`, `services/pdf_generator.py` |

### 2.3 Key Design Decisions

- **Threshold logic is always deterministic.** Regulation applicability is never delegated to an LLM. All thresholds are hardcoded in `services/threshold_engine.py` with statute citations.
- **LLM temperature = 0** on all compliance calls. Reproducibility over creativity.
- **Prompt injection protection** on all user-supplied free text fields. See `rag/prompts.py::_sanitize()`.
- **JSON fences stripped** before every `json.loads()` call. Anthropic models sometimes wrap JSON in markdown code blocks.
- **Per-regulation RAG** — retrieval is isolated per regulation (top-5 per regulation), so a dominant regulation cannot crowd out others.

---

## 3. Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Anthropic API — `claude-sonnet-4-6` |
| Embeddings | `intfloat/multilingual-e5-large` (local, HuggingFace) |
| Vector DB | ChromaDB (persistent, local) |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Auth | Supabase (JWT verification) |
| Database | PostgreSQL via Supabase + SQLAlchemy async |
| PDF | Playwright + Chromium (headless) |
| Email | Resend API |
| Payments | Stripe (subscriptions) |
| Scheduler | APScheduler in a separate `worker.py` process |
| Frontend | Next.js 14+, React, Tailwind CSS |
| Validation | Pydantic v2 |
| Testing | pytest |

---

## 4. Repository Structure

```
kmu-comply/
├── PLANNING.md                  # Architecture reference (original design doc)
├── TECHNICAL_DOCS.md            # This file
├── SESSION_LOG.md               # Session-by-session change log
├── .dev-notes.md                # Dev operational notes (read at session start)
├── docker-compose.yml
├── requirements.txt
│
├── backend/
│   ├── main.py                  # FastAPI app, all routes
│   ├── config.py                # Settings (pydantic-settings)
│   ├── worker.py                # APScheduler process (run separately)
│   │
│   ├── agent/
│   │   ├── profiling.py         # Step 1: profile enrichment (LLM)
│   │   ├── planning.py          # Steps 2-5: applicability → retrieval → gaps → actions
│   │   └── actions.py           # Step 6: report assembly, scoring, executive summary
│   │
│   ├── rag/
│   │   ├── ingest.py            # Document ingestion pipeline → ChromaDB
│   │   ├── retrieval.py         # Dense search + deduplication + LLM rerank
│   │   ├── prompts.py           # ALL prompt templates (no inline prompts elsewhere)
│   │   ├── embeddings.py        # multilingual-e5-large wrapper
│   │   └── company_ingest.py    # Per-job document upload → ChromaDB
│   │
│   ├── models/
│   │   ├── company_profile.py   # CompanyProfile + EnrichedCompanyProfile
│   │   ├── compliance_report.py # ComplianceReport + all sub-models
│   │   ├── enums.py             # Regulation, ComplianceStatus, Priority, etc.
│   │   └── api_responses.py     # FastAPI response models
│   │
│   ├── services/
│   │   ├── threshold_engine.py  # Deterministic applicability engine
│   │   ├── pdf_generator.py     # Playwright HTML→PDF renderer
│   │   ├── job_manager.py       # Async job queue + TTL
│   │   ├── report_store.py      # Persist reports to disk as JSON
│   │   ├── db_service.py        # DB helpers (companies, reports, jobs)
│   │   ├── stripe_service.py    # Checkout, webhooks, subscription queries
│   │   ├── auth_service.py      # Supabase JWT verification
│   │   ├── notification_service.py  # In-app notifications
│   │   ├── scheduler.py         # APScheduler job definitions
│   │   ├── document_store.py    # Temporary file store for uploads
│   │   └── section_hash_store.py    # Regulation change detection
│   │
│   ├── db/
│   │   ├── database.py          # SQLAlchemy async engine + session
│   │   └── models.py            # ORM models: Profile, Company, Report, Subscription
│   │
│   ├── data/
│   │   ├── regulations/         # Source text files per regulation
│   │   │   ├── gdpr/
│   │   │   ├── bdsg/
│   │   │   ├── lksg/
│   │   │   ├── enefg/
│   │   │   ├── csrd/
│   │   │   ├── nis2/
│   │   │   ├── eu_ai_act/
│   │   │   ├── hinschg/
│   │   │   ├── arbschg/         # Source files for workplace_law collection
│   │   │   ├── agg/
│   │   │   └── milog/
│   │   ├── chroma_db/           # ChromaDB persistent store (not in git)
│   │   ├── reports/             # Persisted report JSON files (not in git)
│   │   └── section_hashes.json  # Baseline hashes for change detection
│   │
│   ├── scripts/
│   │   ├── inspect_chunks.py    # Sample and QA-check ChromaDB collections
│   │   ├── eval_retrieval.py    # Retrieval quality evaluation (Top-1/Top-5)
│   │   └── build_section_hash_baseline.py  # Seed section hash baseline
│   │
│   └── tests/
│       ├── conftest.py          # 5 canonical test profiles (fixtures)
│       ├── test_thresholds.py   # Unit tests for threshold engine
│       ├── test_models.py       # Pydantic model validation tests
│       ├── test_rag.py          # RAG retrieval tests
│       └── test_pipeline.py     # Integration tests (requires LLM API key)
│
└── frontend/
    ├── src/app/
    │   ├── page.tsx             # Landing page
    │   ├── analyze/             # Multi-step profile form + processing view
    │   ├── report/[id]/         # Interactive report view + print layout
    │   ├── reports/             # Recent reports list
    │   ├── dashboard/           # Company dashboard
    │   ├── checkout/            # Stripe success/cancel pages
    │   └── account/             # Account settings + billing
    ├── src/components/
    │   ├── report/              # Gap analysis, action plan, score components
    │   └── ui/                  # Shared UI primitives
    └── src/lib/
        ├── api.ts               # All API calls (attaches auth token)
        └── types.ts             # TypeScript types mirroring backend models
```

---

## 5. Data Models

### 5.1 CompanyProfile

The input to every analysis. Fields are either required (`...`) or optional (`Optional[...]`). Optional `bool` fields (`None` = not answered) drive the gap analysis confidence scoring.

**Required fields:**

| Field | Type | Description |
|-------|------|-------------|
| `company_name` | str | 1–200 chars |
| `industry` | str | Sector (it_software, manufacturing, healthcare, retail, finance, logistics, construction, energy, food_beverage, consulting, other) |
| `employee_count` | int | 1–1,000,000 |
| `processes_personal_data` | bool | Triggers GDPR/BDSG applicability |

**Key optional fields (affect applicability):**

| Field | Type | Regulation |
|-------|------|-----------|
| `annual_revenue_eur` | float | CSRD, EnEfG/EDL-G, NIS2 |
| `balance_sheet_total_eur` | float | CSRD, EnEfG/EDL-G |
| `annual_energy_consumption_mwh` | float | EnEfG (EnMS vs audit split) |
| `is_critical_infrastructure_sector` | bool | NIS2 (KRITIS override) |
| `uses_ai_systems` | bool | EU AI Act |
| `ai_systems_are_high_risk` | bool | EU AI Act (Annex III) |
| `is_listed_company` | bool | CSRD Wave 3 |
| `has_supply_chain_abroad` | bool | LkSG indirect note |

**Optional compliance measure fields:** ~35 boolean fields (`has_privacy_policy`, `has_dpo`, `has_incident_response_plan`, etc.) — each maps to a specific legal article. `null` = unanswered, which reduces confidence on that gap finding.

### 5.2 ComplianceReport

```
ComplianceReport
├── job_id, company_name, generated_at
├── applicable_regulations: List[RegulationApplicability]
│     └── {regulation, applies, reason, key_threshold}
├── gap_analysis: List[ComplianceGap]
│     └── {regulation, article_number, article_title, status,
│           evidence, deficiency_description, confidence, source_url}
├── action_plan: List[ActionItem]
│     └── {regulation, article_number, action, priority,
│           estimated_effort, deadline, dependencies, gap_reference, source_url}
├── regulation_scores: List[RegulationScore]
│     └── {regulation, total_requirements, compliant, partially_compliant,
│           non_compliant, cannot_assess, score_percent}
├── overall_score_percent: float          # GDPR/BDSG weighted 1.5×
├── executive_summary: str               # LLM-generated, max 300 words
├── profile_completeness: dict           # {score, score_percent, answered, relevant, unanswered_fields}
├── knowledge_base_versions: dict        # {regulation: {fetched_at, source_file_hash, source_url}}
├── inferred_characteristics: List[str]
├── inferred_assumptions: List[str]      # Prefixed "ASSUMPTION:" — not sole basis for NON_COMPLIANT
├── validation_warnings: List[str]
├── missing_optional_fields: List[str]
├── requires_manual_review: List[str]    # Pipeline steps that fell back
└── disclaimer: str
```

**ComplianceStatus values:** `COMPLIANT` | `PARTIALLY_COMPLIANT` | `NON_COMPLIANT` | `CANNOT_ASSESS`

**Priority values:** `CRITICAL` | `HIGH` | `MEDIUM` | `LOW`

### 5.3 Regulation Enum

| Enum member | ChromaDB collection | Display label |
|-------------|--------------------|----|
| `GDPR` | `gdpr_dsgvo` | GDPR / DSGVO |
| `BDSG` | `bdsg` | BDSG |
| `NIS2` | `nis2` | NIS2 |
| `AI_ACT` | `eu_ai_act` | EU AI Act |
| `HINSCHG` | `hinschg` | HinSchG |
| `ARBSCHG` | `workplace_law` | Employment & Workplace Law |
| `AGG` | `agg` | AGG |
| `MILOG` | `milog` | MiLoG |
| `LKSG` | `lksg` | LkSG |
| `ENEFG` | `enefg` | EnEfG / EDL-G |
| `CSRD` | `csrd` | CSRD |

---

## 6. Analysis Pipeline

The pipeline runs in a background job (`job_manager.py`). Each step is discrete with defined inputs, outputs, and fallback behavior.

### Step 1 — Profile Enrichment (`agent/profiling.py`)

- **Input:** Raw `CompanyProfile`
- **Action:** LLM call (`max_tokens=4096`) infers implicit characteristics, flags missing data, identifies plausible but unconfirmed assumptions
- **Output:** `EnrichedCompanyProfile` with `inferred_characteristics`, `inferred_assumptions`, `validation_warnings`, `missing_optional_fields`
- **Fallback:** If LLM fails, pass through with empty enrichment lists

### Step 2 — Applicability Determination (`services/threshold_engine.py`)

- **Input:** `EnrichedCompanyProfile`
- **Action:** Deterministic threshold checks — never LLM. Each check function returns a typed result dataclass.
- **Output:** `List[RegulationApplicability]`
- **Key rule:** Threshold engine output is authoritative. The gap analysis prompt is explicitly told not to re-derive applicability from retrieved text.

**Threshold summary:**

| Regulation | Key trigger |
|-----------|------------|
| GDPR | `processes_personal_data = True` |
| BDSG | German company + processes personal data |
| NIS2 | Critical/important sector + ≥50 employees or ≥10M revenue; besonders wichtig if ≥250 employees/≥50M or KRITIS |
| EU AI Act | `uses_ai_systems = True`; high-risk obligations active from 2 Aug 2026 |
| HinSchG | ≥50 employees |
| ArbSchG/Workplace law | ≥1 employee (universal) |
| AGG | ≥1 employee (universal) |
| MiLoG | ≥1 employee (universal) |
| LkSG | ≥1,000 employees (direct), lower threshold may receive supplier questionnaires |
| EnEfG/EDL-G | Non-SME (≥250 employees OR >50M revenue OR >43M balance sheet) |
| CSRD | 2 of 3: >250 employees, >50M revenue, >25M balance sheet (Stop-the-clock: Wave 2 postponed to FY2027) |

### Step 3 — Regulatory Article Retrieval (`agent/planning.py → rag/retrieval.py`)

- **Input:** List of applicable regulations + enriched profile
- **Action:** Per-regulation dense retrieval (cosine similarity, `multilingual-e5-large`), top-15 raw, deduplicated, top-5 per regulation
- **Fallback:** If fewer than 5 chunks returned, retry with broader query. Log warning if still under 5.
- **Output:** `List[RegulatoryChunk]` — each chunk carries source authority level (Level 1 = law text, Level 2 = guidance)

### Step 4 — Gap Analysis (`agent/planning.py → rag/prompts.py`)

- **Input:** Retrieved chunks + enriched profile (+ optional company document chunks)
- **Action:** LLM call per regulation. Profile fields are treated as direct evidence (e.g. `has_privacy_policy=False` → NON_COMPLIANT on Art. 13/14 GDPR). Absence of a measure = NON_COMPLIANT, not CANNOT_ASSESS.
- **Output:** `List[ComplianceGap]` — status, evidence (plain English), deficiency description
- **AI Act phasing:** Until 2 Aug 2026, high-risk Annex III gaps are assessed as PARTIALLY_COMPLIANT with a "preparation required" note rather than NON_COMPLIANT. This is computed dynamically from `date.today()`.
- **CANNOT_ASSESS rule:** Only when information is genuinely unknowable. Evidence field must contain a specific question for the company to answer.

### Step 5 — Action Plan (`agent/planning.py`)

- **Input:** All NON_COMPLIANT and PARTIALLY_COMPLIANT gaps
- **Action:** LLM call generates concrete, article-specific actions with priority, estimated effort, statutory deadline (if applicable), and dependency chain
- **Output:** `List[ActionItem]` sorted by priority (CRITICAL → LOW)

### Step 6 — Report Assembly (`agent/actions.py`)

- **Action:** Computes per-regulation scores, weighted overall score (GDPR/BDSG: 1.5×), assigns gap confidence (HIGH/MEDIUM/LOW based on unanswered profile fields), stamps official source URLs on every gap and action, generates executive summary (LLM, max 300 words), assembles `ComplianceReport`
- **Persistence:** Report saved to `backend/data/reports/{job_id}.json` via `report_store.py`. Survives backend restarts.

---

## 7. Knowledge Base (RAG)

### 7.1 ChromaDB Collections

| Collection | Laws covered | Chunks | Source format |
|-----------|-------------|--------|--------------|
| `gdpr_dsgvo` | GDPR (German text) | ~106 | EU Artikel regex |
| `bdsg` | BDSG 2018 | ~27 | German § regex |
| `nis2` | NIS2 Directive | ~90 | EU Article regex |
| `eu_ai_act` | EU AI Act | ~159 | EU Article regex |
| `hinschg` | HinSchG | ~72 | Mixed (law + expanded) |
| `workplace_law` | ArbSchG, ArbZG, MuSchG, JArbSchG, BUrlG, BBiG, AEntG | ~115 | German § regex + expanded |
| `agg` | AGG | ~99 | German § regex |
| `milog` | MiLoG | ~51 | German § regex |
| `lksg` | LkSG | ~27 | German § regex |
| `enefg` | EnEfG | ~22 | German § regex |
| `csrd` | CSRD Directive | ~31 | EU Article regex |
| `compliance_guides` | EDPB + DPA guidance | ~927 | Section heading regex |

### 7.2 Chunking Strategy

Chunks at article/section level, never by arbitrary token count. Three format detectors:

- **Format A** (`_RE_GERMAN_A`): Standard `gesetze-im-internet.de` layout — `§ N\n` then title on next line
- **Format B** (`_RE_GERMAN_B`): SGB-style layout — `§ N[NBSP]Title` all on one line
- **EU format** (`_RE_EU_ARTIKEL` / `_RE_EU_ARTICLE`): `Artikel N` or `Article N`
- **Expanded format** (`_expanded.txt`): `---`-delimited blocks (curated summaries)

Max chunk size: ~6,000 chars (~1,500 tokens). Oversized articles split on Absatz markers `(1)`, `(2)`, etc.

Chunk minimum: 150 chars. Shorter chunks are dropped.

### 7.3 Re-ingesting a Collection

```bash
cd backend
python -c "from rag.ingest import ingest_regulation; ingest_regulation('workplace_law', reset=True)"
```

Replace `'workplace_law'` with any collection key from `REGULATION_COLLECTIONS` in `rag/ingest.py`. The `reset=True` flag deletes the existing collection before re-indexing.

Source files for `workplace_law` live in `data/regulations/arbschg/` (folder name unchanged on disk).

### 7.4 Retrieval Evaluation

```bash
cd backend
python scripts/eval_retrieval.py          # all regulations
python scripts/eval_retrieval.py -r nis2  # single regulation
python scripts/eval_retrieval.py -v       # verbose (shows missed cases)
```

Baseline (Session 18): Top-1 81%, Top-5 100%, Miss 0% across 48 test cases.

---

## 8. API Reference

All endpoints require a Bearer token in the `Authorization` header (Supabase JWT), except `/api/health`, `/api/webhook/stripe`, and `/api/contact`.

Base URL (local): `http://localhost:8000`

---

### Auth

#### `POST /api/auth/sync-profile`
Creates a profile row in the DB for a newly registered user. Call after Supabase sign-up.

**Response:** `{"ok": true}`

---

### Analysis

#### `POST /api/analyze`
Submit a company profile for compliance analysis.

**Request body:**
```json
{
  "profile": { ...CompanyProfile fields... },
  "doc_session_id": "optional-session-id-from-document-upload"
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "pending",
  "message": "Analysis job created. Use GET /api/status/{job_id} to track progress."
}
```

**Errors:**
- `402` — No active Stripe subscription (when `STRIPE_ENABLED=true`)
- `429` — Rate limit: max 10 screenings/hour per user. Includes `Retry-After` header.

---

#### `GET /api/status/{job_id}`
Poll analysis progress.

**Response:**
```json
{
  "job_id": "abc123",
  "status": "running",
  "current_step": "gap_analysis",
  "steps_completed": ["profile_validation", "applicability_determination", "article_retrieval"],
  "created_at": "2026-05-15T10:00:00Z"
}
```

Status values: `pending` | `running` | `completed` | `failed` | `partial`

---

#### `GET /api/report/{job_id}`
Fetch completed report as JSON.

**Response:** Full `ComplianceReport` object.

**Errors:**
- `202` — Report not ready yet (include current status)
- `404` — Job not found

---

#### `POST /api/report/{job_id}/pdf`
Generate and download the PDF report.

**Response:** `application/pdf` binary stream with `Content-Disposition: attachment; filename="complio-{company}.pdf"`

---

#### `GET /api/report/{job_id}/profile`
Retrieve the persisted company profile for a completed job (used for re-assessment pre-fill).

**Response:** `CompanyProfile` JSON.

---

#### `GET /api/reports`
List the current user's recent reports, newest first.

**Response:**
```json
{
  "reports": [
    {
      "job_id": "abc123",
      "company_name": "Acme GmbH",
      "generated_at": "2026-05-15T10:05:00Z",
      "overall_score_percent": 62.5,
      "regulation_count": 7
    }
  ]
}
```

---

### Documents

#### `POST /api/documents`
Upload company documents before analysis. Returns a `doc_session_id` to pass to `/api/analyze`.

**Request:** `multipart/form-data` with one or more files.

Accepted types: PDF, DOCX, TXT. Max size enforced by `document_store.py`.

**Response:**
```json
{
  "doc_session_id": "sess_xyz",
  "files_saved": ["privacy_policy.pdf"],
  "errors": []
}
```

---

### Companies

#### `GET /api/companies`
List all companies for the current user with their latest report score.

#### `GET /api/companies/{company_id}`
Company detail + full report history.

---

### Profile

#### `POST /api/profile/validate`
Validate a profile without running an analysis. Returns warnings for missing optional fields.

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Annual revenue not provided — CSRD and EnEfG/EDL-G applicability may be incomplete."],
  "enriched_profile": { ...EnrichedCompanyProfile... }
}
```

---

### Notifications

#### `GET /api/notifications`
All notifications for the current user.

#### `GET /api/notifications/unread-count`
Returns `{"count": N}`.

#### `POST /api/notifications/mark-read`
Mark all notifications as read.

---

### Billing (Stripe)

#### `POST /api/checkout`
Create a Stripe Checkout session.

**Request:**
```json
{
  "plan": "starter",
  "success_url": "http://localhost:3001/checkout/success",
  "cancel_url": "http://localhost:3001/checkout/cancel"
}
```

Plans: `starter` | `professional`

**Response:** `{"url": "https://checkout.stripe.com/..."}`

#### `GET /api/billing`
Get current subscription status.

#### `POST /api/billing/portal`
Get Stripe Customer Portal URL for subscription management.

#### `POST /api/webhook/stripe`
Stripe webhook receiver. Requires `Stripe-Signature` header.
Handles `checkout.session.completed` → provisions subscription.

---

### Utilities

#### `GET /api/health`
Health check. No auth required.

#### `GET /api/regulations`
List available regulations (static, for informational use).

#### `POST /api/contact`
Send a contact form email via Resend. No auth required. Rate-limited: 5 requests/hour per IP.

---

## 9. Authentication

Complio uses **Supabase** for auth. The frontend handles sign-up/sign-in via Supabase JS client. All protected backend endpoints verify the JWT via `services/auth_service.py::get_current_user()`.

The Supabase JWT is passed as:
```
Authorization: Bearer <supabase_jwt>
```

`get_optional_user()` is used on endpoints that work both authenticated and unauthenticated.

Job ownership is enforced: a user can only access reports from jobs they created (`_assert_owns_job()`). After backend restart, ownership is recovered from the `reports` table in the database.

---

## 10. Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Playwright Chromium (for PDF generation)

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Copy and fill env file
cp .env.example .env
# Set LLM_API_KEY and LLM_MODEL at minimum

# Set up ChromaDB data (downloads + ingests all regulations)
python setup_data.py

# Run backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Worker (scheduler — separate process)

```bash
cd backend
python worker.py
```

The worker runs APScheduler: daily regulation change detection and scheduled re-assessments. Not required for core analysis functionality.

### Frontend

```bash
cd frontend
npm install
npx next dev --port 3001
```

### Run Tests

```bash
cd backend

# Unit tests (no API key needed)
python -m pytest tests/test_thresholds.py tests/test_models.py tests/test_rag.py -v

# Integration tests (require LLM API key + ChromaDB populated)
python -m pytest tests/test_pipeline.py -m integration
```

### PDF Preview (no LLM required)

```bash
cd backend
python test_pdf_preview.py
# outputs preview_report.pdf
```

### Retrieval Evaluation

```bash
cd backend
python scripts/eval_retrieval.py
```

---

## 11. Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_API_KEY` | Yes | Anthropic API key |
| `LLM_MODEL` | Yes | e.g. `claude-sonnet-4-6` |
| `DATABASE_URL` | No | PostgreSQL async URL (`postgresql+asyncpg://...`). If unset, DB features are disabled gracefully. |
| `SUPABASE_URL` | No | Supabase project URL. Required for auth. |
| `SUPABASE_SERVICE_ROLE_KEY` | No | Supabase service role key for JWT verification. |
| `RESEND_API_KEY` | No | For contact form emails. |
| `CONTACT_EMAIL` | No | Destination for contact form. |
| `STRIPE_SECRET_KEY` | No | Stripe secret key (`sk_live_...` or `sk_test_...`). |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret (`whsec_...`). |
| `STRIPE_ENABLED` | No | `true` to enforce subscription gating on `/api/analyze`. |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins. Default: `http://localhost:3000,http://localhost:3001`. |
| `JOB_TTL_SECONDS` | No | In-memory job TTL. Default: `3600`. |
| `LLM_MAX_RETRIES` | No | LLM call retry count. Default: `4` (5 total attempts with exponential backoff). |
| `BASE_URL` | No | Public backend URL. Used by notification service. **Must be set before deploy.** |
| `CHROMA_SERVER_URL` | No | If set (e.g. `http://chroma:8001`), switches ChromaDB from embedded to server mode. Resolves single-writer contention and enables horizontal scaling. |
| `DOCUMENT_ENCRYPTION_KEY` | No | Fernet key for encrypting uploaded company documents at rest. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. If unset, an ephemeral key is used (dev only — lost on restart). **Must be set in production.** |
| `ADMIN_API_KEY` | No | API key for regulation update approval endpoints (`/api/admin/regulation-updates/*`). Set to a strong random value. If unset, admin endpoints return 403. |
| `SENTRY_DSN` | No | Sentry project DSN. When set, SDK captures all LLM failures, pipeline errors, and unhandled exceptions. `send_default_pii=False` — no personal data sent. |
| `ENVIRONMENT` | No | Set to `production` to enable hard startup checks (missing critical env vars cause process exit). Default: `development`. |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend URL. e.g. `http://localhost:8000` |
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Supabase anon key |
| `NEXT_PUBLIC_STRIPE_ENABLED` | No | `true` to show pricing gates in the UI |

---

## 12. Running the Services

### Kill Backend (Windows, PowerShell)

```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
```

### Re-ingest a Regulation Collection

```bash
cd backend
python -c "from rag.ingest import ingest_regulation; ingest_regulation('workplace_law', reset=True)"
```

Available collection keys (from `rag/ingest.py::REGULATION_COLLECTIONS`):
`gdpr`, `bdsg`, `nis2`, `eu_ai_act`, `hinschg`, `workplace_law`, `agg`, `milog`, `lksg`, `enefg`, `csrd`

### Inspect ChromaDB Collections

```bash
cd backend
python scripts/inspect_chunks.py
```

### Rebuild Section Hash Baseline (after re-ingest)

```bash
cd backend
python scripts/build_section_hash_baseline.py
```

---

## 13. Deployment

### Required Before Going Live

1. Set `BASE_URL` in `backend/.env` to the public backend URL (e.g. `https://api.complio.app`)
2. Set `ALLOWED_ORIGINS` to the production frontend URL
3. Set all Supabase variables
4. Provision a persistent volume for `backend/data/chroma_db/` (ChromaDB is file-based — it will not survive container restarts without a mounted volume)
5. Provision a persistent volume for `backend/data/reports/` (persisted report JSON)

### Frontend → Vercel

```bash
cd frontend
vercel deploy --prod
```

Set all `NEXT_PUBLIC_*` environment variables in the Vercel project settings.

### Backend

Any platform that supports Python + persistent storage:
- **Railway / Render / Fly.io** — mount a volume at `/app/backend/data/`
- **VPS** — systemd service for both `uvicorn` and `worker.py`

Backend does not use `--reload`. Changes require a kill + restart.

### Stripe Webhook Registration

After setting `STRIPE_SECRET_KEY`, register the webhook in the Stripe dashboard:
- Endpoint URL: `https://api.complio.app/api/webhook/stripe`
- Event: `checkout.session.completed`
- Copy the signing secret → set as `STRIPE_WEBHOOK_SECRET`
- Test with Stripe CLI before going live:
  ```bash
  stripe listen --forward-to localhost:8000/api/webhook/stripe
  ```

---

## 14. Known Constraints & Watch-outs

### Structured JSON Output via Tool Use

All LLM calls that return structured JSON use Anthropic's **tool use** feature (`tool_choice={"type":"tool","name":"..."}`) — the model is forced to return data matching the tool's JSON schema. `_strip_fences()` and manual `json.loads()` are removed from all JSON-parsing call sites. Any new LLM call returning JSON must also use tool use; fallback text-mode parsing is kept only as a safety net.

### ChromaDB Singleton

`rag/ingest.py` and `rag/retrieval.py` each maintain a module-level `_chroma` singleton. In embedded mode (default), cross-process visibility depends on ChromaDB's file persistence flush — a fresh process always reads the fully committed state. In server mode (`CHROMA_SERVER_URL` set), the singleton is an `HttpClient` and concurrent access is supported.

### Backend Restart Required

No `--reload` flag. Code changes require killing and restarting the uvicorn process. The same applies to the worker.

### Stripe Subscriptions (DB-backed)

Subscription state is fully persisted in the `subscriptions` PostgreSQL table, updated by the Stripe webhook handler. The backend checks `subscriptions.status` on every analyze request — no in-memory token store.

### AI Act Phasing (legally uncertain)

`services/threshold_engine.py` and `rag/prompts.py` compute `date.today() >= date(2026, 8, 2)` at runtime. The Digital Omnibus proposal (provisional EU agreement, Reuters 2025) may delay Annex III high-risk obligations to 2 December 2027. Until formally adopted in the EU Official Journal, the system treats the effective date as uncertain — reporting PARTIALLY_COMPLIANT with a date-uncertainty note rather than NON_COMPLIANT.

### NIS2 / BSIG Revenue Caveat

Revenue-only threshold (≥50M EUR) may not be sufficient for classification as "wichtige Einrichtung" in all sectors — some require balance sheet confirmation. This is flagged in the reason string but cannot be resolved without sector-specific guidance from BSI. The threshold engine notes this caveat.

### Rate Limits

- **Analysis:** 10 screenings / hour / user. When `DATABASE_URL` is set, call timestamps are written to the `rate_limit_events` table and survive restarts. In-memory fallback used only without a DB.
- **Contact form:** 5 requests / hour / IP — in-memory only (contact form is unauthenticated).

### Document Encryption Key

If `DOCUMENT_ENCRYPTION_KEY` is not set in production, an ephemeral Fernet key is generated per process startup. All encrypted documents uploaded during that process lifetime become unreadable after a restart. Set a stable key in production.

### Regulation Update Approval

The weekly official-source fetch creates `PendingRegulationUpdate` records. These do **not** automatically update the knowledge base — a human must call `POST /api/admin/regulation-updates/{id}/approve`. Annex-I regulations (GDPR, NIS2, EU AI Act, CSRD, LkSG) require **two different approvers** before ingestion proceeds. Approver identity (first 8 chars of key) and IP are logged on the record.

### Job Crash Recovery

On startup, the `lifespan` handler marks any `jobs` rows left in `running` status as `failed`. These represent analyses that were interrupted by a server restart. Users polling `GET /api/status/{job_id}` will see `failed` with a message to re-run. There is no automatic retry — in-flight state (document sessions, profile enrichment) cannot be reliably recovered.

### CANNOT_ASSESS Scoring

CANNOT_ASSESS items do **not** count toward the compliance score (`score_percent`). They reduce `assessment_completeness_percent` instead. A report with many CANNOT_ASSESS items will show a high compliance score for the assessed items but a low completeness score — both are displayed to the user. This is intentional: unknown compliance is not half-compliance.

### NIS2 Sector Ambiguity

Industries that don't match any BSIG Annex I or Annex II category (and have `is_critical_infrastructure_sector=False`) return a CANNOT_ASSESS NIS2 result with guidance to consult BSI sector classification. This is correct behavior — forcing a classification for an unknown sector would be legally unreliable.

### CSRD Wave Assignment

The wave is computed at analysis time using profile data. PIE status (Wave 1 trigger) requires both `is_listed_company=True` and `employee_count > 500`. Users who don't specify listing status may receive an incorrect Wave 2 assignment if they are actually PIEs. Advise users to set `is_listed_company` accurately.

### Injection Guard Failure Mode

The LLM injection classifier (`injection_guard.py`) is non-fatal on API failure — if the LLM call fails, the keyword check result is used as the fallback. This means a document that triggered the keyword filter but would have been cleared by the LLM classifier will be blocked. This is intentional: when in doubt, block.

---

## 15. Product Features Reference

### 15.1 User Onboarding

After registration, users are redirected to `/welcome` — a guided onboarding page with a 3-step visual guide and a feature summary. The dashboard shows `OnboardingEmpty` for users with no companies. The reports page shows a contextual empty state with dual CTA.

### 15.2 Document Template Generation

`POST /api/report/{job_id}/templates/{template_id}` generates a compliance document template personalised to the company profile. The `GET /api/templates` endpoint lists all 10 available templates with their regulation references. Templates are returned as Markdown and downloaded client-side.

Available template IDs: `privacy_notice`, `processing_records`, `tom_checklist`, `incident_response_plan`, `ai_usage_policy`, `ai_inventory`, `whistleblower_policy`, `safety_instruction`, `supplier_code_of_conduct`, `nis2_risk_register`.

### 15.3 Action Plan Workflow

The action plan supports three states per item: `open`, `in_progress`, `done`. Each item has `notes` and `evidence_note` fields. State is persisted via:
- `POST /api/report/{job_id}/completions` — upsert status/notes/evidence
- `GET /api/report/{job_id}/completions` — load all item states
- `DELETE /api/report/{job_id}/completions` — reset to open

### 15.4 Expert Review

`POST /api/expert-review` submits a review request with focus items (pre-populated from critical/high gaps) and an optional message. The request is stored in `expert_review_requests` and triggers an admin email via Resend. No payment is taken at submission. Users can check request status via `GET /api/expert-review`.

### 15.5 Legal Database Version Display

Every `ComplianceReport` includes `knowledge_base_versions`: a dict mapping each applicable regulation to `{fetched_at, source_file_hash, source_url}`. The report UI surfaces this in a collapsible table so users can see exactly which legal version underpinned their assessment.

### 15.6 Regulation Update Approval Workflow

`GET /api/admin/regulation-updates` — list all staged updates with status.
`POST /api/admin/regulation-updates/{id}/approve` — approve: copies staging file to production, re-ingests into ChromaDB.
`POST /api/admin/regulation-updates/{id}/reject` — reject and delete staging file.
`POST /api/admin/regulation-updates/fetch-now` — manually trigger a fetch outside the weekly schedule.
All endpoints require `X-Admin-Key` header matching `ADMIN_API_KEY`.

### 15.7 Subscription Plans and Billing

`GET /api/plans` returns the current plan configuration dynamically. Primary differentiator is company count and feature access.

**Plans:**
- `starter` — €49/month, 1 company, monthly re-assessment
- `professional` — €149/month, 5 companies, weekly re-assessment, templates + expert review
- `enterprise` — custom pricing, unlimited companies
- `starter_annual` — €470/year (~€39/month, ~20% off), 1 company
- `professional_annual` — €1,430/year (~€119/month, ~20% off), 5 companies
- `report_credit` — €19 one-time, 1 screening, no subscription

**Feature gates (when `STRIPE_ENABLED=true`):**
- Template generation: Professional+ only
- Expert review: Professional+ only
- Document upload: all plans

### 15.8 Hybrid Retrieval

`rag/retrieval.py` uses a hybrid BM25 + dense vector approach:
- Dense: cosine similarity via `multilingual-e5-large`
- BM25: approximate term-frequency scoring on the same candidate set
- Combined: `0.7 × dense + 0.3 × BM25`
- Per-collection tuned k: GDPR=10, NIS2=8, EU AI Act=8, workplace_law=8, BDSG=6, LkSG=6, EnEfG=5, MiLoG=5, others=6
- Similarity floor: 0.35 — chunks below this are dropped regardless of BM25
- Raw fetch: `k × 3` candidates fetched for BM25 re-ranking before final top-k selection

### 15.9 LLM Injection Guard

`services/injection_guard.py` provides two-stage injection detection for uploaded documents:
1. Keyword pre-filter — no LLM cost when clean
2. `claude-haiku` LLM classifier for suspicious text — returns confidence level
Applied at upload time (raw bytes preview) and again after PDF extraction (encoded injections).
