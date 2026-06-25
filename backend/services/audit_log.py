"""Records admin actions for accountability. Never stores the raw admin key."""
import hashlib
import hmac
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def fingerprint_admin_key(x_admin_key: Optional[str]) -> str:
    if not x_admin_key:
        return "unknown"
    return hmac.new(b"audit", x_admin_key.encode(), hashlib.sha256).hexdigest()[:16]


async def record_admin_action(
    *,
    x_admin_key: Optional[str],
    actor_ip: Optional[str],
    action: str,
    target_type: str,
    target_id: str,
    detail: Optional[dict] = None,
) -> None:
    from db.database import AsyncSessionLocal
    from db.models import AdminAuditLog

    try:
        async with AsyncSessionLocal() as db:
            db.add(AdminAuditLog(
                actor_fingerprint=fingerprint_admin_key(x_admin_key),
                actor_ip=actor_ip,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
            ))
            await db.commit()
    except Exception:
        logger.warning("admin audit log write failed for action=%s target=%s", action, target_id, exc_info=True)
