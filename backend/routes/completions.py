"""
Action item workflow state (completions) — per-report, per-user.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import assert_owns_job
from services.auth_service import get_current_user

router = APIRouter()


class CompletionRequest(BaseModel):
    regulation: str
    article_number: str
    status: str = "done"  # open | in_progress | done
    notes: Optional[str] = None
    evidence_note: Optional[str] = None


@router.get("/api/report/{job_id}/completions")
async def get_completions(job_id: str, current_user: dict = Depends(get_current_user)):
    await assert_owns_job(job_id, current_user["id"])
    from db.database import AsyncSessionLocal
    from db.models import ActionCompletion
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(ActionCompletion).where(
                ActionCompletion.job_id == job_id,
                ActionCompletion.user_id == current_user["id"],
            )
        )).scalars().all()

    return {"completions": [
        {
            "regulation": r.regulation,
            "article_number": r.article_number,
            "status": r.status,
            "notes": r.notes,
            "evidence_note": r.evidence_note,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in rows
    ]}


@router.post("/api/report/{job_id}/completions")
async def upsert_completion(
    job_id: str,
    req: CompletionRequest,
    current_user: dict = Depends(get_current_user),
):
    if req.status not in ("open", "in_progress", "done"):
        raise HTTPException(status_code=400, detail="status must be open, in_progress, or done")
    await assert_owns_job(job_id, current_user["id"])

    from db.database import AsyncSessionLocal
    from db.models import ActionCompletion
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        row = (await db.execute(
            select(ActionCompletion).where(
                ActionCompletion.job_id == job_id,
                ActionCompletion.user_id == current_user["id"],
                ActionCompletion.regulation == req.regulation,
                ActionCompletion.article_number == req.article_number,
            )
        )).scalar_one_or_none()

        if row:
            row.status = req.status
            row.notes = req.notes if req.notes is not None else row.notes
            row.evidence_note = req.evidence_note if req.evidence_note is not None else row.evidence_note
            if req.status == "done" and not row.completed_at:
                row.completed_at = datetime.now(timezone.utc)
            elif req.status != "done":
                row.completed_at = None
        else:
            db.add(ActionCompletion(
                user_id=current_user["id"],
                job_id=job_id,
                regulation=req.regulation,
                article_number=req.article_number,
                status=req.status,
                notes=req.notes,
                evidence_note=req.evidence_note,
                completed_at=datetime.now(timezone.utc) if req.status == "done" else None,
            ))
        await db.commit()

    return {"ok": True}


@router.delete("/api/report/{job_id}/completions")
async def reset_completion(
    job_id: str,
    req: CompletionRequest,
    current_user: dict = Depends(get_current_user),
):
    await assert_owns_job(job_id, current_user["id"])
    from db.database import AsyncSessionLocal
    from db.models import ActionCompletion
    from sqlalchemy import delete

    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(ActionCompletion).where(
                ActionCompletion.job_id == job_id,
                ActionCompletion.user_id == current_user["id"],
                ActionCompletion.regulation == req.regulation,
                ActionCompletion.article_number == req.article_number,
            )
        )
        await db.commit()

    return {"ok": True}
