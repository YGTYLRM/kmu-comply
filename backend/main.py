from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Header, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timezone
from time import time
import html

from config import settings
from models import (
    CompanyProfile,
    AnalyzeResponse,
    StatusResponse,
    ComplianceReport,
    ProfileValidationResponse,
    RegulationsListResponse,
    HealthResponse,
    ErrorResponse,
    JobStatus,
)
from services.job_manager import JobManager
from services.threshold_engine import determine_applicable_regulations
from services.auth_service import get_current_user, get_optional_user

job_manager = JobManager(ttl_seconds=settings.job_ttl_seconds)

# Job ownership: job_id → user_id (guards report endpoints)
_job_owners: dict[str, str] = {}

ANALYZE_LIMIT = 10
ANALYZE_WINDOW = 3600  # seconds

# In-memory fallback used only when DB is not configured
_analyze_calls_fallback: dict[str, list[float]] = defaultdict(list)


async def _check_rate_limit(user_id: str) -> None:
    if settings.database_url:
        from db.database import AsyncSessionLocal
        from db.models import RateLimitEvent
        from sqlalchemy import select, func, delete
        from datetime import timedelta
        now_dt = datetime.now(timezone.utc)
        window_start = now_dt - timedelta(seconds=ANALYZE_WINDOW)
        async with AsyncSessionLocal() as db:
            # Count calls in the last hour
            count = (await db.execute(
                select(func.count()).where(
                    RateLimitEvent.user_id == user_id,
                    RateLimitEvent.endpoint == "analyze",
                    RateLimitEvent.called_at >= window_start,
                )
            )).scalar_one()
            if count >= ANALYZE_LIMIT:
                # Find oldest call in window to compute retry time
                oldest = (await db.execute(
                    select(func.min(RateLimitEvent.called_at)).where(
                        RateLimitEvent.user_id == user_id,
                        RateLimitEvent.endpoint == "analyze",
                        RateLimitEvent.called_at >= window_start,
                    )
                )).scalar_one()
                retry_in = int(ANALYZE_WINDOW - (now_dt - oldest).total_seconds()) + 1
                mins, secs = retry_in // 60, retry_in % 60
                wait = f"{mins}m {secs}s" if mins else f"{secs}s"
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit reached — maximum {ANALYZE_LIMIT} screenings per hour. "
                           f"Try again in {wait}.",
                    headers={"Retry-After": str(retry_in)},
                )
            db.add(RateLimitEvent(user_id=user_id, endpoint="analyze"))
            # Prune old events older than 2 hours to keep the table lean
            await db.execute(
                delete(RateLimitEvent).where(
                    RateLimitEvent.called_at < now_dt - timedelta(hours=2)
                )
            )
            await db.commit()
    else:
        # Fallback: in-memory (acceptable when DB is not configured)
        now = time()
        calls = [t for t in _analyze_calls_fallback[user_id] if now - t < ANALYZE_WINDOW]
        _analyze_calls_fallback[user_id] = calls
        if len(calls) >= ANALYZE_LIMIT:
            oldest = min(calls)
            retry_in = int(ANALYZE_WINDOW - (now - oldest)) + 1
            mins, secs = retry_in // 60, retry_in % 60
            wait = f"{mins}m {secs}s" if mins else f"{secs}s"
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit reached — maximum {ANALYZE_LIMIT} screenings per hour. "
                       f"Try again in {wait}.",
                headers={"Retry-After": str(retry_in)},
            )
        _analyze_calls_fallback[user_id].append(now)


async def _assert_owns_job(job_id: str, user_id: str) -> None:
    # Fast path: job was created in this process (in-progress or recently completed)
    owner = _job_owners.get(job_id)
    if owner is None and settings.database_url:
        # DB fallback: handles post-restart access to completed jobs
        from services.db_service import get_job_owner
        owner = await get_job_owner(job_id)
    if owner is None:
        raise HTTPException(status_code=403, detail="Access denied.")
    if owner != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")


def _cleanup_orphaned_chroma_collections() -> None:
    """Delete any per-job ChromaDB collections left over from a previous crashed process."""
    try:
        import chromadb
        from rag.ingest import CHROMA_DIR
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        orphans = [c.name for c in client.list_collections() if c.name.startswith("job_")]
        for name in orphans:
            client.delete_collection(name)
        if orphans:
            import logging
            logging.getLogger(__name__).info(
                "startup: deleted %d orphaned job collections: %s", len(orphans), orphans
            )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("startup: orphan cleanup failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _cleanup_orphaned_chroma_collections()
    if settings.database_url:
        from db.database import init_db
        await init_db()
    await job_manager.start()
    yield
    await job_manager.stop()


app = FastAPI(
    title="KMU-Comply API",
    description="Autonomous regulatory compliance analysis for German SMEs",
    version="0.1.0",
    lifespan=lifespan,
)

_allowed_origins = [o.strip() for o in (settings.allowed_origins or "http://localhost:3000,http://localhost:3001").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)


@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        chromadb="not_connected",
        embedding_model=settings.embedding_model,
    )


@app.post("/api/auth/sync-profile")
async def sync_profile(current_user: dict = Depends(get_current_user)):
    """Called after login/register to ensure the user has a profile row in our DB."""
    if not settings.database_url:
        return {"ok": True}
    from db.database import AsyncSessionLocal
    from db.models import Profile
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Profile).where(Profile.id == current_user["id"]))
        profile = result.scalar_one_or_none()
        if not profile:
            profile = Profile(id=current_user["id"], email=current_user["email"])
            db.add(profile)
            await db.commit()
    return {"ok": True}


@app.post("/api/profile/validate", response_model=ProfileValidationResponse)
async def validate_profile(profile: CompanyProfile, current_user: dict = Depends(get_current_user)):
    """Validate a company profile without running analysis."""
    from models.company_profile import EnrichedCompanyProfile

    warnings: list[str] = []
    missing: list[str] = []

    if profile.annual_revenue_eur is None:
        missing.append("annual_revenue_eur")
        warnings.append("Annual revenue not provided — CSRD and EnEfG applicability may be incomplete.")
    if profile.balance_sheet_total_eur is None:
        missing.append("balance_sheet_total_eur")
        warnings.append("Balance sheet not provided — CSRD applicability may be incomplete.")
    if profile.annual_energy_consumption_mwh is None:
        missing.append("annual_energy_consumption_mwh")
        warnings.append("Energy consumption not provided — EnEfG energy management requirements cannot be assessed.")

    enriched = EnrichedCompanyProfile(
        **profile.model_dump(),
        missing_optional_fields=missing,
        validation_warnings=warnings,
    )
    return ProfileValidationResponse(
        valid=True,
        errors=[],
        warnings=warnings,
        enriched_profile=enriched.model_dump(),
    )


class AnalyzeRequest(BaseModel):
    profile: CompanyProfile
    doc_session_id: Optional[str] = None


@app.post("/api/documents")
async def upload_documents(files: list[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
    """Upload company documents before analysis. Returns a doc_session_id."""
    from services.document_store import document_store

    session_id = document_store.create_session()
    saved: list[str] = []
    errors: list[str] = []

    for f in files:
        try:
            content = await f.read()
            name = document_store.save_file(session_id, f.filename or "upload", content)
            saved.append(name)
        except ValueError as e:
            errors.append(str(e))

    if not saved and errors:
        document_store.clear(session_id)
        raise HTTPException(status_code=400, detail="; ".join(errors))

    return {
        "doc_session_id": session_id,
        "files_saved": saved,
        "errors": errors,
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    """Submit a company profile for compliance analysis. Returns a job_id."""
    await _check_rate_limit(current_user["id"])

    # Enforce subscription plan limits
    if settings.stripe_enabled and settings.database_url:
        from services.stripe_service import get_active_subscription, check_company_limit
        sub = await get_active_subscription(current_user["id"])
        if not sub:
            raise HTTPException(status_code=402, detail="Active subscription required.")
        allowed, reason = await check_company_limit(current_user["id"])
        if not allowed:
            raise HTTPException(status_code=402, detail=reason)

    # Upsert company in DB so it can be monitored going forward
    company_id: Optional[str] = None
    if settings.database_url:
        try:
            from services.db_service import upsert_company
            company_id = await upsert_company(current_user["id"], body.profile)
        except Exception as exc:
            # Non-fatal — analysis still runs, just won't be monitored
            import logging
            logging.getLogger(__name__).warning("analyze: db upsert failed: %s", exc)

    job_id = await job_manager.create_job(
        body.profile,
        doc_session_id=body.doc_session_id,
        user_id=current_user["id"],
        company_id=company_id,
    )
    _job_owners[job_id] = current_user["id"]
    return AnalyzeResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Analysis job created. Use GET /api/status/{job_id} to track progress.",
    )


@app.get("/api/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str, current_user: dict = Depends(get_current_user)):
    await _assert_owns_job(job_id, current_user["id"])
    status = job_manager.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return status


@app.get("/api/report/{job_id}", response_model=ComplianceReport)
async def get_report(job_id: str, current_user: dict = Depends(get_current_user)):
    await _assert_owns_job(job_id, current_user["id"])
    # Try in-memory job first (fastest path for recently completed jobs)
    report = job_manager.get_report(job_id)
    if report is None:
        # Try DB then disk
        from services.report_store import load_async
        report = await load_async(job_id)
    if report is None:
        status = job_manager.get_status(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
        raise HTTPException(
            status_code=202,
            detail=f"Report not ready yet. Current status: {status.status}",
        )
    return report


@app.get("/api/report/{job_id}/profile")
async def get_profile(job_id: str, current_user: dict = Depends(get_current_user)):
    await _assert_owns_job(job_id, current_user["id"])
    from services.report_store import load_profile
    profile = load_profile(job_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found for this job.")
    return profile


@app.post("/api/report/{job_id}/pdf")
async def generate_pdf_endpoint(job_id: str, current_user: dict = Depends(get_current_user)):
    import asyncio
    from fastapi.responses import Response
    from services.pdf_generator import generate_pdf as _gen_pdf

    await _assert_owns_job(job_id, current_user["id"])
    report = job_manager.get_report(job_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found or not completed.")

    loop = asyncio.get_running_loop()
    pdf_bytes = await loop.run_in_executor(None, _gen_pdf, report)
    filename  = f"complio-{report.company_name.replace(' ', '-')[:40]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/reports")
async def list_reports(current_user: dict = Depends(get_current_user)):
    """List persisted reports for the current user, newest first."""
    from services.report_store import list_recent_async
    return {"reports": await list_recent_async(user_id=current_user["id"])}


@app.get("/api/companies")
async def list_companies(current_user: dict = Depends(get_current_user)):
    """List all companies for the current user with their latest report summary."""
    from db.database import AsyncSessionLocal
    from db.models import Company, Report
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        # Latest report per company
        latest_subq = (
            select(Report.company_id, func.max(Report.created_at).label("last_report_at"))
            .group_by(Report.company_id)
            .subquery()
        )
        latest_score_subq = (
            select(Report.company_id, Report.overall_score_percent, Report.created_at)
            .join(latest_subq, (Report.company_id == latest_subq.c.company_id) &
                  (Report.created_at == latest_subq.c.last_report_at))
            .subquery()
        )
        stmt = (
            select(
                Company,
                latest_score_subq.c.overall_score_percent,
                latest_score_subq.c.created_at.label("last_report_at"),
                func.count(Report.id).label("report_count"),
            )
            .where(Company.user_id == current_user["id"])
            .outerjoin(latest_score_subq, latest_score_subq.c.company_id == Company.id)
            .outerjoin(Report, Report.company_id == Company.id)
            .group_by(Company.id, latest_score_subq.c.overall_score_percent, latest_score_subq.c.created_at)
            .order_by(Company.updated_at.desc())
        )
        rows = (await db.execute(stmt)).all()

    return {"companies": [
        {
            "id": str(c.id),
            "name": c.name,
            "industry": c.industry,
            "employee_count": c.employee_count,
            "country": c.country,
            "latest_score": score,
            "last_report_at": last_at.isoformat() if last_at else None,
            "report_count": count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c, score, last_at, count in rows
    ]}


@app.get("/api/companies/{company_id}")
async def get_company(company_id: str, current_user: dict = Depends(get_current_user)):
    """Get company detail plus all report history."""
    from db.database import AsyncSessionLocal
    from db.models import Company, Report
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Company).where(Company.id == company_id, Company.user_id == current_user["id"])
        )
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found.")

        reports_result = await db.execute(
            select(Report)
            .where(Report.company_id == company_id)
            .order_by(Report.created_at.desc())
        )
        reports = reports_result.scalars().all()

    return {
        "company": {
            "id": str(company.id),
            "name": company.name,
            "industry": company.industry,
            "employee_count": company.employee_count,
            "country": company.country,
            "created_at": company.created_at.isoformat() if company.created_at else None,
        },
        "reports": [
            {
                "id": str(r.id),
                "job_id": r.job_id,
                "score": r.overall_score_percent,
                "triggered_by": r.triggered_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ],
    }


@app.get("/api/notifications")
async def list_notifications(current_user: dict = Depends(get_current_user)):
    from services.notification_service import get_notifications
    return {"notifications": await get_notifications(current_user["id"])}


@app.get("/api/notifications/unread-count")
async def unread_count(current_user: dict = Depends(get_current_user)):
    from services.notification_service import get_unread_count
    return {"count": await get_unread_count(current_user["id"])}


@app.post("/api/notifications/mark-read")
async def mark_notifications_read(current_user: dict = Depends(get_current_user)):
    from services.notification_service import mark_all_read
    await mark_all_read(current_user["id"])
    return {"ok": True}


@app.get("/api/regulations", response_model=RegulationsListResponse)
async def list_regulations():
    from models.api_responses import RegulationInfo

    regs = [
        RegulationInfo(
            id="gdpr_dsgvo",
            name="GDPR / DSGVO",
            description="General Data Protection Regulation",
            document_count=0,
        ),
        RegulationInfo(
            id="lksg",
            name="LkSG",
            description="Supply Chain Due Diligence Act",
            document_count=0,
        ),
        RegulationInfo(
            id="enefg",
            name="EnEfG",
            description="Energy Efficiency Act",
            document_count=0,
        ),
        RegulationInfo(
            id="csrd",
            name="CSRD",
            description="Corporate Sustainability Reporting Directive",
            document_count=0,
        ),
        RegulationInfo(
            id="bdsg",
            name="BDSG",
            description="Federal Data Protection Act (Bundesdatenschutzgesetz)",
            document_count=0,
        ),
    ]
    return RegulationsListResponse(regulations=regs)


class ContactRequest(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    phone: Optional[str] = None
    topic: Optional[str] = None
    message: str


_contact_calls: dict[str, list[float]] = defaultdict(list)

@app.post("/api/contact")
async def contact(req: ContactRequest, request: Request):
    if not settings.resend_api_key or not settings.contact_email:
        raise HTTPException(status_code=503, detail="Contact not configured.")
    ip = request.client.host if request.client else "unknown"
    now = time()
    recent = [t for t in _contact_calls[ip] if now - t < 3600]
    _contact_calls[ip] = recent
    if len(recent) >= 5:
        raise HTTPException(status_code=429, detail="Too many contact requests. Try again later.")
    _contact_calls[ip].append(now)

    import resend
    resend.api_key = settings.resend_api_key

    subject = f"Contact: {req.name}"
    if req.topic:
        subject += f" — {req.topic}"
    if req.company:
        subject += f" ({req.company})"

    # Escape all user-supplied content before embedding in HTML
    esc_name    = html.escape(req.name)
    esc_email   = html.escape(req.email)
    esc_company = html.escape(req.company or "Not provided")
    esc_phone   = html.escape(req.phone   or "Not provided")
    esc_topic   = html.escape(req.topic   or "Not specified")
    esc_message = html.escape(req.message)

    rows = [
        ("Name",    esc_name),
        ("Email",   esc_email),
        ("Company", esc_company),
        ("Phone",   esc_phone),
        ("Topic",   esc_topic),
    ]

    rows_html = "".join(
        f'<tr><td style="padding:8px 12px 8px 0;color:#64748b;font-size:13px;white-space:nowrap;vertical-align:top">{k}</td>'
        f'<td style="padding:8px 0;font-size:14px;color:#0f172a">{v}</td></tr>'
        for k, v in rows
    )

    email_html = f"""
    <div style="font-family:sans-serif;max-width:580px;margin:0 auto;padding:32px 24px">
      <div style="margin-bottom:24px">
        <div style="font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px">
          Complio — New Contact
        </div>
        <h2 style="margin:0;font-size:20px;color:#0f172a">{esc_name} got in touch</h2>
      </div>

      <table style="width:100%;border-collapse:collapse;margin-bottom:24px">
        {rows_html}
      </table>

      <div style="background:#f8fafc;border-radius:10px;padding:16px 20px">
        <p style="font-size:12px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 8px">Message</p>
        <p style="font-size:14px;color:#1e293b;line-height:1.7;white-space:pre-wrap;margin:0">{esc_message}</p>
      </div>

      <p style="margin-top:24px;font-size:12px;color:#94a3b8">
        Reply directly to this email to respond to {esc_name}.
      </p>
    </div>
    """

    resend.Emails.send({
        "from": "Complio <onboarding@resend.dev>",
        "to": [settings.contact_email],
        "reply_to": req.email,
        "subject": subject,
        "html": email_html,
    })

    return {"ok": True}


# ── Stripe ────────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: str                   # "starter" | "professional"
    success_url: str
    cancel_url: str


def _validate_redirect_url(url: str) -> None:
    allowed = [o.rstrip("/") for o in _allowed_origins]
    if not any(url.startswith(origin) for origin in allowed):
        raise HTTPException(status_code=400, detail="Invalid redirect URL.")


@app.post("/api/checkout")
async def create_checkout(req: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payments not configured.")
    _validate_redirect_url(req.success_url)
    _validate_redirect_url(req.cancel_url)
    from services.stripe_service import create_subscription_checkout
    try:
        url = await create_subscription_checkout(
            plan=req.plan,
            user_id=current_user["id"],
            user_email=current_user["email"],
            success_url=req.success_url,
            cancel_url=req.cancel_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"url": url}


@app.get("/api/billing")
async def get_billing(current_user: dict = Depends(get_current_user)):
    """Return the current user's subscription status."""
    if not settings.stripe_enabled:
        return {"subscription": None, "stripe_enabled": False}
    from services.stripe_service import get_active_subscription
    sub = await get_active_subscription(current_user["id"])
    return {"subscription": sub, "stripe_enabled": True}


@app.post("/api/billing/portal")
async def billing_portal(current_user: dict = Depends(get_current_user)):
    """Return a Stripe Customer Portal URL for subscription management."""
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payments not configured.")
    from services.stripe_service import create_portal_session
    base = _allowed_origins[0] if _allowed_origins else "http://localhost:3001"
    try:
        url = await create_portal_session(current_user["id"], return_url=f"{base}/account/billing")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"url": url}


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook not configured.")
    payload = await request.body()
    from services.stripe_service import handle_webhook
    try:
        await handle_webhook(payload, stripe_signature or "")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    return {"received": True}
