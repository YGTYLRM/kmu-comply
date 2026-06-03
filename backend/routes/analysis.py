"""
Core analysis endpoints: document upload, job submission, status polling, report retrieval.
"""
import asyncio
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from config import settings
from dependencies import assert_owns_job, check_rate_limit, check_endpoint_rate_limit
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

    session_id = document_store.create_session(current_user["id"])
    saved: list[str] = []
    errors: list[str] = []

    for f in files:
        try:
            content = await f.read()
            filename = f.filename or "upload"

            try:
                # Scan beginning + middle + end so injections hidden past 4KB are caught
                content_len = len(content)
                if content_len <= 50_000:
                    preview_text = content.decode("utf-8", errors="replace")
                else:
                    chunk = 16_000
                    mid = content_len // 2
                    parts = [
                        content[:chunk],
                        content[mid - chunk // 2 : mid + chunk // 2],
                        content[-chunk:],
                    ]
                    preview_text = "\n".join(p.decode("utf-8", errors="replace") for p in parts)
                is_safe, reason = classify_document_for_injection(preview_text, source_name=filename)
                if not is_safe:
                    errors.append(f"'{filename}' was rejected: {reason}")
                    continue
            except Exception as guard_exc:
                logger.warning("injection guard error for '%s': %s — accepting file", filename, guard_exc)

            name = document_store.save_file(session_id, filename, content)
            saved.append(name)
        except ValueError as e:
            errors.append(str(e))

    if not saved and errors:
        document_store.clear(session_id)
        raise HTTPException(status_code=400, detail="; ".join(errors))

    return {"doc_session_id": session_id, "files_saved": saved, "errors": errors}


_idem_cache: dict[str, tuple[str, float]] = {}  # key → (job_id, expires_at)
_IDEM_TTL = 300.0


async def _get_cached_job(idem_key: str) -> Optional[str]:
    from config import settings
    if settings.redis_url:
        try:
            from redis.asyncio import Redis
            r = Redis.from_url(settings.redis_url, decode_responses=True)
            try:
                return await r.get(f"idem:{idem_key}")
            finally:
                await r.aclose()
        except Exception:
            pass
    now = time.monotonic()
    entry = _idem_cache.get(idem_key)
    if entry and now < entry[1]:
        return entry[0]
    return None


async def _set_cached_job(idem_key: str, job_id: str) -> None:
    from config import settings
    if settings.redis_url:
        try:
            from redis.asyncio import Redis
            r = Redis.from_url(settings.redis_url, decode_responses=True)
            try:
                await r.setex(f"idem:{idem_key}", int(_IDEM_TTL), job_id)
            finally:
                await r.aclose()
        except Exception:
            pass
    _idem_cache[idem_key] = (job_id, time.monotonic() + _IDEM_TTL)
    if len(_idem_cache) > 200:
        now = time.monotonic()
        for k in [k for k, (_, exp) in list(_idem_cache.items()) if now >= exp]:
            _idem_cache.pop(k, None)


class AnalyzeRequest(BaseModel):
    profile: CompanyProfile
    doc_session_id: Optional[str] = None
    idempotency_key: Optional[str] = None


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    if body.idempotency_key:
        idem_key = f"{current_user['id']}:{body.idempotency_key}"
        existing = await _get_cached_job(idem_key)
        if existing:
            return AnalyzeResponse(
                job_id=existing,
                status=JobStatus.PENDING,
                message="Duplicate request — returning existing job.",
            )

    await check_rate_limit(current_user["id"])

    # Verify the caller owns the document session they're referencing
    if body.doc_session_id:
        from services.document_store import document_store
        session_owner = document_store.get_session_owner(body.doc_session_id)
        if session_owner is None or session_owner != current_user["id"]:
            raise HTTPException(status_code=403, detail="Document session not found or access denied.")

    if settings.database_url:
        from services.stripe_service import get_active_subscription, check_company_limit

        sub = await get_active_subscription(current_user["id"])
        if not sub:
            raise HTTPException(status_code=402, detail="Aktives Abonnement erforderlich. Bitte wählen Sie einen Plan unter /account/billing.")
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

    if body.idempotency_key:
        await _set_cached_job(f"{current_user['id']}:{body.idempotency_key}", job_id)

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
    report = await job_manager.get_report(job_id)
    if report is None:
        status = await job_manager.get_status_async(job_id)
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
    from services.report_store import load_profile_async
    profile = await load_profile_async(job_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found for this job.")
    return profile


@router.post("/api/report/{job_id}/pdf")
async def generate_pdf_endpoint(job_id: str, current_user: dict = Depends(get_current_user)):
    from services.pdf_generator import generate_pdf as _gen_pdf

    await assert_owns_job(job_id, current_user["id"])
    await check_endpoint_rate_limit(current_user["id"], "pdf", limit=20)
    report = await job_manager.get_report(job_id)
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
