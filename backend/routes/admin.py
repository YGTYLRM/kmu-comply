"""
Admin endpoints: regulation update approval workflow.
All routes require a valid X-Admin-Key header.
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request

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
    approver_id = (x_admin_key[:8] + "...") if x_admin_key else "unknown"
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
