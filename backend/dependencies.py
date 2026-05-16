"""
Shared FastAPI dependencies and request-guard helpers.
"""
import logging
from datetime import datetime, timezone, timedelta
from time import time

from fastapi import HTTPException, Header

from config import settings
from state import job_owners, analyze_calls_fallback

logger = logging.getLogger(__name__)

ANALYZE_LIMIT = 10
ANALYZE_WINDOW = 3600  # seconds


async def check_rate_limit(user_id: str) -> None:
    if settings.database_url:
        from db.database import AsyncSessionLocal
        from db.models import RateLimitEvent
        from sqlalchemy import select, func, delete

        now_dt = datetime.now(timezone.utc)
        window_start = now_dt - timedelta(seconds=ANALYZE_WINDOW)
        async with AsyncSessionLocal() as db:
            count = (await db.execute(
                select(func.count()).where(
                    RateLimitEvent.user_id == user_id,
                    RateLimitEvent.endpoint == "analyze",
                    RateLimitEvent.called_at >= window_start,
                )
            )).scalar_one()
            if count >= ANALYZE_LIMIT:
                oldest = (await db.execute(
                    select(func.min(RateLimitEvent.called_at)).where(
                        RateLimitEvent.user_id == user_id,
                        RateLimitEvent.endpoint == "analyze",
                        RateLimitEvent.called_at >= window_start,
                    )
                )).scalar_one()
                retry_in = int(ANALYZE_WINDOW - (now_dt - oldest).total_seconds()) + 1
                mins, secs = retry_in // 60, retry_in % 60
                wait = f"{mins}m {secs}s" if mins else f"{secs}s"
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit reached — maximum {ANALYZE_LIMIT} screenings per hour. "
                           f"Try again in {wait}.",
                    headers={"Retry-After": str(retry_in)},
                )
            db.add(RateLimitEvent(user_id=user_id, endpoint="analyze"))
            await db.execute(
                delete(RateLimitEvent).where(
                    RateLimitEvent.called_at < now_dt - timedelta(hours=2)
                )
            )
            await db.commit()
    else:
        now = time()
        calls = [t for t in analyze_calls_fallback[user_id] if now - t < ANALYZE_WINDOW]
        analyze_calls_fallback[user_id] = calls
        if len(calls) >= ANALYZE_LIMIT:
            oldest = min(calls)
            retry_in = int(ANALYZE_WINDOW - (now - oldest)) + 1
            mins, secs = retry_in // 60, retry_in % 60
            wait = f"{mins}m {secs}s" if mins else f"{secs}s"
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit reached — maximum {ANALYZE_LIMIT} screenings per hour. "
                       f"Try again in {wait}.",
                headers={"Retry-After": str(retry_in)},
            )
        analyze_calls_fallback[user_id].append(now)


async def assert_owns_job(job_id: str, user_id: str) -> None:
    owner = job_owners.get(job_id)
    if owner is None and settings.database_url:
        from services.db_service import get_job_owner
        owner = await get_job_owner(job_id)
    if owner is None or owner != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")


def validate_redirect_url(url: str, allowed_origins: list[str]) -> None:
    if not any(url.startswith(origin) for origin in allowed_origins):
        raise HTTPException(status_code=400, detail="Invalid redirect URL.")


def require_admin(x_admin_key: str = Header(None)) -> None:
    if not settings.admin_api_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin access required.")
