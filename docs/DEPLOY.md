# Complio — Deployment Runbook

**Target:** First production deploy on Railway, Fly.io, or a Linux VPS.
**Time estimate:** 2–3 hours (first deploy), 15 minutes (subsequent deploys).

---

## Minimum server requirements

| Component | Minimum | Why |
|-----------|---------|-----|
| vCPU | 4 | Celery + FastAPI + embedding model (multilingual-e5-large) |
| RAM | 8 GB | 2× Playwright renders (~2 GB each) + ChromaDB + FastAPI workers |
| Disk | 20 GB SSD | ChromaDB (~3 GB) + model cache (~2 GB) + logs |
| OS | Ubuntu 22.04+ | Playwright Chromium dependency |

Playwright semaphore is set to 2 concurrent renders by default (`PDF_CONCURRENCY=2`).
Raising it above 2 on an 8 GB instance will cause OOM kills under load.

---

## Prerequisites

- [ ] Supabase project on a **paid plan** (free tier caps at 500 MB database + 2 GB bandwidth — a single traffic spike will hit this before you can react)
- [ ] Anthropic API key with credits
- [ ] Stripe account (test mode is fine for initial deploy)
- [ ] Resend account with a verified sending domain
- [ ] Sentry account (optional but recommended)
- [ ] A domain name pointed at your hosting provider
- [ ] Anthropic DPA signed — required before processing customer data (self-service at console.anthropic.com → Settings → Data Usage)
- [ ] Supabase DPA confirmed — Supabase provides a standard GDPR DPA; verify it is in place for your project (app.supabase.com → project settings → Legal)

---

## Step 1 — Prepare environment variables

Copy `.env.example` to `backend/.env` and fill in all required values:

```bash
cp .env.example backend/.env
```

**Minimum required for pipeline to work:**
```
LLM_API_KEY=sk-ant-api03-...
DATABASE_URL=postgresql+asyncpg://postgres:[pw]@db.[project].supabase.co:5432/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
ENVIRONMENT=production
ADMIN_API_KEY=[random 32-char secret]
DOCUMENT_ENCRYPTION_KEY=[generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"]
ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Step 2 — Supabase setup

### 2a — Run database migrations
```bash
cd backend
alembic upgrade head
```

### 2b — Apply Row-Level Security (REQUIRED — do this immediately)
```bash
# Option 1: psql
psql $DATABASE_URL -f db/rls_policies.sql

# Option 2: Python script
python scripts/apply_rls.py

# Option 3: Supabase dashboard
# Open: https://app.supabase.com/project/[project]/sql/new
# Paste contents of: backend/db/rls_policies.sql
# Click "Run"
```

### 2c — Verify RLS is active
```bash
python scripts/apply_rls.py --verify
```

---

## Step 3 — Frontend build

```bash
cd frontend
npm install
npm run build
```

Set environment variables in Vercel (or wherever you host the frontend):
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_STRIPE_ENABLED=true   # when Stripe is configured
```

---

## Step 4 — Backend deploy (Railway example)

### 4a — Create Railway project
1. Go to railway.app → New Project → Deploy from GitHub repo
2. Select this repository, service: `backend/`
3. Set root directory to `/` (Dockerfile is at project root)

### 4b — Add persistent volumes
In Railway settings, add volumes:
- `/app/backend/data/chroma_db` — ChromaDB (persists knowledge base)
- `/app/backend/data/reports` — Report JSON files

**IMPORTANT:** If the ChromaDB volume is not mounted or mounts to the wrong path, the
knowledge base will be empty after every deploy. The pipeline will return CANNOT_ASSESS
for all regulations silently. Verify after first deploy:

```bash
curl https://api.yourdomain.com/api/health/deep
# Expected: {"status":"ok","total_chunks":3019,...}
# If total_chunks=0 or any collection has 0 chunks: volume is not mounted correctly
```

### 4c — Set all environment variables from Step 1

### 4d — Deploy

---

## Step 5 — Populate knowledge base (REQUIRED)

After the backend is running with valid API credits:

```bash
# Connect to your deployed backend container, or run locally pointing at prod DB:
cd backend
python scripts/ingest_all.py
```

Verify:
```bash
python scripts/kb_health.py
# Expected: 15/15 OK, total ~3,019+ chunks
```

---

## Step 6 — Configure Stripe

1. In Stripe dashboard → Webhooks → Add endpoint: `https://api.yourdomain.com/api/billing/webhook`
2. Select events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
3. Copy the webhook signing secret (`whsec_...`)
4. Add to backend `.env`:
   ```
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_ENABLED=true
   ```
5. Restart the backend

---

## Step 7 — Configure Resend

1. Add and verify a sending domain in Resend dashboard
2. Create an API key with `send` permission
3. Add to backend `.env`:
   ```
   RESEND_API_KEY=re_...
   CONTACT_EMAIL=hello@yourdomain.com
   ```

---

## Step 8 — Rotate all secrets

Generate fresh secrets for production — never use dev/test keys in production:

```bash
# Generate a new Fernet encryption key for documents
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate a random admin API key
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 9 — Health check

```bash
curl https://api.yourdomain.com/health
# Expected: {"status":"ok"} or {"status":"degraded"} with subsystem details

python scripts/kb_health.py
# Expected: 15/15 PASS
```

---

## Step 10 — Add legal pages

Before accepting any users, ensure these pages exist on your frontend:
- `/impressum` — required by § 5 DDG (German law)
- `/datenschutz` — required by DSGVO Art. 13
- `/agb` — recommended for B2B SaaS

Fill in the placeholder values in:
- `frontend/src/app/impressum/page.tsx`
- `frontend/src/app/datenschutz/page.tsx`
- `frontend/src/app/agb/page.tsx`

---

## Worker process

The scheduler worker must run alongside the web server:

```bash
# In a separate process / Railway service:
python worker.py
```

For Celery (when `REDIS_URL` is set):
```bash
celery -A celery_app worker --loglevel=info --concurrency=2
```

---

## Checklist before first user

### Technical
- [ ] Alembic migrations applied (`alembic upgrade head`)
- [ ] RLS policies applied (`scripts/apply_rls.py`)
- [ ] KB populated (`scripts/kb_health.py` shows 15/15)
- [ ] Deep health check passes (`curl /api/health/deep` → `"status":"ok"`)
- [ ] Stripe webhook configured and tested
- [ ] HTTPS working
- [ ] `ENVIRONMENT=production` set (enables startup checks)
- [ ] All secrets rotated from dev values
- [ ] Sentry DSN set and verified error capture works
- [ ] Worker process running

### Legal (BLOCKING — do not accept paying customers without these)
- [ ] Impressum complete with **real** street address + postcode (§ 5 DDG)
- [ ] Datenschutz page reviewed — fill in any remaining placeholder values
- [ ] AGB reviewed by a German lawyer or qualified legal advisor
- [ ] Anthropic DPA signed (console.anthropic.com → Settings → Data Usage)
- [ ] Supabase DPA confirmed (app.supabase.com → project settings → Legal)
- [ ] Cookie/consent banner active if using any analytics or non-essential scripts
- [ ] CSRD Omnibus status verified with legal counsel before issuing CSRD findings
- [ ] Threshold engine reviewed by a Rechtsanwalt for at least GDPR + NIS2 + LkSG

---

## Rollback

```bash
# Roll back last migration
alembic downgrade -1

# Roll back to specific revision
alembic downgrade <revision>
```

ChromaDB has no migration system — take a backup of `data/chroma_db/` before each ingest.
