from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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

job_manager = JobManager(ttl_seconds=settings.job_ttl_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await job_manager.start()
    yield
    await job_manager.stop()


app = FastAPI(
    title="KMU-Comply API",
    description="Autonomous regulatory compliance analysis for German SMEs",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        chromadb="not_connected",
        embedding_model=settings.embedding_model,
    )


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
async def upload_documents(files: list[UploadFile] = File(...)):
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
async def analyze(body: AnalyzeRequest):
    """Submit a company profile for compliance analysis. Returns a job_id."""
    job_id = await job_manager.create_job(body.profile, doc_session_id=body.doc_session_id)
    return AnalyzeResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Analysis job created. Use GET /api/status/{job_id} to track progress.",
    )


@app.get("/api/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    status = job_manager.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return status


@app.get("/api/report/{job_id}", response_model=ComplianceReport)
async def get_report(job_id: str):
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


@app.post("/api/report/{job_id}/pdf")
async def generate_pdf_endpoint(job_id: str):
    import asyncio
    from fastapi.responses import Response
    from services.pdf_generator import generate_pdf as _gen_pdf

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


@app.post("/api/contact")
async def contact(req: ContactRequest):
    if not settings.resend_api_key or not settings.contact_email:
        raise HTTPException(status_code=503, detail="Contact not configured.")

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
