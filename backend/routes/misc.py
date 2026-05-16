"""
Miscellaneous endpoints: health, auth sync, contact, regulations list, templates, plans.
"""
import asyncio
import html
import json
import logging
from time import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from config import settings
from models import RegulationsListResponse
from models.api_responses import RegulationInfo
from services.auth_service import get_current_user
from state import contact_calls

logger = logging.getLogger(__name__)
router = APIRouter()

_CONTACT_LIMIT = 5
_CONTACT_WINDOW = 3600  # seconds


@router.get("/api/health")
async def health():
    checks: dict[str, str] = {}

    def _chroma_check():
        try:
            from rag.ingest import _chroma_client
            _chroma_client().list_collections()
            return "ok"
        except Exception as exc:
            return f"error: {exc}"

    loop = asyncio.get_event_loop()
    checks["chromadb"] = await loop.run_in_executor(None, _chroma_check)

    if settings.database_url:
        try:
            from db.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as db:
                await db.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"
    else:
        checks["database"] = "not_configured"

    checks["llm"] = "configured" if settings.llm_api_key else "not_configured"

    overall = (
        "ok"
        if all(v in ("ok", "configured", "not_configured") for v in checks.values())
        else "degraded"
    )
    return {
        "status": overall,
        "environment": settings.environment,
        "embedding_model": settings.embedding_model,
        "checks": checks,
    }


@router.post("/api/auth/sync-profile")
async def sync_profile(current_user: dict = Depends(get_current_user)):
    if not settings.database_url:
        return {"ok": True}
    from db.database import AsyncSessionLocal
    from db.models import Profile
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Profile).where(Profile.id == current_user["id"])
        )
        if not result.scalar_one_or_none():
            db.add(Profile(id=current_user["id"], email=current_user["email"]))
            await db.commit()
    return {"ok": True}


@router.get("/api/regulations", response_model=RegulationsListResponse)
async def list_regulations():
    regs = [
        RegulationInfo(id="gdpr_dsgvo",  name="GDPR / DSGVO", description="General Data Protection Regulation",                  document_count=0),
        RegulationInfo(id="lksg",        name="LkSG",          description="Supply Chain Due Diligence Act",                     document_count=0),
        RegulationInfo(id="enefg",       name="EnEfG",         description="Energy Efficiency Act",                              document_count=0),
        RegulationInfo(id="csrd",        name="CSRD",          description="Corporate Sustainability Reporting Directive",        document_count=0),
        RegulationInfo(id="bdsg",        name="BDSG",          description="Federal Data Protection Act (Bundesdatenschutzgesetz)", document_count=0),
    ]
    return RegulationsListResponse(regulations=regs)


@router.get("/api/plans")
async def list_plans():
    from services.stripe_service import PLAN_CONFIG
    return {
        "plans": [
            {
                "id": plan_id,
                "name": cfg["name"],
                "amount_cents": cfg["amount"],
                "currency": cfg["currency"],
                "interval": cfg["interval"],
                "company_limit": cfg["company_limit"],
                "reassessment_days": cfg["reassessment_days"],
                "features": cfg.get("features", []),
            }
            for plan_id, cfg in PLAN_CONFIG.items()
        ]
    }


@router.get("/api/templates")
async def list_templates():
    from services.template_generator import TEMPLATES
    return {"templates": [
        {
            "id": tid,
            "title": t["title"],
            "regulation": t["regulation"],
            "description": t["description"],
        }
        for tid, t in TEMPLATES.items()
    ]}


@router.post("/api/report/{job_id}/templates/{template_id}")
async def generate_template(
    job_id: str,
    template_id: str,
    current_user: dict = Depends(get_current_user),
):
    from dependencies import assert_owns_job
    await assert_owns_job(job_id, current_user["id"])

    if settings.stripe_enabled:
        from services.stripe_service import check_feature_access
        allowed, reason = await check_feature_access(current_user["id"], "templates")
        if not allowed:
            raise HTTPException(status_code=402, detail=reason)

    from services.report_store import load_profile
    from services.template_generator import generate_template as _gen

    profile = load_profile(job_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found for this report.")

    try:
        content = _gen(template_id, json.dumps(profile, indent=2))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {"template_id": template_id, "content": content}


class ContactRequest(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    phone: Optional[str] = None
    topic: Optional[str] = None
    message: str


@router.post("/api/contact")
async def contact(req: ContactRequest, request: Request):
    if not settings.resend_api_key or not settings.contact_email:
        raise HTTPException(status_code=503, detail="Contact not configured.")

    ip = request.client.host if request.client else "unknown"
    now = time()
    recent = [t for t in contact_calls[ip] if now - t < _CONTACT_WINDOW]
    contact_calls[ip] = recent
    if len(recent) >= _CONTACT_LIMIT:
        raise HTTPException(status_code=429, detail="Too many contact requests. Try again later.")
    contact_calls[ip].append(now)

    import resend
    resend.api_key = settings.resend_api_key

    subject = f"Contact: {req.name}"
    if req.topic:
        subject += f" — {req.topic}"
    if req.company:
        subject += f" ({req.company})"

    esc_name    = html.escape(req.name)
    esc_email   = html.escape(req.email)
    esc_company = html.escape(req.company or "Not provided")
    esc_phone   = html.escape(req.phone   or "Not provided")
    esc_topic   = html.escape(req.topic   or "Not specified")
    esc_message = html.escape(req.message)

    rows_html = "".join(
        f'<tr><td style="padding:8px 12px 8px 0;color:#64748b;font-size:13px;white-space:nowrap;vertical-align:top">{k}</td>'
        f'<td style="padding:8px 0;font-size:14px;color:#0f172a">{v}</td></tr>'
        for k, v in [
            ("Name", esc_name), ("Email", esc_email), ("Company", esc_company),
            ("Phone", esc_phone), ("Topic", esc_topic),
        ]
    )

    email_html = (
        f'<div style="font-family:sans-serif;max-width:580px;margin:0 auto;padding:32px 24px">'
        f'<div style="margin-bottom:24px">'
        f'<div style="font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px">Complio — New Contact</div>'
        f'<h2 style="margin:0;font-size:20px;color:#0f172a">{esc_name} got in touch</h2>'
        f'</div>'
        f'<table style="width:100%;border-collapse:collapse;margin-bottom:24px">{rows_html}</table>'
        f'<div style="background:#f8fafc;border-radius:10px;padding:16px 20px">'
        f'<p style="font-size:12px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 8px">Message</p>'
        f'<p style="font-size:14px;color:#1e293b;line-height:1.7;white-space:pre-wrap;margin:0">{esc_message}</p>'
        f'</div>'
        f'<p style="margin-top:24px;font-size:12px;color:#94a3b8">Reply directly to this email to respond to {esc_name}.</p>'
        f'</div>'
    )

    resend.Emails.send({
        "from": "Complio <onboarding@resend.dev>",
        "to": [settings.contact_email],
        "reply_to": req.email,
        "subject": subject,
        "html": email_html,
    })

    return {"ok": True}
