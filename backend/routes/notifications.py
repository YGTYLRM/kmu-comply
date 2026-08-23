"""
User notification endpoints.
"""
from fastapi import APIRouter, Depends

from services.auth_service import get_current_user

router = APIRouter()


@router.get("/api/notifications")
async def list_notifications(current_user: dict = Depends(get_current_user)):
    from services.notification_service import get_notifications
    return {"notifications": await get_notifications(current_user["id"])}


@router.get("/api/notifications/unread-count")
async def unread_count(current_user: dict = Depends(get_current_user)):
    from services.notification_service import get_unread_count
    return {"count": await get_unread_count(current_user["id"])}


@router.post("/api/notifications/mark-read")
async def mark_notifications_read(current_user: dict = Depends(get_current_user)):
    from services.notification_service import mark_all_read
    await mark_all_read(current_user["id"])
    return {"ok": True}
