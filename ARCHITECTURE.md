# Complio — System Architecture

> Full architectural and technical documentation for evaluation purposes.
> Covers system design, component interactions, data flows, design decisions, and implementation detail.

---

## 1. System Purpose and Scope

Complio is an autonomous compliance screening agent for German small and medium-sized enterprises (SMEs). Given a company profile submitted through a web interface, the system determines which of 11 German and EU regulations apply to that company, retrieves the relevant legal obligations from a local vector knowledge base, runs a large language model (LLM) gap analysis comparing the company's stated measures against those obligations, and produces a scored compliance report in both interactive web and PDF form.

The system is not a legal audit tool. Every report carries an explicit disclaimer to this effect and is positioned as a preliminary screening instrument. The primary design constraint that flows from this is: **the LLM is never permitted to determine whether a regulation applies, or what its thresholds are.** All applicability decisions are made by deterministic, statute-cited code. The LLM is restricted to interpreting legal text in context of a specific company profile and producing structured output.

---

## 2. High-Level Architecture

### 2.1 Process Topology

The system runs as three distinct OS-level processes:

```
┌─────────────────────────────────────────────────────────────┐
│  Browser                                                    │
│  Next.js frontend (port 3001)                               │
│  - Supabase JS client handles auth                          │
│  - All backend calls via src/lib/api.ts                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS / REST
┌────────────────────────▼────────────────────────────────────┐
│  Process 1: FastAPI Web Server (port 8000)                  │
│  python -m uvicorn main:app --host 0.0.0.0 --port 8000     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Auth        │  │  Job Manager │  │  Analysis        │  │
│  │  (Supabase   │  │  (in-memory  │  │  Pipeline        │  │
│  │   JWT verify)│  │   async queue│  │  (6 steps)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Stripe      │  │  PDF         │  │  Report Store    │  │
│  │  (payments)  │  │  Generator   │  │  (disk JSON)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────┬───────────────┬───────────────┬───────────────┘
              │               │               │
    ┌─────────▼──┐  ┌─────────▼──┐  ┌────────▼───────┐
    │ ChromaDB   │  │ PostgreSQL │  │ Anthropic API  │
    │ (local,    │  │ (Supabase) │  │ (LLM calls)    │
    │  file-     │  │            │  │                │
    │  based)    │  └────────────┘  └────────────────┘
    └────────────┘

┌────────────────────────────────────────────────────────────┐
│  Process 2: Worker (scheduler)                             │
│  python worker.py                                          │
│                                                            │
│  APScheduler (AsyncIOScheduler)                            │
│  ├── 03:00 UTC daily — regulation change detection        │
│  └── 04:00 UTC daily — re-assessment cycle check          │
└────────────────────────────────────────────────────────────┘
```

The web server and worker are intentionally separate processes. The worker runs long-running re-ingest and re-analysis tasks that would block the web server's event loop. Both processes share the same ChromaDB directory on disk and the same PostgreSQL database.

### 2.2 External Service Dependencies

| Service | Role | Required |
|---------|------|----------|
| Anthropic API | LLM inference (all text generation and analysis) | Yes |
| Supabase Auth | User registration, login, JWT issuance | Yes (for multi-user) |
| Supabase PostgreSQL | Companies, reports, subscriptions, notifications | Yes (for persistence) |
| Stripe | Subscription billing, checkout sessions | No (toggled via `STRIPE_ENABLED`) |
| Resend | Transactional email (notifications, contact form) | No (degrades gracefully) |

---

## 3. Backend Architecture

### 3.1 Framework and Configuration

**FastAPI** (`main.py`) serves as the web framework. It uses an `asynccontextmanager` lifespan handler to initialize the database connection pool and start the job manager's cleanup loop on startup.

Configuration is managed by **pydantic-settings** (`config.py`). A single `Settings` instance is loaded once at import time from the `.env` file and made available as a module-level singleton (`settings`). Key parameters:

| Setting | Default | Purpose |
|---------|---------|---------|
| `llm_api_key` | — | Anthropic API key |
| `llm_model` | `gpt-4o` | Model ID (overridden to `claude-sonnet-4-6` in `.env`) |
| `llm_temperature` | `0.0` | Applied to all compliance LLM calls |
| `llm_max_retries` | `4` | Retry count for failed LLM calls (5 total attempts) |
| `llm_timeout_seconds` | `120` | API timeout |
| `job_ttl_seconds` | `3600` | In-memory job TTL |
| `max_concurrent_jobs` | `5` | Concurrent analysis limit |
| `embedding_model` | `intfloat/multilingual-e5-large` | Local embedding model |
| `stripe_enabled` | `false` | Subscription gating toggle |
| `database_url` | — | PostgreSQL async connection string |

**Middleware stack** (applied in order):
1. `CORSMiddleware` — allows configured origins, credentials, GET/POST/OPTIONS
2. `SecurityHeadersMiddleware` — adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`

### 3.2 Authentication

Authentication is handled by **Supabase**. The frontend uses the Supabase JavaScript client to sign in. The resulting JWT is attached to every backend request as `Authorization: Bearer <token>`.

`services/auth_service.py` provides two FastAPI dependencies:
- `get_current_user()` — verifies the JWT using the Supabase service role key, raises `401` if invalid
- `get_optional_user()` — same but returns `None` instead of raising, for endpoints that work unauthenticated

After a user registers, the frontend calls `POST /api/auth/sync-profile`, which creates a row in the `profiles` table (keyed by the Supabase user ID).

**Job ownership enforcement:** When a job is created, the user's ID is stored in `_job_owners: dict[str, str]` (in-memory). All report-access endpoints call `_assert_owns_job(job_id, user_id)`, which first checks the in-memory map, then falls back to querying the `reports` table in PostgreSQL (to handle post-restart access). If no owner record exists (legacy report), access is permitted.

### 3.3 Startup Cleanup

On startup, the lifespan handler calls `_cleanup_orphaned_chroma_collections()` before the database initializes. This scans ChromaDB for any collection whose name starts with `job_` — these are per-job company-document collections that were created during a previous process run that crashed or was killed mid-job. All orphaned collections are deleted and logged. This prevents unbounded disk growth from abandoned document ingestion sessions.

### 3.4 Rate Limiting

Two rate limiters are implemented in `main.py`:

- **Analysis rate limiter:** 10 screenings per user per hour. When `DATABASE_URL` is configured, call timestamps are written to the `rate_limit_events` table in PostgreSQL — this survives restarts and is consistent across processes. An in-memory `defaultdict(list)` fallback is used only when the DB is not configured. The table is pruned of rows older than 2 hours on every write. When the limit is reached, the response includes a `Retry-After` header and a human-readable wait time.
- **Contact form rate limiter:** 5 requests per IP per hour — in-memory only (contact form is unauthenticated, so user-keyed DB storage is not applicable).

### 3.4 Job Manager (`services/job_manager.py`)

The `JobManager` is an in-memory async job queue. When `POST /api/analyze` is called, `create_job()` generates a UUID, creates a `_Job` object, and immediately launches the pipeline as an `asyncio.Task` (non-blocking — the HTTP response returns the job ID before analysis begins).

**Job lifecycle:**

```
create_job()
    │
    ├── saves profile to disk (report_store.save_profile)
    ├── returns job_id to caller
    └── asyncio.create_task(_run_pipeline(job))

_run_pipeline(job)
    │
    ├── status = RUNNING
    ├── calls run_analysis() from agent/compliance_agent.py
    │       (6-step pipeline, each step updates job.current_step)
    ├── on success:
    │     ├── status = COMPLETED (or PARTIAL if requires_manual_review)
    │     ├── saves report to disk
    │     └── saves report to DB (if company_id exists)
    └── on failure:
          └── status = FAILED, stores error message
```

**Status resolution:** `get_status()` first checks the in-memory `_jobs` dict. If not found (job expired from TTL), it checks whether a report file exists on disk via `report_store.exists()`. This allows status queries on completed jobs that have been evicted from memory.

**TTL cleanup:** A background `asyncio.Task` runs every 5 minutes, evicting jobs older than `job_ttl_seconds`. On eviction, it also deletes the per-job ChromaDB collection for uploaded company documents and clears the temporary document store.

### 3.5 Report Persistence (`services/report_store.py`)

**PostgreSQL is the source of truth** when `DATABASE_URL` is configured. Disk (`backend/data/reports/`) is kept as a resilience backup only.

- **Write path:** `save()` writes to disk (fast backup). The DB write is performed by `job_manager` via `db_service.save_report_to_db()`, storing the full `ComplianceReport` JSON in the `reports.raw_json` column.
- **Read path (`load_async`):** Queries `reports.raw_json` by `job_id` first; falls back to disk if not found.
- **List path (`list_recent_async`):** Executes a single SQL query joining `reports` and `companies` on `user_id`, sorted by `created_at DESC`. O(1) regardless of report count — no filesystem scan.
- **Disk fallback:** All operations fall back to the disk scan if the DB is unavailable or not configured.

Company profiles are saved to `backend/data/reports/{job_id}_profile.json` (disk only — used for re-assessment pre-fill, not stored in the DB).

---

## 4. Analysis Pipeline

The pipeline is implemented in `agent/compliance_agent.py` (orchestration), `agent/profiling.py` (Step 1), `agent/planning.py` (Steps 2–5), and `agent/actions.py` (Step 6). Each step follows the same error contract: catch all exceptions, log them, append the step name to `failures: list[str]`, and continue. The report is never abandoned mid-pipeline.

### Step 1 — Profile Enrichment (`agent/profiling.py`)

**Input:** Raw `CompanyProfile` (Pydantic model, validated on receipt by FastAPI)

**Deterministic phase:**
- Checks three optional but applicability-critical fields (`annual_revenue_eur`, `balance_sheet_total_eur`, `annual_energy_consumption_mwh`)
- Generates a `missing_optional_fields` list and corresponding human-readable `validation_warnings`

**LLM phase:**
- Constructs the enrichment prompt via `rag/prompts.py::profile_enrichment_prompt()`
- LLM call: `max_tokens=4096`, `temperature=0`, system persona applied
- JSON fence stripping applied before `json.loads()` (Anthropic models sometimes wrap output in ` ```json ``` `)
- Expected JSON output:
  ```json
  {
    "inferred_characteristics": ["..."],
    "inferred_assumptions": ["ASSUMPTION: ..."],
    "validation_warnings": ["..."],
    "missing_optional_fields": ["field_name"]
  }
  ```
- `inferred_characteristics`: facts directly and logically implied by the profile (e.g. "company employs staff → ArbSchG applies")
- `inferred_assumptions`: plausible but unconfirmed inferences, always prefixed with `"ASSUMPTION:"`. The gap analysis prompt is later instructed that assumptions alone cannot be the basis for a NON_COMPLIANT finding.
- LLM-generated lists are merged with deterministic lists; duplicates removed with `dict.fromkeys()`

**Fallback:** If the LLM API key is absent or all retry attempts fail, the method returns an `EnrichedCompanyProfile` with only the deterministic enrichment (empty `inferred_characteristics`) and appends a warning: `"Automated profile enrichment failed — manual review recommended."` The pipeline continues normally.

**Retry logic:** `settings.llm_max_retries + 1` total attempts (default 3). Catches `json.JSONDecodeError`, `anthropic.APIError`, and generic `Exception` separately.

**Output:** `EnrichedCompanyProfile` — a subclass of `CompanyProfile` adding `inferred_characteristics`, `inferred_assumptions`, `missing_optional_fields`, `validation_warnings`.

---

### Step 2 — Applicability Determination (`services/threshold_engine.py`)

**Design principle:** This step never calls an LLM. All threshold logic is hardcoded Python with inline statute citations. The output of this step is the authoritative source of truth for which regulations apply. The gap analysis step is explicitly forbidden from re-deriving applicability.

Each regulation has a dedicated check function returning a typed frozen dataclass:

#### GDPR (`check_gdpr`)
- Applies if `processes_personal_data == True`
- DPO required if `employee_count >= 20` AND `NOT processing_is_occasional` (BDSG §38(1))
- Processing records required if `employee_count >= 250` OR `NOT processing_is_occasional` OR `processes_special_category_data` (Art. 30(5) GDPR)

#### BDSG (`check_bdsg`)
- Applies if `country == "DE"` AND `processes_personal_data == True`
- Cannot apply without GDPR also applying
- DPO threshold mirrors GDPR: ≥20 employees processing non-occasionally

#### NIS2 (`check_nis2`)
Implemented using German BSIG categories, not EU Directive terms:
- Sector check: `is_critical_infrastructure_sector == True` OR `industry in {energy, finance, healthcare, logistics, it_software}`
- If not in scope: does not apply
- **besonders wichtige Einrichtung** (§28(6) BSIG): `employee_count >= 250` OR `revenue >= 50M EUR` OR `is_critical_infrastructure_sector == True` (KRITIS override regardless of size)
- **wichtige Einrichtung** (§28(7) BSIG): `employee_count >= 50` OR `revenue >= 10M EUR`
- Revenue caveat: revenue alone may be insufficient for some sectors; flagged in reason string

#### EU AI Act (`check_ai_act`)
- Applies if `uses_ai_systems == True`
- Two boolean fields computed at runtime from `date.today()`:
  - `high_risk_obligations_active = today >= date(2026, 8, 2)`
  - `gpai_rules_active = today >= date(2025, 8, 2)`
- Reason string split into "Active now" and "Coming" sections reflecting the phased rollout (Art. 5 prohibitions Feb 2025, GPAI Aug 2025, high-risk Annex I/III Aug 2026, legacy Aug 2027)
- These booleans are passed through to the gap analysis prompt

#### HinSchG (`check_hinschg`)
- Applies if `employee_count >= 50` (§12(2) HinSchG)

#### Workplace Law / ArbSchG (`check_arbschg`)
- Applies if `employee_count >= 1` — universal employer obligation

#### AGG (`check_agg`)
- Applies if `employee_count >= 1` — universal

#### MiLoG (`check_milog`)
- Applies if `employee_count >= 1` — universal

#### LkSG (`check_lksg`)
- Directly applies if `employee_count >= 1000` (§1(1) LkSG, since Jan 2024)
- Indirect relevance note: companies below threshold may receive supplier questionnaires from LkSG-covered customers; flagged if `has_supply_chain_abroad == True` or `employee_count >= 500`

#### EnEfG / EDL-G (`check_enefg`)
- Non-SME gate: `employee_count >= 250` OR `revenue > 50M EUR` OR `balance_sheet > 43M EUR` (EU Recommendation 2003/361/EC)
- If non-SME:
  - EDL-G §8 audit (4-year energy audit, DIN EN 16247-1) is the baseline obligation
  - If `energy_consumption >= 7.5 GWh`: EnEfG §8(1) certified EnMS (ISO 50001/EMAS) is mandatory; this satisfies the EDL-G audit obligation
  - EnEfG §9: energy-saving measure implementation plans required above relevant thresholds
  - EnEfG §15: waste heat assessment required if technically usable waste heat ≥200 kW

#### CSRD (`check_csrd`)
- Large company: 2 of 3 size criteria met: `employees > 250`, `revenue > 50M EUR`, `balance_sheet > 25M EUR`
- Listed company: applies under Wave 3 regardless of size
- Stop-the-clock (Directive (EU) 2025/794): Wave 2 postponed to FY2027; flagged in reason string

**Output:** `List[RegulationApplicability]` — each entry has `regulation`, `applies`, `reason` (human-readable explanation citing the specific statute), `key_threshold` (the precise legal trigger).

---

### Step 3 — Regulatory Article Retrieval (`agent/planning.py`, `rag/retrieval.py`)

**Input:** `EnrichedCompanyProfile` + `List[RegulationApplicability]`

**Retrieval architecture:**

For each applicable regulation:
1. Constructs a tailored retrieval query via `_build_query()` — a regulation-specific function that combines industry context, employee count, and regulation-specific terminology. For example, NIS2 queries use BSIG terminology (`besonders wichtige Einrichtung`); workplace law queries include all 7 laws in the collection.
2. Calls `retrieve(query, [reg_key], top_k=15)` — dense semantic search against the regulation's ChromaDB collection
3. If fewer than 5 chunks returned, retries with a broader fallback query
4. Deduplicates results: for each `(regulation, article_number)` pair, keeps the highest-scoring chunk
5. Takes top-5 chunks per regulation

This per-regulation isolation is intentional: a global retrieval step with a single query could allow high-chunk-count collections (e.g. GDPR) to dominate, leaving other applicable regulations with insufficient context.

If company documents were uploaded, a second retrieval is performed against the per-job ChromaDB collection (`job_{job_id}`) for the same regulation query. These company document chunks are passed to the gap analysis as Level 3 evidence (evidence only, cannot override legal obligations).

**Source authority model:**
- Level 1 — Official law text (binding): always takes precedence
- Level 2 — Regulatory guidance (authoritative interpretation): explains how authorities apply the law
- Level 3 — Company documents (evidence only): shows what the company does; cannot waive a legal obligation

**Output:** `List[RegulatoryChunk]` — each chunk carries regulation, article number, title, text, obligation type (MUST/SHOULD/MAY), source URL, and document type (law/guidance).

---

### Step 4 — Gap Analysis (`agent/planning.py`, `rag/prompts.py`)

**Input:** Retrieved chunks + enriched profile + optional company document chunks

**LLM call pattern:** One LLM call per regulation (not one global call). This keeps context windows manageable and prevents cross-regulation interference.

**Prompt structure** (`gap_analysis_prompt()` in `rag/prompts.py`):

```
<task>        — role instruction
<applicability_notice>  — explicit instruction NOT to re-derive thresholds
<company_profile>       — sanitized JSON
<company_documents>     — if uploaded (Level 3 evidence)
<retrieved_regulations> — chunks with source authority labels
<instructions>          — status definitions, profile field mappings,
                          AI Act phasing note, CANNOT_ASSESS rules
```

**Profile field guidance:** The prompt contains an explicit mapping from 35+ profile boolean fields to their corresponding legal articles and expected compliance status outcomes. Example:
- `has_privacy_policy=false` → NON_COMPLIANT on Art. 13/14 GDPR
- `has_incident_response_plan=false` → NON_COMPLIANT on Art. 21(2)(b) NIS2
- `has_gefaehrdungsbeurteilung=false` → NON_COMPLIANT on §5 ArbSchG

The model is instructed to translate profile field states into plain-English evidence, never writing JSON field names in output.

**AI Act phasing (dynamic, legally uncertain):** The prompt computes `date.today() >= date(2026, 8, 2)` at call time and injects either:
- Before 2 Aug 2026: "High-risk obligations not yet active — assess as PARTIALLY_COMPLIANT with note on uncertain effective date (2 Aug 2026 under current law; Digital Omnibus proposal may delay Annex III to 2 Dec 2027, pending formal adoption in the EU Official Journal)"
- From 2 Aug 2026 onward: "Current law obligations active, but Digital Omnibus uncertainty flagged — assess as PARTIALLY_COMPLIANT until formal adoption resolves the date"

**CANNOT_ASSESS rule:** Only valid when information is genuinely unknowable from all available data. The evidence field must contain a specific, concrete question the company must answer. Absence of a compliance measure is NON_COMPLIANT, not CANNOT_ASSESS.

**Prompt injection protection:** All user-supplied free text fields (company name, industry, existing compliance notes, uploaded document content) are passed through `_sanitize()` before embedding in prompts. This function truncates, strips XML/HTML tags, and neutralizes injection keywords (`ignore`, `disregard`, `override`, `system prompt`, `new instruction`, `you are now`).

**Output:** `List[ComplianceGap]` — each gap has regulation, article number, article title, status, evidence (plain English), optional deficiency description (for NON_COMPLIANT and PARTIALLY_COMPLIANT), and confidence indicator (set in Step 6).

---

### Step 5 — Action Plan Generation (`agent/planning.py`)

**Input:** All gaps with status NON_COMPLIANT or PARTIALLY_COMPLIANT

**LLM call:** Single call with all actionable gaps. `max_tokens=8192` (action plans can be long for companies with many gaps).

**Priority assignment rules** (injected into the prompt):
- CRITICAL: legal deadline within 30 days, or active data breach risk
- HIGH: unimplemented legal obligation, any GDPR/BDSG data protection violation
- MEDIUM: partially met legal obligation, or best practice with meaningful risk reduction
- LOW: optional improvement, early preparation for upcoming requirements

**Output:** `List[ActionItem]` sorted by priority (CRITICAL → LOW), each with regulation, article number, concrete action text, priority, estimated effort string (e.g. "4-8 hours"), statutory deadline if applicable, dependency list, and a `gap_reference` pointing back to the originating `ComplianceGap`.

---

### Step 6 — Report Assembly (`agent/actions.py`)

**Gap confidence scoring:** For each gap, the system counts how many of the regulation's relevant profile fields were answered (`not None`). Ratio ≥0.8 → HIGH; ≥0.5 → MEDIUM; else LOW. CANNOT_ASSESS is always LOW. Regulations with no optional fields (ENEFG, CSRD) default to HIGH (assessed from structural data only).

**Score computation:**
- Per-regulation score: `(compliant × 100 + partial × 50 + cannot_assess × 50) / total_requirements`
- CANNOT_ASSESS is treated as 50% (neutral) — the system cannot determine compliance, not assumed non-compliant
- Overall weighted score: GDPR and BDSG weighted 1.5×, all others 1.0×
- Rationale: GDPR/BDSG represent the highest legal exposure and enforcement activity for German SMEs

**Source URL stamping:** Every `ComplianceGap` and `ActionItem` receives the official regulation URL from `_OFFICIAL_URLS` (e.g. EUR-Lex for GDPR, gesetze-im-internet.de for ArbSchG). This makes every finding traceable to its legal source.

**Knowledge base versioning:** For each applicable regulation, reads one chunk from ChromaDB to extract `fetched_at` (file modification timestamp proxy for download date) and `source_file_hash` (SHA-256 of the source file). Stored in the report as `knowledge_base_versions`. This makes reports auditable — readers know exactly which version of each law was used.

**Profile completeness:** Computes the ratio of answered compliance-measure fields across all regulation-relevant groups. Displayed as a warning on the PDF cover if below 70%.

**Executive summary:** LLM call (`max_tokens=512`) generating a 300-word summary following a fixed 4-sentence structure. Falls back to a deterministic template if the LLM fails.

**Output:** `ComplianceReport` — the fully assembled report object.

---

## 5. Knowledge Base Architecture

### 5.1 Embedding Model

`intfloat/multilingual-e5-large` is loaded locally via `sentence-transformers` and cached for the process lifetime with `@lru_cache(maxsize=1)`. It handles German legal text correctly — English-only models fail to retrieve German statute text reliably.

The model requires specific prefixes per the E5 paper:
- Document passages: `"passage: " + text`
- Retrieval queries: `"query: " + text`

Embeddings are L2-normalized (`normalize_embeddings=True`), producing unit vectors. ChromaDB uses cosine distance (`hnsw:space: cosine`). Cosine similarity is computed as `1.0 - distance` for scoring.

A fallback model (`sentence-transformers/paraphrase-multilingual-mpnet-base-v2`) is used if the primary model fails to load.

### 5.2 ChromaDB

ChromaDB can run in two modes, controlled by the `CHROMA_SERVER_URL` environment variable:
- **Embedded mode** (default, `CHROMA_SERVER_URL` unset): `PersistentClient` reads/writes directly to `backend/data/chroma_db/`. Single-writer; suitable for single-instance deployments.
- **Server mode** (`CHROMA_SERVER_URL=http://host:8001`): `HttpClient` connects to a separate ChromaDB server process. Supports concurrent access from multiple backend instances and the worker. No code changes required — only the environment variable.

Data is stored to `backend/data/chroma_db/` in embedded mode. The client is maintained as a module-level singleton in both `rag/ingest.py` and `rag/retrieval.py`.

**Collection structure:** One collection per regulation, plus one meta-collection for guidance documents. Each chunk is stored with metadata:

| Metadata field | Purpose |
|---------------|---------|
| `regulation` | Collection/regulation key |
| `article_number` | Section identifier (e.g. `§ 5`, `Art. 30`) |
| `paragraph` | Sub-paragraph index within article |
| `title` | Article title |
| `document_type` | `law` or `guidance` |
| `obligation_type` | `MUST`, `SHOULD`, `MAY`, `CONDITIONAL` |
| `source_file` | Filename of the source document |
| `source_url` | Official URL of the regulation |
| `fetched_at` | ISO-8601 timestamp of source file modification |
| `source_file_hash` | SHA-256 (first 16 chars) of source file |
| `content_hash` | SHA-256 (first 16 chars) of chunk text — for section-level change detection |

### 5.3 Chunking Pipeline

Source documents are stored in `backend/data/regulations/{regulation}/` as `.txt` or `.pdf` files. The ingest pipeline (`rag/ingest.py`) processes each file through a format-detection and chunking step.

**Format detection and routing:**

```python
if "_expanded" in path.stem:
    → _chunk_separator_blocks()   # Curated '---'-delimited blocks

elif regulation in German law set and path.suffix == ".txt":
    → _chunk_german_law()         # § N regex with format auto-detection

elif regulation in EU law set:
    → _chunk_eu_law()             # Artikel/Article N regex

elif regulation == "compliance_guides":
    → _chunk_german_law() or _chunk_guidance()

else:
    → _chunk_guidance()           # Numbered section headings
    → fallback: _chunk_fixed()    # Fixed 300-word chunks
```

**German law format detection** (`_chunk_german_law`): Two regex patterns are tested:
- Format A (`_RE_GERMAN_A`): `^§\s{1,3}(\d+[a-z]?)\s*\n` — standard layout, newline after section number
- Format B (`_RE_GERMAN_B`): `^§[ \t\xa0]{0,3}(\d+[a-z]?)([^\n]*)` — SGB-style, title inline with section number (non-breaking space separator)

Format B is chosen when it produces more than twice as many valid body matches as Format A. This reliably distinguishes SGB-style files from standard laws.

**Deduplication during chunking:** `gesetze-im-internet.de` pages contain both a table of contents and the full article text. Each section therefore appears twice in the downloaded file. The chunker deduplicates by section number, keeping the longer (full-text) match.

**Oversized article splitting** (`_split_oversized`): If a single article exceeds ~6,000 characters (~1,500 tokens), it is split on Absatz markers `(1)`, `(2)` etc. Each sub-chunk preserves the article header. If no Absatz markers exist, the article is split at word boundaries at the midpoint.

**Minimum chunk size:** 150 characters. Chunks below this threshold are dropped (stub entries, table of contents fragments, etc.).

**Provenance stamping** (`_stamp_provenance`): After chunking, every chunk receives `fetched_at`, `source_file_hash`, and `content_hash` metadata for auditability and change detection.

**Upsert batching:** Chunks are embedded and upserted to ChromaDB in batches of 32. IDs are deterministic: `{regulation}_{file_stem}_{batch_index + position}`.

### 5.4 Retrieval Quality

Evaluated against `backend/data/retrieval_eval.json`: 48 test cases covering all 11 regulations. Each test case specifies a natural-language question, the target regulation collection, and one or more expected article numbers.

Matching uses prefix normalization: "§ 12(1)" and "§ 12" are treated as equivalent; regulation prefixes ("arbschg §5" → "§5") are stripped.

**Baseline metrics (Session 18):**
- Top-1 accuracy: 81%
- Top-5 accuracy: 100%
- Miss rate: 0%

### 5.5 Company Document RAG

When a user uploads documents before running analysis, the files are:
1. Stored temporarily in `services/document_store.py` on disk
2. Parsed (PDF via pdfplumber with pypdf fallback, DOCX and TXT directly)
3. Ingested into a per-job ChromaDB collection named `job_{job_id}` using fixed-size chunking (300-word blocks)
4. Queried alongside the regulation knowledge base during Step 4
5. Cleaned up (collection deleted, files removed) when the job expires from TTL

Company document chunks are presented to the LLM as Level 3 evidence with explicit instructions that they cannot override legal obligations.

---

## 6. Prompt Engineering Architecture

All prompts live exclusively in `rag/prompts.py`. No inline prompt strings exist anywhere else in the codebase.

### 6.1 Structured Output via Tool Use

All LLM calls that return structured data use Anthropic's **tool use** feature with `tool_choice={"type": "tool", "name": "..."}`. This forces the model to return data matching a predefined JSON Schema — no manual fence stripping, no `json.loads()` fragility.

Three tool schemas are defined:
- `submit_gap_analysis` — returns `{"gaps": [...]}` matching `ComplianceGap` fields
- `submit_action_plan` — returns `{"actions": [...]}` matching `ActionItem` fields
- `submit_profile_enrichment` — returns `{"inferred_characteristics", "inferred_assumptions", "validation_warnings", "missing_optional_fields"}`

The tool's `input` dict is extracted from `response.content[0]` and the relevant key is serialized to a JSON string before passing to the existing `_parse_*` functions (unchanged interface). The `_strip_fences()` workaround is removed from all JSON-parsing call sites.

### 6.2 System Persona

A single `SYSTEM_PERSONA` string is applied to every LLM call:

```
"You are a Senior Regulatory Compliance Consultant specializing in German SME law."
```

The persona specifies: plain language (B2 level), specific article citations (never vague), concrete advice, explicit uncertainty acknowledgment, MUST/SHOULD/MAY distinction, realistic effort estimates, no hallucinated requirements.

Source authority hierarchy is embedded in the persona definition so it applies globally to all LLM calls.

### 6.2 Profile Enrichment Prompt

Structured with XML tags: `<task>`, `<company_profile>`, `<instructions>`. Returns structured JSON. Constraints distinguish `inferred_characteristics` (direct logical implication, high certainty) from `inferred_assumptions` (plausible but unconfirmed, must be ASSUMPTION-prefixed). Prevents re-stating explicit profile data.

### 6.3 Gap Analysis Prompt

The most complex prompt. Uses f-string construction with dynamic components:

- **`<applicability_notice>`:** Hardcoded block telling the model applicability is already decided. Prevents the model from re-reading size thresholds in retrieved text and second-guessing the threshold engine.
- **Profile field guidance:** 35+ field-to-article mappings telling the model exactly what compliance status each field state implies. This is a f-string and includes the dynamically computed AI Act phasing note.
- **`<unconfirmed_assumptions>`:** If Step 1 produced assumptions, they appear here with explicit instructions not to use them as sole basis for NON_COMPLIANT findings.
- **CANNOT_ASSESS rule:** Defined with a specific example of an acceptable CANNOT_ASSESS usage (asking a concrete question) versus unacceptable usage (treating missing documentation as unknowable).
- **Language rules:** The model is explicitly instructed never to write JSON field names (`has_dpo`, `employee_count=62`) in output — only plain English descriptions.

Input sanitization (`_sanitize_profile_json`) passes all free-text profile fields through the injection filter before embedding in the prompt.

### 6.4 Action Plan Prompt

Priority assignment rules are stated explicitly with examples. Actions must be concrete (not "document your data processing" but "create a Verarbeitungsverzeichnis listing X, Y, Z"). Every action must map to exactly one gap via `gap_reference`.

### 6.5 Executive Summary Prompt

Fixed structure: 4-sentence paragraph. Reports raw data (regulations, score, top findings) and generates flowing prose. Output is plain text, not JSON.

---

## 7. Database Architecture

### 7.1 ORM and Async Engine

SQLAlchemy 2.0 with async engine (`asyncpg` driver). `db/database.py` defines:
- `Base` — declarative base for all ORM models
- `AsyncSessionLocal` — async session factory
- `init_db()` — creates all tables on startup (called in the FastAPI lifespan handler)

### 7.2 Schema

**`profiles`**
- Primary key: Supabase user UUID (string, not generated by this system)
- Fields: name, email, created_at
- Relations: companies (1:N), notifications (1:N), subscription (1:1)

**`companies`**
- Mirrors `CompanyProfile` fields almost exactly (all ~50 compliance fields stored)
- Foreign key: `user_id → profiles.id`
- `updated_at` auto-updates on write
- Created/updated via `db_service.upsert_company()` — keyed on `(user_id, company_name)`, so re-submitting the same company updates rather than inserts

**`reports`**
- Foreign key: `company_id → companies.id`
- `job_id` — links to the job that produced it (unique, nullable for scheduled reports)
- `raw_json` — full `ComplianceReport` JSON stored in a JSON column for queryability
- `triggered_by` — `"manual"` | `"scheduled"` | `"reg_change"`

**`gap_items`**
- Denormalized subset of gap data linked to a report
- Enables efficient querying of gaps across reports without deserializing `raw_json`

**`action_items`**
- Linked to a company (not a report) — tracks ongoing action completion state
- `completed_at` set when the user marks an action done

**`subscriptions`**
- One per user (1:1 with profiles)
- Stores Stripe customer ID, subscription ID, plan, status, period end date
- Updated by the Stripe webhook handler on `checkout.session.completed`

**`notifications`**
- Created by the scheduler on re-assessment completion or regulation change
- `read_at` set by `POST /api/notifications/mark-read`

---

## 8. Monitoring and Scheduling Architecture

### 8.1 Worker Process

`worker.py` runs `start_scheduler()` from `services/scheduler.py`. This creates an `AsyncIOScheduler` with two cron jobs and starts it. The worker never starts the FastAPI web server — it runs the event loop in isolation.

### 8.2 Regulation Change Detection

**Trigger:** Daily at 03:00 UTC.

**Algorithm:**
1. SHA-256 hash of all `.txt` files under each regulation directory → `reg_hashes.json`
2. Compare against stored hashes from previous run
3. For each changed regulation:
   a. Load section hashes from `data/section_hashes.json` (pre-re-ingest state)
   b. Re-ingest the regulation into ChromaDB with `reset=True`
   c. Build new section hashes from the updated ChromaDB collection
   d. Diff: identify changed, added, and removed sections
   e. Save new section hashes as the new baseline
4. For each changed regulation, query the DB for all companies affected by that regulation
5. Launch `_run_scheduled_analysis()` as an asyncio task for each company

**Section hash store (`services/section_hash_store.py`):** Maps `{regulation → {article_number → content_hash}}`. The diff identifies which specific articles changed within a regulation update, allowing notification messages to cite the changed sections.

### 8.3 Re-assessment Cycle

**Trigger:** Daily at 04:00 UTC (runs daily; individual companies are skipped if not yet due).

**Logic:**
- Queries the DB for all companies whose most recent report is older than the plan's interval (7 days for Professional, 30 days for Starter)
- For each due company, runs the full 6-step analysis pipeline
- Saves the result to disk and DB
- Fetches the second-most-recent report for delta comparison (score change, improved/regressed gaps)
- Creates a notification in DB and sends an email via Resend

### 8.4 Scheduled Analysis Flow

Both triggers share `_run_scheduled_analysis()`:
1. Reconstruct `CompanyProfile` from the company's stored profile dict
2. Generate a new `job_id` (UUID)
3. Run the full pipeline via `run_analysis()`
4. Save report to disk (with `user_id` for ownership) and DB
5. Compute delta vs previous report
6. Save notification to `notifications` table
7. Send email via `notification_service.send_notification_email()`

---

## 9. PDF Generation Architecture

`services/pdf_generator.py` generates the PDF entirely from a `ComplianceReport` object with no additional LLM calls. The approach is:

1. **HTML construction:** Pure Python string concatenation building a full HTML document with inline styles. No external CSS files, no web fonts fetched at render time (fonts are loaded via Google Fonts CDN before the PDF is generated, or from cache).

2. **Playwright rendering:** The HTML is loaded into a headless Chromium instance via Playwright (`sync_playwright`). The page is set to 794×1123px (A4 at 96dpi). `page.pdf()` renders to A4 with zero margins (all spacing is in the HTML).

3. **Why Playwright over WeasyPrint/ReportLab:** CSS3 `border-radius`, `box-shadow`, `linear-gradient`, and `radial-gradient` work reliably. Complex layout (flexbox, multi-column tables) renders correctly. Chromium is the reference renderer.

**Known Chromium quirks handled:**
- `border-radius` on `<table>` elements with `border-collapse: collapse` is ignored by Chromium. Fix: wrap table in a `<div>` with `border-radius` applied to the div, `overflow: hidden`.
- Orphan headers (section title at bottom of page, content on next page): handled with a spacer `<div>` inside a `page-break-inside: avoid` wrapper rather than on the header element itself.

**Design system:**
- Cover: dark navy gradient (`#020817 → #0c1a45`), score ring with colored glow shadow
- Content pages: white body, dark navy header bar (`#0f172a`), 2.5pt blue gradient accent line, 3.5pt blue left-edge border
- Table headers: `#dbeafe` background, `#1e40af` text
- Gap cards: white body, colored left-border (green/amber/red by status), `box-shadow`
- Gap confidence badges: amber (MEDIUM), orange (LOW), none (HIGH)
- Fonts: Inter (Google Fonts), fallback Arial

**Logo embedding:** If `backend/assets/logo-dark-bg.png` exists, it is read and base64-encoded inline into the HTML. No network request during PDF generation.

---

## 10. Frontend Architecture

### 10.1 Routing

Next.js 14 App Router. Key routes:

| Route | Purpose |
|-------|---------|
| `/` | Landing page — value proposition, regulations list, pricing |
| `/analyze` | Multi-step company profile form (3 steps) |
| `/analyze/processing` | Job progress view, polls `/api/status/{job_id}` |
| `/report/[id]` | Interactive compliance report |
| `/report/[id]/print` | Print-optimized layout (stripped navbar) |
| `/reports` | Recent reports list |
| `/dashboard` | Company dashboard with score history |
| `/checkout/success` | Stripe post-payment success |
| `/checkout/cancel` | Stripe cancellation |
| `/account/billing` | Subscription management (Stripe Customer Portal) |

### 10.2 API Client (`src/lib/api.ts`)

All backend calls flow through a single module that:
- Reads the Supabase session to get the JWT
- Attaches `Authorization: Bearer <token>` to every request
- Attaches `X-Access-Token` (Stripe access token, when applicable) from localStorage
- Handles JSON serialization and error parsing

### 10.3 State Management

No global state library. State is component-local with React hooks. The analyze flow uses `useRouter` for navigation and browser `sessionStorage` for transient job ID tracking between pages. Action task completion state is stored in `localStorage` per job ID.

### 10.4 Design System

Dark premium aesthetic for the main UI:
- Background: `bg-dark-950` (`#03071a`)
- Cards: `rgba(10,22,40,0.75)` + `border-white/[0.07]`
- Accent: `blue-600` (`#2563eb`) with glow effects
- Animations: Framer Motion (page transitions, card entrances)
- Font: Inter

---

## 11. Security Architecture

### 11.1 Authentication and Authorization
- All state-mutating and data-access endpoints require a valid Supabase JWT
- JWT expiry is enforced by Supabase; the backend does not issue tokens
- Job ownership enforced per request (not just at job creation)

### 11.2 Input Validation
- All request bodies validated by Pydantic v2 models with field constraints
- String fields have explicit `max_length` constraints
- Numeric fields have `ge`/`le` constraints
- Free text fields (company name, compliance notes) sanitized via `_sanitize()` before prompt embedding

### 11.3 Prompt Injection Protection
- `_sanitize()` strips XML/HTML tags, truncates at configured max lengths, and replaces injection keywords with `[removed]`
- Uploaded document content is run through the same sanitizer before being embedded in prompts
- The `<applicability_notice>` block in the gap analysis prompt provides defense-in-depth against prompt injection attempting to override applicability decisions

### 11.4 Uploaded Document Encryption

Company-uploaded files are encrypted at rest using **Fernet** (AES-128-CBC + HMAC-SHA256, from the `cryptography` package). The encryption key is read from `DOCUMENT_ENCRYPTION_KEY` in the environment. If not set, an ephemeral key is generated per process startup (acceptable in dev; set in production).

Files are stored as `{filename}.enc` in a per-session temp directory. Decryption happens in memory via `document_store.read_file()` — plaintext bytes are passed directly to text extraction (`pdfplumber` via `io.BytesIO`), never written to disk unencrypted. The per-session directory is wiped by the job TTL cleanup.

### 11.5 Stripe Webhook Verification
- Stripe-Signature header verified using `stripe_webhook_secret` before any event processing
- Redirect URLs in checkout requests validated against the allowed origins list

### 11.5 Response Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

---

## 12. Error Handling and Resilience

### 12.1 LLM Call Failure Handling

All LLM calls use the same pattern with exponential backoff (5 total attempts, delays of 1s/2s/4s/8s):
```
for attempt in range(max_retries + 1):   # default: 5 total
    try:
        response = llm_client().messages.create(...)
        return parse(response)
    except JSONDecodeError: log + retry
    except anthropic.APIError: log + retry
    except Exception: log + retry
    if not last attempt: sleep(2 ** attempt)  # 1s, 2s, 4s, 8s

log failure
append step_name to failures list
return [] (empty result, pipeline continues)
```

No step is terminal. A failed gap analysis for one regulation produces no gaps for that regulation (the report is marked PARTIAL, not FAILED). The user sees which steps required manual review.

### 12.2 RAG Retrieval Failure Handling

If a regulation collection is empty or missing in ChromaDB, `retrieve()` logs a warning and returns an empty list. The pipeline continues with no chunks for that regulation, resulting in CANNOT_ASSESS findings for all its requirements.

### 12.3 Pipeline Isolation

Each analysis step runs in a try/except. A failure in Step 4 for regulation X does not affect Step 4 for regulation Y, because gap analysis runs per regulation in separate LLM calls.

### 12.4 Database Failure Handling

All database operations in the main analysis pipeline are wrapped in try/except with "non-fatal" semantics: if the DB is unavailable, the analysis still runs and the report is saved to disk. Only DB-dependent features (monitoring, notifications, subscription enforcement) are affected.

---

## 13. Testing Architecture

**Test profiles** (`tests/conftest.py`) — five canonical fixtures designed to cover the full applicability spectrum:

| Profile | Employees | Key characteristics |
|---------|-----------|-------------------|
| `profile_it_agency` | 5 | Processes personal data; GDPR/BDSG only |
| `profile_manufacturer` | 500 | Supply chain abroad, high energy (10,000 MWh), non-SME |
| `profile_large_listed` | 1,500 | All regulations apply, listed company |
| `profile_freelancer` | 1 | Minimal obligations, occasional processing |
| `profile_healthcare` | 50 | Special category data, NIS2-adjacent |

**`test_thresholds.py`:** Unit tests for every regulation's applicability threshold, boundary conditions, and reason string content. Deterministic — no LLM required.

**`test_models.py`:** Pydantic model validation tests — required fields, type coercion, validator behavior.

**`test_rag.py`:** ChromaDB retrieval tests — requires a populated ChromaDB instance.

**`test_pipeline.py`:** Integration tests running the full 6-step pipeline. Marked `@pytest.mark.integration` — require a live LLM API key and populated ChromaDB. Separated from unit tests to allow CI to run units only.

---

## 14. Deployment Architecture

### 14.1 Process Management

In production, both `uvicorn` (web server) and `python worker.py` (scheduler) should be managed by a process supervisor (systemd, Docker Compose, or platform equivalents). The worker must be restarted alongside the web server on code changes.

### 14.2 Persistent Storage Requirements

ChromaDB and the report JSON store are file-based and **must** be on a persistent volume. Container restarts without volume mounts will wipe all indexed knowledge and all saved reports. Minimum required mounts:
- `backend/data/chroma_db/` — ChromaDB collections (~GB-scale depending on regulation count)
- `backend/data/reports/` — report JSON files
- `backend/data/section_hashes.json` — regulation change detection baseline

### 14.3 ChromaDB Scalability Note

ChromaDB in embedded (file-based) mode is single-writer. Concurrent writes from the web server and worker can produce contention. At scale, migrating to ChromaDB server mode or a managed vector database (Pinecone, Weaviate) would be necessary. For the current single-tenant deployment scale, embedded mode is sufficient.

### 14.4 Environment Split

| Component | Platform |
|-----------|---------|
| Frontend | Vercel |
| Backend + Worker | Any container platform with persistent volumes |
| Database | Supabase (managed PostgreSQL) |
| ChromaDB | Co-located with backend (same container/VM) |

The `BASE_URL` environment variable must be set to the public backend URL before deploy — it is used by `notification_service.py` to construct report links in email notifications.
