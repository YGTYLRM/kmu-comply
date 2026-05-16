"""
Core analysis endpoints: document upload, job submission, status polling, report retrieval.
"""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from config import settings
from dependencies import assert_owns_job, check_rate_limit
from models import (
    AnalyzeResponse,
    CompanyProfile,
    ComplianceReport,
    JobStatus,
    ProfileValidationResponse,
    StatusResponse,
)
from services.auth_service import get_current_user
from state import job_manager, job_owners

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/profile/validate", response_model=ProfileValidationResponse)
async def validate_profile(
    profile: CompanyProfile, current_user: dict = Depends(get_current_user)
):
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


@router.post("/api/documents")
async def upload_documents(
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    from services.document_store import document_store
    from services.injection_guard import classify_document_for_injection

    session_id = document_store.create_session()
    saved: list[str] = []
    errors: list[str] = []

    for f in files:
        try:
            content = await f.read()
            filename = f.filename or "upload"

            try:
                preview_text = content[:4000].decode("utf-8", errors="replace")
                is_safe, reason = classify_document_for_injection(preview_text, source_name=filename)
                if not is_safe:
                    errors.append(f"'{filename}' was rejected: {reason}")
                    continue
            except Exception:
                pass  # injection guard failure is non-fatal

            name = document_store.save_file(session_id, filename, content)
            saved.append(name)
        except ValueError as e:
            errors.append(str(e))

    if not saved and errors:
        document_store.clear(session_id)
        raise HTTPException(status_code=400, detail="; ".join(errors))

    return {"doc_session_id": session_id, "files_saved": saved, "errors": errors}


class AnalyzeRequest(BaseModel):
    profile: CompanyProfile
    doc_session_id: Optional[str] = None


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    await check_rate_limit(current_user["id"])

    if settings.stripe_enabled and settings.database_url:
        from services.stripe_service import get_active_subscription, check_company_limit

        sub = await get_active_subscription(current_user["id"])
        if not sub:
            raise HTTPException(status_code=402, detail="Active subscription required.")
        allowed, reason = await check_company_limit(current_user["id"])
        if not allowed:
            raise HTTPException(status_code=402, detail=reason)

    company_id: Optional[str] = None
    if settings.database_url:
        try:
            from services.db_service import upsert_company
            company_id = await upsert_company(current_user["id"], body.profile)
        except Exception as exc:
            logger.warning("analyze: db upsert failed: %s", exc)

    job_id = await job_manager.create_job(
        body.profile,
        doc_session_id=body.doc_session_id,
        user_id=current_user["id"],
        company_id=company_id,
    )
    job_owners[job_id] = current_user["id"]
    return AnalyzeResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Analysis job created. Use GET /api/status/{job_id} to track progress.",
    )


@router.get("/api/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str, current_user: dict = Depends(get_current_user)):
    await assert_owns_job(job_id, current_user["id"])
    status = await job_manager.get_status_async(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return status


@router.get("/api/report/{job_id}", response_model=ComplianceReport)
async def get_report(job_id: str, current_user: dict = Depends(get_current_user)):
    await assert_owns_job(job_id, current_user["id"])
    report = job_manager.get_report(job_id)
    if report is None:
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


@router.get("/api/report/{job_id}/profile")
async def get_profile(job_id: str, current_user: dict = Depends(get_current_user)):
    await assert_owns_job(job_id, current_user["id"])
    from services.report_store import load_profile
    profile = load_profile(job_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found for this job.")
    return profile


@router.post("/api/report/{job_id}/pdf")
async def generate_pdf_endpoint(job_id: str, current_user: dict = Depends(get_current_user)):
    from services.pdf_generator import generate_pdf as _gen_pdf

    await assert_owns_job(job_id, current_user["id"])
    report = job_manager.get_report(job_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found or not completed.")

    loop = asyncio.get_running_loop()
    pdf_bytes = await loop.run_in_executor(None, _gen_pdf, report)
    filename = f"complio-{report.company_name.replace(' ', '-')[:40]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
