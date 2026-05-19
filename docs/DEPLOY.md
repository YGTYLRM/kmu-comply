# Complio — Deployment Runbook

**Target:** First production deploy on Railway, Fly.io, or a Linux VPS.
**Time estimate:** 2–3 hours (first deploy), 15 minutes (subsequent deploys).

---

## Prerequisites

- [ ] Supabase project created (free tier is fine to start)
- [ ] Anthropic API key with credits
- [ ] Stripe account (test mode is fine for initial deploy)
- [ ] Resend account with a verified sending domain
- [ ] Sentry account (optional but recommended)
- [ ] A domain name pointed at your hosting provider

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

- [ ] Alembic migrations applied (`alembic upgrade head`)
- [ ] RLS policies applied (`scripts/apply_rls.py`)
- [ ] KB populated (`scripts/kb_health.py` shows 15/15)
- [ ] Impressum, Datenschutz, AGB pages filled in
- [ ] Stripe webhook configured and tested
- [ ] HTTPS working
- [ ] `ENVIRONMENT=production` set (enables startup checks)
- [ ] All secrets rotated from dev values
- [ ] Sentry DSN set and verified error capture works
- [ ] Worker process running

---

## Rollback

```bash
# Roll back last migration
alembic downgrade -1

# Roll back to specific revision
alembic downgrade <revision>
```

ChromaDB has no migration system — take a backup of `data/chroma_db/` before each ingest.
