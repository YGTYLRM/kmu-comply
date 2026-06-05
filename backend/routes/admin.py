"""
Admin endpoints: regulation update approval workflow + expert review management.
All routes require a valid X-Admin-Key header.
"""
import asyncio
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from dependencies import require_admin

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


@router.get("/regulation-updates")
async def list_regulation_updates():
    from db.database import AsyncSessionLocal
    from db.models import PendingRegulationUpdate
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(PendingRegulationUpdate)
            .order_by(PendingRegulationUpdate.fetched_at.desc())
            .limit(100)
        )).scalars().all()

    return {"updates": [
        {
            "id": r.id,
            "regulation": r.regulation,
            "source_url": r.source_url,
            "fetched_at": r.fetched_at.isoformat() if r.fetched_at else None,
            "status": r.status,
            "change_summary": r.change_summary,
            "new_hash": r.new_hash[:12],
            "previous_hash": r.previous_hash[:12] if r.previous_hash else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        }
        for r in rows
    ]}


@router.post("/regulation-updates/{update_id}/approve")
async def approve_regulation_update(
    update_id: str,
    request: Request,
    # Read the key again for the audit trail — router dep already enforced auth
    x_admin_key: Optional[str] = Header(None),
):
    from services.regulation_updater import approve_update

    approver_ip = request.client.host if request.client else "unknown"
    # Store a short HMAC fingerprint — never the raw key prefix
    approver_id = (
        hmac.new(b"audit", x_admin_key.encode(), hashlib.sha256).hexdigest()[:16]
        if x_admin_key else "unknown"
    )
    try:
        result = await approve_update(
            update_id,
            approver_identity=approver_id,
            approver_ip=approver_ip,
        )
        return {"ok": True, **result}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/regulation-updates/{update_id}/reject")
async def reject_regulation_update(update_id: str):
    from services.regulation_updater import reject_update

    try:
        await reject_update(update_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/regulation-updates/fetch-now")
async def trigger_regulation_fetch():
    from services.regulation_updater import fetch_and_stage_updates

    asyncio.create_task(fetch_and_stage_updates())
    return {
        "ok": True,
        "message": "Fetch started in background — check /api/admin/regulation-updates for results.",
    }


# ─── Expert review management ────────────────────────────────────────────────

class UpdateExpertReviewBody(BaseModel):
    status: str  # in_review | completed
    notes: Optional[str] = None


class AssignExpertReviewBody(BaseModel):
    assigned_to: str  # email or name of the reviewer
    reviewer_notes: Optional[str] = None


@router.get("/expert-reviews")
async def list_expert_reviews_admin(status: Optional[str] = None):
    from db.database import AsyncSessionLocal
    from db.models import ExpertReviewRequest
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        stmt = select(ExpertReviewRequest).order_by(ExpertReviewRequest.created_at.desc()).limit(200)
        if status:
            stmt = stmt.where(ExpertReviewRequest.status == status)
        rows = (await db.execute(stmt)).scalars().all()

    return {"reviews": [
        {
            "id": r.id,
            "user_id": r.user_id,
            "job_id": r.job_id,
            "company_name": r.company_name,
            "user_email": r.user_email,
            "focus_items": r.focus_items,
            "message": r.message,
            "status": r.status,
            "assigned_to": r.assigned_to,
            "reviewer_notes": r.reviewer_notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        }
        for r in rows
    ]}


@router.patch("/expert-reviews/{review_id}/status")
async def update_expert_review_status(review_id: str, body: UpdateExpertReviewBody):
    if body.status not in ("in_review", "completed"):
        raise HTTPException(status_code=400, detail="status must be 'in_review' or 'completed'")

    from db.database import AsyncSessionLocal
    from db.models import ExpertReviewRequest
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        row = (await db.execute(
            select(ExpertReviewRequest).where(ExpertReviewRequest.id == review_id)
        )).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Expert review request not found.")
        row.status = body.status
        row.reviewed_at = datetime.now(timezone.utc)
        await db.commit()

    return {"ok": True, "id": review_id, "status": body.status}


@router.patch("/expert-reviews/{review_id}/assign")
async def assign_expert_review(review_id: str, body: AssignExpertReviewBody):
    from db.database import AsyncSessionLocal
    from db.models import ExpertReviewRequest
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        row = (await db.execute(
            select(ExpertReviewRequest).where(ExpertReviewRequest.id == review_id)
        )).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Expert review request not found.")
        row.assigned_to = body.assigned_to
        if body.reviewer_notes:
            row.reviewer_notes = body.reviewer_notes
        if row.status == "pending":
            row.status = "in_review"
        await db.commit()

    return {"ok": True, "id": review_id, "assigned_to": body.assigned_to}
