# Complio — Security Posture

This document summarizes the security controls implemented in the Complio backend and frontend.

---

## Threat Model

Complio processes two categories of sensitive data:
1. **Company compliance profiles** — business-sensitive data about a company's operations, processes, and gaps
2. **Uploaded documents** — potentially confidential business documents uploaded for evidence

The primary threat vectors are:
- Prompt injection via uploaded documents or company profile free-text fields
- Unauthorized access to another user's compliance reports (IDOR)
- SSRF via the website scanner
- Data leakage through logging, error messages, or the health endpoint

---

## Implemented Controls

### Input / Prompt Injection

| Control | Implementation | Location |
|---------|---------------|----------|
| Keyword sanitizer | Strips XML/HTML, truncates, removes injection keywords (`ignore`, `disregard`, `override`, `system prompt`, `new instruction`) | `rag/prompts.py:_sanitize()` |
| Unicode normalization | `unicodedata.normalize("NFKC")` — neutralizes homoglyph attacks | `rag/prompts.py:_sanitize()` |
| LLM injection classifier | Haiku 4.5 sweep on uploaded documents — blocks HIGH/MEDIUM confidence injections before chunking | `services/injection_guard.py` |
| Full-file injection scan | Scans beginning + middle + end of file, up to 48KB — catches buried injections | `services/injection_guard.py` |
| Magic bytes validation | PDF must start with `%PDF`; txt/md must be valid UTF-8 | `services/document_store.py` |
| Applicability lock | LLM explicitly told: applicability is already decided; it must not re-derive thresholds | `rag/prompts.py` (gap_analysis_prompt) |

### Authentication & Authorization

| Control | Implementation | Location |
|---------|---------------|----------|
| JWT authentication | Supabase JWT verified on all state-mutating endpoints | `services/auth_service.py` |
| IDOR prevention | Sessions store `user_id`; analyze endpoint checks job ownership | `routes/analysis.py` |
| Job ownership | Redis-first `assert_owns_job()` with DB fallback | `services/redis_store.py` |
| Admin key protection | Constant-time compare via `secrets.compare_digest()` | `routes/admin.py` |
| Admin key audit trail | HMAC fingerprint stored (not raw prefix) | `routes/admin.py` |

### Network & Transport

| Control | Implementation | Location |
|---------|---------------|----------|
| SSRF guard | Rejects RFC1918 + loopback targets before Playwright opens | `services/website_scanner.py` |
| PDF network isolation | All requests blocked via `route.abort()` during PDF rendering | `services/pdf_generator.py` |
| CSP headers | Content-Security-Policy via SecurityHeadersMiddleware | `main.py` |
| HSTS | Strict-Transport-Security header | `main.py` |
| Proxy headers | ProxyHeadersMiddleware for correct client IP behind load balancer | `main.py` |
| Additional response headers | X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy | `main.py` |

### Rate Limiting

| Endpoint | Limit | Storage |
|---------|-------|---------|
| `POST /api/analyze` | 10/hour per user | PostgreSQL (persistent across restarts) |
| `POST /api/scan-website` | 10/hour per user | In-memory with DB fallback |
| `POST /api/report/{id}/pdf` | 20/hour per user | In-memory |
| `POST /api/report/{id}/templates/{id}` | 30/hour per user | In-memory |
| `POST /api/contact` | 5/hour per IP | In-memory |

### Data Protection

| Control | Implementation | Location |
|---------|---------------|----------|
| Document encryption at rest | Fernet AES-128-CBC + HMAC-SHA256 | `services/document_store.py` |
| Key management | `DOCUMENT_ENCRYPTION_KEY` env var; ephemeral key if unset (dev only) | `config.py` |
| No plaintext disk write | Decryption happens in-memory; plaintext bytes never written to disk | `services/document_store.py` |
| Document TTL | 7-day automatic expiry + cleanup | `services/document_store.py`, `services/job_manager.py` |
| Health endpoint minimization | In production: only `{"status":"ok/degraded"}` returned | `routes/misc.py` |
| ChromaDB reset protection | `ALLOW_RESET=false` in production | `docker-compose.yml` |

### Infrastructure

| Control | Implementation |
|---------|---------------|
| Next.js CVE patched | 14.2.3 → 14.2.25 (CVE-2025-29927 directory traversal) |
| Sentry error tracking | Activated by `SENTRY_DSN` env var; `send_default_pii=False` |
| ChromaDB orphan cleanup | Abandoned per-job collections deleted on startup |
| ChromaDB write isolation | `threading.Semaphore(1)` in embedded mode |

---

## Outstanding Security Items

| Item | Risk | Required before launch? |
|------|------|------------------------|
| Rotate all secrets in `backend/.env` | CRITICAL if any key was exposed | Yes |
| Add Redis password to docker-compose | HIGH | Yes (if using Redis/Celery) |
| Switch `auth_service.py` to Supabase anon key | HIGH | Yes — service role key bypasses RLS |
| Apply RLS policies in Supabase | CRITICAL | Yes — user data isolation |
| `npm install` in frontend/ | MEDIUM | Yes (to lock Next.js 14.2.25) |
| ToS and Privacy Policy pages | LEGAL | Yes — GDPR Art. 13 + e-commerce law |
| Rate limits stored in-memory | LOW | No — restart resets counters for non-analyze endpoints |

---

## What Is NOT Present

- No WAF (mitigated by Pydantic validation + sanitization)
- No IP allowlisting on admin endpoints (admin key is the only control)
- No audit log for all API calls (only admin + job state is logged)
- No automated secret rotation

---

## Security Testing

- 17 security issues identified in a structured code review (session 5) — all fixed
- No penetration test conducted
- No third-party security audit
- Recommendation: Before handling customer data, conduct a Pentest particularly targeting the website scanner (SSRF), uploaded document pipeline (injection), and the Stripe webhook handler
