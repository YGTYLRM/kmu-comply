from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from collections import defaultdict
from time import time

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

# Simple in-memory rate limiter: user_id → list of timestamps
_analyze_calls: dict[str, list[float]] = defaultdict(list)
ANALYZE_LIMIT = 10   # max requests
ANALYZE_WINDOW = 3600  # per hour

# Job ownership: job_id → user_id (guards report endpoints)
_job_owners: dict[str, str] = {}


def _check_rate_limit(user_id: str) -> None:
    now = time()
    calls = [t for t in _analyze_calls[user_id] if now - t < ANALYZE_WINDOW]
    _analyze_calls[user_id] = calls
    if len(calls) >= ANALYZE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit reached. Maximum 10 screenings per hour.")
    _analyze_calls[user_id].append(now)


def _assert_owns_job(job_id: str, user_id: str) -> None:
    owner = _job_owners.get(job_id)
    if owner is None:
        return  # legacy job from before auth — allow
    if owner != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    allow_headers=["Authorization", "Content-Type", "X-Access-Token"],
)


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
async def validate_profile(profile: CompanyProfile):
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
    _check_rate_limit(current_user["id"])
    job_id = await job_manager.create_job(body.profile, doc_session_id=body.doc_session_id)
    _job_owners[job_id] = current_user["id"]
    return AnalyzeResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Analysis job created. Use GET /api/status/{job_id} to track progress.",
    )


@app.get("/api/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str, current_user: dict = Depends(get_current_user)):
    _assert_owns_job(job_id, current_user["id"])
    status = job_manager.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return status


@app.get("/api/report/{job_id}", response_model=ComplianceReport)
async def get_report(job_id: str, current_user: dict = Depends(get_current_user)):
    _assert_owns_job(job_id, current_user["id"])
    report = job_manager.get_report(job_id)
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
    _assert_owns_job(job_id, current_user["id"])
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

    _assert_owns_job(job_id, current_user["id"])
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
    from services.report_store import list_recent
    all_reports = list_recent()
    user_job_ids = {jid for jid, uid in _job_owners.items() if uid == current_user["id"]}
    # Include reports with no owner (legacy) only if they exist — filter to user's own
    user_reports = [r for r in all_reports if r["job_id"] not in _job_owners or r["job_id"] in user_job_ids]
    return {"reports": user_reports}


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

    rows = [
        ("Name",    req.name),
        ("Email",   req.email),
        ("Company", req.company or "Not provided"),
        ("Phone",   req.phone   or "Not provided"),
        ("Topic",   req.topic   or "Not specified"),
    ]

    rows_html = "".join(
        f'<tr><td style="padding:8px 12px 8px 0;color:#64748b;font-size:13px;white-space:nowrap;vertical-align:top">{k}</td>'
        f'<td style="padding:8px 0;font-size:14px;color:#0f172a">{v}</td></tr>'
        for k, v in rows
    )

    html = f"""
    <div style="font-family:sans-serif;max-width:580px;margin:0 auto;padding:32px 24px">
      <div style="margin-bottom:24px">
        <div style="font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px">
          Complio — New Contact
        </div>
        <h2 style="margin:0;font-size:20px;color:#0f172a">{req.name} got in touch</h2>
      </div>

      <table style="width:100%;border-collapse:collapse;margin-bottom:24px">
        {rows_html}
      </table>

      <div style="background:#f8fafc;border-radius:10px;padding:16px 20px">
        <p style="font-size:12px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 8px">Message</p>
        <p style="font-size:14px;color:#1e293b;line-height:1.7;white-space:pre-wrap;margin:0">{req.message}</p>
      </div>

      <p style="margin-top:24px;font-size:12px;color:#94a3b8">
        Reply directly to this email to respond to {req.name}.
      </p>
    </div>
    """

    resend.Emails.send({
        "from": "Complio <onboarding@resend.dev>",
        "to": [settings.contact_email],
        "reply_to": req.email,
        "subject": subject,
        "html": html,
    })

    return {"ok": True}


# ── Stripe ────────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: str                   # "starter" | "professional"
    success_url: str
    cancel_url: str


@app.post("/api/checkout")
async def create_checkout(req: CheckoutRequest):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payments not configured.")
    from services.stripe_service import create_checkout_session
    try:
        url = create_checkout_session(req.plan, req.success_url, req.cancel_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"url": url}


@app.get("/api/checkout/verify")
async def verify_checkout(session_id: str):
    """Success page calls this to exchange a Stripe session_id for an access token."""
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payments not configured.")
    from services.stripe_service import verify_session
    token = verify_session(session_id)
    if not token:
        raise HTTPException(status_code=402, detail="Payment not confirmed.")
    return {"token": token}


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook not configured.")
    payload = await request.body()
    from services.stripe_service import handle_webhook
    token = handle_webhook(payload, stripe_signature or "")
    return {"received": True}
