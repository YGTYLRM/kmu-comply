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
async def generate_pdf(job_id: str):
    report = job_manager.get_report(job_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found or not completed.")
    # PDF generation implemented in Phase 4
    raise HTTPException(status_code=501, detail="PDF generation not yet implemented.")


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
