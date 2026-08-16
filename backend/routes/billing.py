"""
Stripe billing endpoints: checkout, subscription status, portal, webhook.
"""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from config import settings
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def _allowed_origins() -> list[str]:
    raw = settings.allowed_origins or "http://localhost:3000,http://localhost:3001"
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


def _validate_redirect_url(url: str) -> None:
    if not any(url.startswith(origin) for origin in _allowed_origins()):
        raise HTTPException(status_code=400, detail="Invalid redirect URL.")


class CheckoutRequest(BaseModel):
    plan: str
    success_url: str
    cancel_url: str


@router.post("/api/checkout")
async def create_checkout(
    req: CheckoutRequest, current_user: dict = Depends(get_current_user)
):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payments not configured.")
    _validate_redirect_url(req.success_url)
    _validate_redirect_url(req.cancel_url)
    from services.stripe_service import create_subscription_checkout

    try:
        url = await create_subscription_checkout(
            plan=req.plan,
            user_id=current_user["id"],
            user_email=current_user["email"],
            success_url=req.success_url,
            cancel_url=req.cancel_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"url": url}


@router.get("/api/billing")
async def get_billing(current_user: dict = Depends(get_current_user)):
    if not settings.stripe_enabled:
        return {"subscription": None, "stripe_enabled": False}
    from services.stripe_service import get_active_subscription

    sub = await get_active_subscription(current_user["id"])
    return {"subscription": sub, "stripe_enabled": True}


@router.post("/api/billing/portal")
async def billing_portal(current_user: dict = Depends(get_current_user)):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payments not configured.")
    from services.stripe_service import create_portal_session

    origins = _allowed_origins()
    base = origins[0] if origins else "http://localhost:3001"
    try:
        url = await create_portal_session(
            current_user["id"], return_url=f"{base}/account/billing"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"url": url}


@router.post("/api/webhook/stripe")
async def stripe_webhook(
    request: Request, stripe_signature: str = Header(None)
):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook not configured.")
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header.")
    payload = await request.body()
    from services.stripe_service import handle_webhook

    try:
        await handle_webhook(payload, stripe_signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    except Exception:
        logger.exception("stripe webhook processing error")
        raise HTTPException(status_code=500, detail="Webhook processing failed.")
