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
from dependencies import check_endpoint_rate_limit
from models import RegulationsListResponse
from models.api_responses import RegulationInfo
from services.auth_service import get_current_user
from state import contact_calls

logger = logging.getLogger(__name__)
router = APIRouter()

_CONTACT_LIMIT = 5
_CONTACT_WINDOW = 3600  # seconds


_KB_EXPECTED_MIN_CHUNKS: dict[str, int] = {
    "gdpr_dsgvo":       50,
    "bdsg":             15,
    "lksg":             15,
    "enefg":            10,
    "csrd":             80,
    "compliance_guides": 500,
    "nis2":             40,
    "eu_ai_act":        70,
    "hinschg":          30,
    "workplace_law":    150,
    "agg":              40,
    "milog":            20,
    "ttdsg":            15,
    "gwg":              40,
    "eu_data_act":      30,
}


@router.get("/api/health/deep")
async def health_deep():
    """Extended health check that validates ChromaDB collection contents.

    The shallow /api/health only checks ChromaDB connectivity. A successful
    connection with empty collections still looks healthy but the pipeline will
    silently return CANNOT_ASSESS for every regulation. This endpoint validates
    actual chunk counts against expected minimums so empty-KB failures are
    caught before they affect customers.
    """
    def _deep_chroma_check() -> dict[str, object]:
        try:
            from rag.ingest import _chroma_client
            client = _chroma_client()
            collections = {c.name: c.count() for c in client.list_collections()}
            results: dict[str, object] = {}
            total_chunks = 0
            failed: list[str] = []
            for name, min_count in _KB_EXPECTED_MIN_CHUNKS.items():
                actual = collections.get(name, 0)
                total_chunks += actual
                ok = actual >= min_count
                results[name] = {"chunks": actual, "min_expected": min_count, "ok": ok}
                if not ok:
                    failed.append(f"{name}:{actual}<{min_count}")
            return {
                "ok": len(failed) == 0,
                "total_chunks": total_chunks,
                "collections": results,
                "failed_collections": failed,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    loop = asyncio.get_event_loop()
    kb = await loop.run_in_executor(None, _deep_chroma_check)
    status = "ok" if kb.get("ok") else "degraded"
    # In production, suppress per-collection details to avoid leaking infra info
    if settings.environment == "production":
        return {"status": status, "total_chunks": kb.get("total_chunks", 0), "failed_collections": kb.get("failed_collections", [])}
    return {"status": status, **kb}


@router.post("/api/quick-check")
async def quick_check(request: Request):
    """Free applicability check — runs the deterministic threshold engine only.

    No LLM calls, no API credits, no authentication required.
    Accepts a minimal company snapshot and returns which of the 14 regulations apply
    and why. This is the top-of-funnel feature: let prospects see the value of the
    threshold engine before paying for the full gap analysis.

    Rate-limited to 20 requests per hour per IP.
    """
    from time import time as _time

    RATE_LIMIT = 20
    WINDOW = 3600

    ip = request.client.host if request.client else "unknown"
    now = _time()
    # Reuse the existing contact_calls store since it has the same pattern
    recent = [t for t in contact_calls[ip] if now - t < WINDOW]
    if len(recent) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Zu viele Anfragen. Bitte versuchen Sie es später erneut.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body.")

    try:
        employee_count = max(1, int(body.get("employee_count", 1)))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="employee_count must be a positive integer.")

    from models.company_profile import CompanyProfile
    from services.threshold_engine import determine_applicable_regulations

    # Build a minimal CompanyProfile from the quick-check request.
    # Fields not provided default to the conservative/safe choice (avoids false negatives).
    industry_raw = str(body.get("industry", "other")).lower()

    def _opt_float(key: str) -> float | None:
        val = body.get(key)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    profile = CompanyProfile(
        company_name="Vorprüfung",
        employee_count=employee_count,
        industry=industry_raw,
        country="DE",
        annual_revenue_eur=_opt_float("annual_revenue_eur"),
        balance_sheet_total_eur=_opt_float("balance_sheet_total_eur"),
        annual_energy_consumption_mwh=_opt_float("annual_energy_consumption_mwh"),
        processes_personal_data=bool(body.get("processes_personal_data", True)),
        has_website=bool(body.get("has_website", True)),
        processing_is_occasional=bool(body.get("processing_is_occasional", False)),
        processes_special_category_data=bool(body.get("processes_special_category_data", False)),
        is_listed_company=bool(body.get("is_listed_company", False)),
        is_aml_obligated_sector=bool(body.get("is_aml_obligated_sector", False)),
        uses_ai_systems=bool(body.get("uses_ai_systems", False)),
        ai_systems_are_high_risk=body.get("ai_systems_are_high_risk"),
        has_supply_chain_abroad=bool(body.get("has_supply_chain_abroad", False)),
        supply_chain_countries=body.get("supply_chain_countries") or [],
        is_critical_infrastructure_sector=bool(body.get("is_critical_infrastructure_sector", False)),
    )

    contact_calls[ip].append(now)

    _REG_DISPLAY_NAMES = {
        "gdpr_dsgvo": "GDPR / DSGVO",
        "bdsg": "BDSG",
        "lksg": "LkSG",
        "enefg": "EnEfG",
        "csrd": "CSRD",
        "nis2": "NIS2",
        "eu_ai_act": "EU AI Act",
        "hinschg": "HinSchG",
        "workplace_law": "ArbSchG",
        "agg": "AGG",
        "milog": "MiLoG",
        "ttdsg": "TTDSG / TDDDG",
        "gwg": "GwG",
        "eu_data_act": "EU Data Act",
    }

    applicability = determine_applicable_regulations(profile)
    applicable = [
        {
            "regulation": a.regulation.value,
            "name": _REG_DISPLAY_NAMES.get(a.regulation.value, a.regulation.value),
            "reason": a.reason,
        }
        for a in applicability if a.applies
    ]
    not_applicable = [
        {
            "regulation": a.regulation.value,
            "name": _REG_DISPLAY_NAMES.get(a.regulation.value, a.regulation.value),
            "reason": a.reason,
        }
        for a in applicability if not a.applies
    ]

    return {
        "applicable_count": len(applicable),
        "applicable": applicable,
        "not_applicable": not_applicable,
        "disclaimer": "Vorläufige Einschätzung auf Basis der eingegebenen Daten. Keine Rechtsberatung.",
    }


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

    if settings.llm_api_key:
        checks["llm"] = "configured (not tested — call is expensive)"
    else:
        checks["llm"] = "not_configured"

    if settings.redis_url:
        try:
            from redis.asyncio import Redis
            r = Redis.from_url(settings.redis_url, decode_responses=True)
            try:
                await r.ping()
                checks["redis"] = "ok"
            finally:
                await r.aclose()
        except Exception as exc:
            checks["redis"] = f"error: {exc}"
    else:
        checks["redis"] = "not_configured"

    overall = (
        "ok"
        if all(v.startswith("ok") or "not_configured" in v or "not tested" in v for v in checks.values())
        else "degraded"
    )
    # In production, return only the overall status — detailed checks leak infrastructure info
    if settings.environment == "production":
        return {"status": overall}
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
    await check_endpoint_rate_limit(current_user["id"], "templates", limit=30)

    if settings.stripe_enabled:
        from services.stripe_service import check_feature_access
        allowed, reason = await check_feature_access(current_user["id"], "templates")
        if not allowed:
            raise HTTPException(status_code=402, detail=reason)

    from services.report_store import load_profile_async
    from services.template_generator import generate_template as _gen

    profile = await load_profile_async(job_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found for this report.")

    try:
        content = _gen(template_id, json.dumps(profile, indent=2))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template or template parameters.")
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Template generation temporarily unavailable.")

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
