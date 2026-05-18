"""
Expert review request endpoints.
"""
import html
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import settings
from dependencies import assert_owns_job
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class ExpertReviewRequestBody(BaseModel):
    job_id: str
    message: Optional[str] = None
    focus_items: Optional[list[dict]] = None


@router.post("/api/expert-review")
async def request_expert_review(
    req: ExpertReviewRequestBody,
    current_user: dict = Depends(get_current_user),
):
    await assert_owns_job(req.job_id, current_user["id"])

    if settings.stripe_enabled:
        from services.stripe_service import check_feature_access
        allowed, reason = await check_feature_access(current_user["id"], "expert_review")
        if not allowed:
            raise HTTPException(status_code=402, detail=reason)

    from services.report_store import load_profile_async
    profile = await load_profile_async(req.job_id)
    company_name = profile.get("company_name", "Unknown") if profile else "Unknown"

    from db.database import AsyncSessionLocal
    from db.models import ExpertReviewRequest

    async with AsyncSessionLocal() as db:
        review = ExpertReviewRequest(
            user_id=current_user["id"],
            job_id=req.job_id,
            company_name=company_name,
            user_email=current_user.get("email"),
            focus_items=req.focus_items,
            message=req.message,
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        review_id = review.id

    if settings.resend_api_key and settings.contact_email:
        try:
            import resend
            resend.api_key = settings.resend_api_key
            esc_company = html.escape(company_name)
            esc_email   = html.escape(current_user.get("email", "unknown"))
            esc_message = html.escape(req.message or "No message provided")
            focus_str   = ", ".join(
                f"{f.get('regulation','?')} {f.get('article_number','?')}"
                for f in (req.focus_items or [])
            ) or "Full report review"
            resend.Emails.send({
                "from": "Complio <onboarding@resend.dev>",
                "to": [settings.contact_email],
                "subject": f"Expert Review Request — {company_name}",
                "html": (
                    f'<div style="font-family:sans-serif;max-width:560px">'
                    f'<h2>New Expert Review Request</h2>'
                    f'<p><b>Company:</b> {esc_company}</p>'
                    f'<p><b>User:</b> {esc_email}</p>'
                    f'<p><b>Report:</b> {req.job_id}</p>'
                    f'<p><b>Focus:</b> {html.escape(focus_str)}</p>'
                    f'<p><b>Message:</b> {esc_message}</p>'
                    f'<p><b>Review ID:</b> {review_id}</p>'
                    f'</div>'
                ),
            })
        except Exception as exc:
            logger.warning("expert review email failed: %s", exc)

    return {
        "ok": True,
        "review_id": review_id,
        "message": "Expert review request submitted. We will contact you within 2 business days.",
    }


@router.get("/api/expert-review")
async def list_expert_reviews(current_user: dict = Depends(get_current_user)):
    from db.database import AsyncSessionLocal
    from db.models import ExpertReviewRequest
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(ExpertReviewRequest)
            .where(ExpertReviewRequest.user_id == current_user["id"])
            .order_by(ExpertReviewRequest.created_at.desc())
        )).scalars().all()

    return {"requests": [
        {
            "id": r.id,
            "job_id": r.job_id,
            "company_name": r.company_name,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]}
