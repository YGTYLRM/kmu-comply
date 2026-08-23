# Complio — Production Readiness Assessment

---

## Overall Status: Near-Launch Ready (Code), Pre-Deploy (Infrastructure)

The code is feature-complete and stable. No blocking code issues remain. The system cannot be launched because several infrastructure and configuration steps are pending — all owned by the founder, not requiring code changes.

---

## What Is Complete

### Core Product
- [x] 14-regulation deterministic applicability engine (all thresholds with verbatim citations)
- [x] Rule engine with required-field tracking and confidence grading
- [x] RAG pipeline: multilingual-e5-large embeddings + BM25 hybrid retrieval + cross-encoder reranking
- [x] Gap analysis via LLM (Anthropic tool use, per-regulation, grounded in retrieved text)
- [x] Citation verification (LLM citations cross-checked against retrieved chunks)
- [x] Action plan generation (prioritized, concrete, article-linked)
- [x] Deterministic compliance score formula
- [x] PDF generation (Playwright, A4, embedded fonts, no external network calls)
- [x] 10 document templates (GDPR privacy notice, ROPA, TOM, incident response, AI policy, AI inventory, whistleblower policy, safety instruction, supplier code of conduct, NIS2 risk register)
- [x] Company document upload + RAG (Fernet-encrypted, 7-day TTL, magic bytes validation)
- [x] Website scanner (HTTPS check, Impressum, cookie banner, §25 TTDSG, trackers)

### Billing & Auth
- [x] Stripe integration (checkout, webhooks, subscription management, Customer Portal)
- [x] Supabase JWT authentication
- [x] Feature gating by plan (templates, expert review gated on Professional+)
- [x] Rate limiting (analysis 10/hr, scan 10/hr, PDF 20/hr, templates 30/hr)

### Monitoring & Scheduling
- [x] APScheduler: weekly regulation change detection + daily re-assessment cycle
- [x] Sentry error tracking (activated by env var)
- [x] Alembic database migrations
- [x] Redis + Celery job queue (with asyncio fallback for dev)

### Security
- [x] 17 security controls applied (CSP, HSTS, SSRF guard, injection scanning, IDOR guard, rate limiting, encryption, etc.)
- [x] RLS policy SQL written (needs to be applied in Supabase)

### Tests
- [x] 219 passing tests (rule engine 32, thresholds 44, golden profiles 9, celery 12, pipeline retrieval 4, CI retrieval eval 42, website scanner 21, citation verification 6, etc.)
- [x] 0 test failures in default run

### Knowledge Base
- [x] 15 ChromaDB collections, 3,020 chunks indexed
- [x] 7 new expanded guidance files ready for ingest (BSI NIS2, BAFA LkSG, DENA EnEfG, BaFin GwG, ESRS CSRD, DSK GDPR, CJEU rulings)

---

## What Is NOT Complete

### Blocking for Launch (User Action Required)

| Item | Who | What to do |
|------|-----|-----------|
| Anthropic API credits | Founder | Top up account — entire pipeline blocked |
| RLS policies | Founder | Run `backend/db/rls_policies.sql` in Supabase SQL editor |
| Stripe configuration | Founder | Create webhook → get `whsec_` → add to `.env` → set `STRIPE_ENABLED=true` |
| Resend API key | Founder | Get key, add to `.env` |
| Deployment | Founder | Railway/Fly.io/VPS + persistent volumes + `alembic upgrade head` |
| Secret rotation | Founder | Rotate Anthropic key, Stripe key, Supabase service role key, DB password in `.env` |
| Redis password | Founder | Add to docker-compose + REDIS_URL |
| npm install | Founder | `cd frontend && npm install` (locks Next.js 14.2.25) |
| KB re-ingest | Founder | `python scripts/ingest_all.py` after API credits available |

### Blocking for Revenue (Legal Required)

| Item | Who | Notes |
|------|-----|-------|
| ToS and Privacy Policy | Lawyer-drafted | Required for GDPR Art. 13 + German e-commerce law |
| Threshold engine review | Rechtsanwalt | Per regulation group; CSRD Omnibus uncertainty is highest risk |
| CSRD Omnibus verification | Lawyer | EU Council Feb 2026 raised thresholds — verify if formally in force |

### Not Blocking but Should Be Done

| Item | Priority | Notes |
|------|---------|-------|
| E2E golden profile tests | Medium | Pipeline tests need API credits; add after credits restored |
| Improve retrieval_eval failures | Medium | 13 of 261 cases fail; will improve after KB ingest |
| Pentest | Medium | Especially website scanner (SSRF) + document upload pipeline |
| Third-party legal review of AI output | Low | Standard SaaS liability due diligence |

---

## Deployment Steps (In Order)

```bash
# 1. Set up infrastructure
# - Create account on Railway, Fly.io, or provision a VPS
# - Mount persistent volumes for chroma_db/ and reports/
# - Set all environment variables (see ARCHITECTURE.md § Configuration)

# 2. Apply database schema
alembic upgrade head

# 3. Apply Supabase RLS
# - Open Supabase SQL editor
# - Run: backend/db/rls_policies.sql

# 4. Build and deploy
# Frontend → Vercel (git push triggers deploy)
# Backend → container platform

# 5. Populate knowledge base (requires API credits)
cd backend
python scripts/ingest_all.py

# 6. Verify
curl https://api.yourdomain.com/health
python -m pytest tests/ -m "not retrieval_eval" -k "not e2e" -q

# 7. Configure Stripe
# - Add webhook endpoint → get whsec_ → add to .env
# - Set STRIPE_ENABLED=true
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| CSRD threshold is wrong due to Omnibus | Medium | High | Flagged in output; lawyer review before selling |
| LLM hallucination in gap analysis | Low | Medium | Citation grounding + verification; CANNOT_ASSESS for empty KB |
| Customer misuses screening as legal advice | Medium | High | Disclaimers on every output; ToS needed |
| Competitor releases similar product first | Medium | High | Faster to market = first-mover in German SME space |
| Anthropic API price increase | Low | Medium | Most pipeline cost is embedding (local) not LLM |
| ChromaDB corruption | Low | High | Regular backups of chroma_db/; or migrate to ChromaDB server mode |
