# KMU-Comply: Autonomous Regulatory Compliance Agent for German SMEs

## Mission
Build a production-grade autonomous AI agent that takes a German SME's company profile and delivers a comprehensive, accurate regulatory compliance analysis with zero errors, clear actionable recommendations, and professional-quality output. This is not a toy prototype — it must be reliable enough to become a commercial product.

---

## Product Vision
KMU-Comply is an end-to-end compliance assistant. An SME owner with zero legal knowledge should be able to:
1. Enter their company details in a clean, guided form
2. Click "Analyze"
3. Receive a professional compliance report within 2 minutes
4. Understand exactly what they need to do, in what order, and why

The agent must NEVER hallucinate legal requirements. Every claim must trace back to a specific article or paragraph in the regulatory source documents stored in the knowledge base. If the agent is uncertain, it must say so explicitly rather than guess.

---

## Architecture: Four-Module Design (Wang et al., 2024)

### Module 1: Profiling
The agent operates as a Senior Regulatory Compliance Consultant specializing in German SME law.

System prompt persona characteristics:
- Speaks in clear, plain language (B2 German level / professional English — no legalese)
- Always cites specific regulatory articles (e.g., "Art. 30 DSGVO" not "GDPR requires documentation")
- Never gives vague advice like "you should consider..." — always concrete: "You must create a Record of Processing Activities (Verarbeitungsverzeichnis) per Art. 30 DSGVO. Here is what it must contain: [list]"
- Acknowledges uncertainty explicitly: "Based on your profile, this regulation likely applies, but a qualified legal review is recommended for [specific reason]"
- Distinguishes between MUST (legal obligation), SHOULD (best practice), and MAY (optional recommendation)
- Provides estimated effort/cost ranges for each recommendation

Profile is injected via system prompt at every LLM call. Never rely on the model "remembering" the role.

### Module 2: Memory (Hybrid Architecture)

#### Short-Term Memory (Context Window)
- Current company profile being analyzed
- Current step in the analysis pipeline
- Intermediate results from previous steps
- Conversation history if user asks follow-up questions
- Max context budget: Reserve 40% for RAG results, 20% for system prompt + profile, 20% for intermediate state, 20% for generation

#### Long-Term Memory (ChromaDB)
Collection structure — one collection per regulation, plus one meta-collection:

- collection: gdpr_dsgvo (GDPR full text, chunked)
- collection: lksg (Supply Chain Due Diligence Act)
- collection: enefg (Energy Efficiency Act)
- collection: csrd (Corporate Sustainability Reporting Directive)
- collection: bdsg (Bundesdatenschutzgesetz)
- collection: compliance_guides (Official guidance documents, DPA opinions, checklists)
- collection: past_assessments (Previously completed assessments for learning - future feature)

Chunking strategy (CRITICAL — bad chunking = bad retrieval = bad output):
- Chunk by legal article/paragraph, NOT by arbitrary token count
- Each chunk = one complete article or numbered paragraph
- Metadata per chunk MUST include: regulation, article_number, paragraph, title, applicable_to (list of company characteristics that trigger this article), obligation_type (MUST/SHOULD/CONDITIONAL), threshold (any size/revenue/employee thresholds), last_updated, source_url
- Chunk overlap: 0 (legal articles are self-contained units)
- If an article is longer than 1500 tokens, split by numbered paragraph (Absatz) within that article
- ALWAYS preserve the full article number and title in every sub-chunk

Embedding model:
- Use intfloat/multilingual-e5-large — handles German legal text well
- Fallback: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
- NEVER use English-only embedding models for German legal text

Retrieval strategy:
- Step 1: Filter by regulation collections relevant to the company profile
- Step 2: Dense retrieval with cosine similarity, top-k=15 per relevant collection
- Step 3: Rerank results using the LLM with a reranking prompt
- Step 4: Take top-20 reranked chunks as final context
- Step 5: Deduplicate — if same article appears from multiple chunks, merge them
- NEVER pass more than 20 chunks to the LLM

### Module 3: Planning (Multi-Step with Feedback)

The agent executes a fixed 6-step pipeline. Each step has defined inputs, outputs, validation checks, and fallback behavior. The agent does NOT freestyle.

STEP 1: Profile Validation and Enrichment
  Input: Raw company profile from user
  Action: Validate all required fields, flag missing data, infer implicit characteristics
  Output: Enriched and validated CompanyProfile object
  Check: All required fields present? If not, ask user, do NOT proceed with assumptions

STEP 2: Regulation Applicability Determination
  Input: Validated CompanyProfile
  Action: For each regulation (GDPR, LkSG, EnEfG, CSRD, BDSG), determine if it applies based on company size, industry, activities, thresholds
  Output: List of applicable regulations with applicability reasoning
  Check: Each determination must cite the specific threshold article

STEP 3: Relevant Article Retrieval (RAG)
  Input: List of applicable regulations + CompanyProfile
  Action: For each applicable regulation, retrieve relevant articles from ChromaDB
  Output: Ranked list of relevant regulatory requirements with full article text
  Check: Minimum 5 articles retrieved per applicable regulation. If fewer, broaden search query, retry once

STEP 4: Compliance Gap Analysis
  Input: Retrieved articles + CompanyProfile (including current compliance measures)
  Action: For each retrieved requirement, assess: COMPLIANT / PARTIALLY_COMPLIANT / NON_COMPLIANT / CANNOT_ASSESS
  Output: Gap analysis table with status, evidence, and specific deficiency description
  Check: Every assessment must have an evidence field explaining WHY that status was assigned

STEP 5: Action Plan Generation
  Input: Gap analysis results
  Action: For each NON_COMPLIANT and PARTIALLY_COMPLIANT item, generate specific action, priority (CRITICAL/HIGH/MEDIUM/LOW), estimated effort, deadline if exists, dependencies
  Output: Prioritized action plan sorted by priority then effort
  Check: Every action must map to a specific gap. No orphan actions. No orphan gaps.

STEP 6: Report Assembly and Quality Check
  Input: All outputs from steps 1-5
  Action: Assemble into structured ComplianceReport, run self-validation
  Output: Final ComplianceReport object
  Check: Self-validation checklist:
  - Every cited article exists in the knowledge base
  - No contradictory assessments
  - Action plan covers every non-compliant gap
  - Priority assignments are consistent (GDPR violations always >= HIGH)
  - Report contains disclaimer about not replacing legal counsel
  - All company-specific details from profile are reflected

Feedback loop: If any step validation check fails:
1. Log the failure with details
2. Attempt self-correction (retry with modified query/prompt) — max 2 retries
3. If still failing after retries, mark that section as "requires manual review" and continue
4. NEVER silently skip a failed step
5. NEVER enter an infinite retry loop

### Module 4: Action (Output Generation)

Report structure:
1. Executive Summary (max 300 words) — company name, applicable regulations count, overall compliance score, top 3 critical findings
2. Company Profile Summary — validated input data, inferred characteristics, missing data flagged
3. Regulatory Applicability Matrix — table with Regulation / Applies? / Reason / Key Threshold
4. Detailed Compliance Analysis per regulation — applicable articles, current status, specific gaps
5. Prioritized Action Plan — table with Priority / Action / Regulation / Article / Effort / Deadline / Dependencies
6. Compliance Score Breakdown — per-regulation score, overall weighted score, visual indicator
7. Disclaimer — AI-generated, not legal advice, consult qualified professional

---

## Regulatory Threshold Logic (HARDCODED — not LLM-determined)

These thresholds MUST be implemented as deterministic code, NOT left to LLM interpretation:

GDPR: applies if processes_personal_data == True. DPO required if employee_count >= 20 (BDSG s38). Processing records required if employee_count >= 250 OR processing is not occasional OR processes special categories.

LkSG: applies if employee_count >= 1000 (since Jan 2024, previously 3000).

EnEfG: energy audit required if NOT SME by EU definition (>250 employees OR >50M revenue). Energy management system if annual_energy_consumption >= 7500 MWh (s8 EnEfG). Waste heat reporting if >= 2500 MWh.

CSRD: applies if two of three met: employee_count > 250, annual_revenue > 50M EUR, balance_sheet > 25M EUR. Listed SMEs from 2026.

BDSG: applies if processes personal data and company is in Germany. DPO required if >= 20 employees regularly processing personal data.

---

## Tech Stack (Locked)

- Language: Python 3.11+
- Agent Framework: LangChain (latest)
- Vector DB: ChromaDB (latest)
- LLM: OpenAI API (gpt-4o)
- Embeddings: intfloat/multilingual-e5-large
- Backend API: FastAPI (latest)
- Frontend: Next.js 14+ with React
- UI: Tailwind CSS + shadcn/ui
- PDF Generation: WeasyPrint or ReportLab
- Validation: Pydantic v2
- Testing: pytest + pytest-asyncio
- Environment: python-dotenv

---

## Error Handling Philosophy — Zero crashes. Zero silent failures. Zero hallucinations.

RULE 1: Every function that can fail MUST have try/except with specific exception types. Never bare except.
RULE 2: Every LLM call MUST validate output against expected Pydantic model. If validation fails, retry with constrained prompt (max 2 retries). If still failing, return structured error.
RULE 3: Every RAG retrieval MUST check result count. If 0, broaden query and retry. If still 0, mark as CANNOT_ASSESS.
RULE 4: All API endpoints MUST return structured JSON, even for errors.
RULE 5: All LLM outputs citing regulatory articles MUST be cross-referenced against knowledge base. Hallucinated citations are removed before reaching user.
RULE 6: Rate limiting and timeout handling. LLM API timeout: 120 seconds. If timeout, retry once, then degrade gracefully.
RULE 7: Input sanitization on all user inputs. Strip HTML, limit string lengths, validate numeric ranges.

---

## API Endpoints

POST /api/analyze — Submit company profile, start analysis (returns job_id)
GET /api/status/{job_id} — Check analysis progress (steps completed, current step)
GET /api/report/{job_id} — Get completed compliance report
POST /api/report/{job_id}/pdf — Generate and download PDF version
GET /api/regulations — List available regulations in knowledge base
GET /api/health — Health check endpoint
POST /api/profile/validate — Validate company profile without running analysis

---

## Frontend Requirements

Design philosophy: Calm, trustworthy, professional. Think "digital consultant", not "AI chatbot".
- Clean white/slate design with subtle blue accents (trust color)
- NO flashy AI branding, no robot icons
- Step-by-step guided form with tooltips explaining each field
- Real-time validation on form fields
- Progress indicator during analysis showing which step is running
- Report view with collapsible sections, traffic-light indicators, export button
- Mobile responsive
- Loading states for every async operation (skeleton loaders, not spinners)
- German and English language toggle

Pages:
- / (landing page with value proposition)
- /analyze (multi-step company profile form)
- /analyze/processing (progress view with step indicators)
- /report/{id} (interactive compliance report)

---

## Prompt Engineering Rules

RULE 1: NEVER use inline prompt strings. ALL prompts live in backend/rag/prompts.py as named constants or template functions.
RULE 2: Every prompt MUST include role/persona, specific task instruction, input data in XML tags, output format specification, constraints, and few-shot examples for complex tasks.
RULE 3: Use XML tags to delimit all structured input: <company_profile>, <retrieved_regulations>, <gap_analysis>, <previous_step_output>.
RULE 4: Every structured output prompt MUST instruct the model to respond in valid JSON only. Parse with json.loads() + Pydantic validation.
RULE 5: Temperature = 0.0 for all compliance-related generation. Creativity is not a feature here.

---

## Testing Strategy

Unit Tests: threshold logic with edge cases, Pydantic model validation, chunking correctness, retrieval relevance.

Integration Tests with 5 predefined company profiles:
1. Small IT agency (5 employees, processes personal data, no supply chain)
2. Medium manufacturer (500 employees, supply chain in Asia, high energy use)
3. Large listed company (1500 employees, all regulations apply)
4. Freelancer/Solo (1 employee, minimal obligations)
5. Healthcare company (50 employees, special category data)

Edge Case Tests: missing optional fields, all regulations not applicable, ChromaDB unavailable, LLM API timeout, extremely long inputs.

---

## Project Structure

compliance-agent/
  PLANNING.md
  README.md
  .env.example
  .gitignore
  backend/
    main.py
    config.py
    agent/ (profiling.py, memory.py, planning.py, actions.py, validation.py)
    rag/ (ingest.py, retrieval.py, prompts.py, embeddings.py)
    models/ (company_profile.py, compliance_report.py, api_responses.py, enums.py)
    services/ (threshold_engine.py, report_generator.py, job_manager.py)
    data/regulations/ (gdpr/, lksg/, enefg/, csrd/, bdsg/)
    tests/ (test_thresholds.py, test_models.py, test_rag.py, test_pipeline.py, test_profiles/)
  frontend/
    package.json, tailwind.config.js, next.config.js
    src/app/ (layout.tsx, page.tsx, analyze/, report/)
    src/components/ (ui/, profile-form/, report/, common/)
    src/lib/ (api.ts, types.ts, utils.ts)
    src/hooks/ (useAnalysis.ts, useReport.ts)
  scripts/ (ingest_regulations.py, seed_test_data.py, run_test_analysis.py)
  requirements.txt
  docker-compose.yml

---

## Development Phases

Phase 1 Foundation (Week 1-2): Project scaffolding, Pydantic models, threshold engine, unit tests, FastAPI skeleton
Phase 2 RAG Pipeline (Week 3-4): Regulatory document collection, article-level chunking, ChromaDB setup, retrieval + reranking, integration tests
Phase 3 Agent Logic (Week 5-7): Prompt templates, profiling module, planning module, action module, self-validation, end-to-end tests
Phase 4 Frontend (Week 8-10): Next.js setup, landing page, profile form, progress view, report view, PDF export
Phase 5 Polish and Evaluation (Week 11-12): Error handling hardening, edge case testing, performance optimization, user evaluation, bug fixes

---

## Current Phase
Phase 1: Foundation — Project scaffolding
