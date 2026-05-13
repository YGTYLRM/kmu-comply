"""
Stripe subscription billing service.

Plans:
  starter      — €49/month  — 1 company, monthly reassessment
  professional — €149/month — 3 companies, weekly reassessment
  enterprise   — custom     — contact us

Activation: set STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_ENABLED=true in .env
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

PLAN_CONFIG = {
    "starter": {
        "name": "Complio Starter",
        "amount": 4900,
        "currency": "eur",
        "interval": "month",
        "company_limit": 1,
        "reassessment_days": 30,
    },
    "professional": {
        "name": "Complio Professional",
        "amount": 14900,
        "currency": "eur",
        "interval": "month",
        "company_limit": 3,
        "reassessment_days": 7,
    },
}


def _stripe():
    import stripe
    stripe.api_key = settings.stripe_secret_key
    return stripe


# ── Checkout ──────────────────────────────────────────────────────────────────

async def create_subscription_checkout(
    plan: str,
    user_id: str,
    user_email: str,
    success_url: str,
    cancel_url: str,
) -> str:
    if plan not in PLAN_CONFIG:
        raise ValueError(f"Unknown plan: {plan}")
    cfg    = PLAN_CONFIG[plan]
    stripe = _stripe()
    customer_id = await _get_or_create_customer(user_id, user_email)
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{
            "price_data": {
                "currency": cfg["currency"],
                "unit_amount": cfg["amount"],
                "product_data": {"name": cfg["name"]},
                "recurring": {"interval": cfg["interval"]},
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=user_id,
        subscription_data={"metadata": {"plan": plan, "user_id": user_id}},
        allow_promotion_codes=True,
    )
    return session.url


async def create_portal_session(user_id: str, return_url: str) -> str:
    stripe      = _stripe()
    customer_id = await _get_stripe_customer_id(user_id)
    if not customer_id:
        raise ValueError("No Stripe customer found for this user.")
    session = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
    return session.url


# ── Subscription queries ──────────────────────────────────────────────────────

async def get_active_subscription(user_id: str) -> Optional[dict]:
    from db.database import AsyncSessionLocal
    from db.models import Subscription
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_(["active", "trialing"]),
            )
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return None
        return {
            "plan": sub.plan,
            "status": sub.status,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "stripe_subscription_id": sub.stripe_subscription_id,
            "company_limit": PLAN_CONFIG.get(sub.plan, {}).get("company_limit", 999),
            "reassessment_days": PLAN_CONFIG.get(sub.plan, {}).get("reassessment_days", 30),
        }


async def check_company_limit(user_id: str) -> tuple[bool, str]:
    if not settings.stripe_enabled:
        return True, ""
    sub = await get_active_subscription(user_id)
    if not sub:
        return False, "Active subscription required."
    limit = sub["company_limit"]
    from db.database import AsyncSessionLocal
    from db.models import Company
    from sqlalchemy import select, func
    async with AsyncSessionLocal() as db:
        count = (await db.execute(
            select(func.count()).where(Company.user_id == user_id)
        )).scalar_one() or 0
    if count >= limit:
        return False, (
            f"Your {sub['plan'].capitalize()} plan allows {limit} "
            f"company profile{'s' if limit != 1 else ''}. Upgrade to add more."
        )
    return True, ""


# ── Webhook ───────────────────────────────────────────────────────────────────

async def handle_webhook(payload: bytes, signature: str) -> None:
    stripe = _stripe()
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except Exception as exc:
        logger.warning("stripe: invalid webhook signature: %s", exc)
        raise

    etype = event["type"]
    logger.info("stripe: event %s", etype)

    if etype == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("mode") == "subscription":
            await _on_subscription_created(session)

    elif etype in ("customer.subscription.updated", "customer.subscription.created"):
        await _on_subscription_updated(event["data"]["object"])

    elif etype == "customer.subscription.deleted":
        await _on_subscription_canceled(event["data"]["object"])

    elif etype == "invoice.payment_failed":
        await _on_payment_failed(event["data"]["object"])


async def _on_subscription_created(session: dict) -> None:
    user_id = session.get("client_reference_id")
    sub_id  = session.get("subscription")
    if not user_id or not sub_id:
        return
    stripe = _stripe()
    sub    = stripe.Subscription.retrieve(sub_id)
    plan   = sub.get("metadata", {}).get("plan", "starter")
    await _upsert_sub(
        user_id=user_id,
        customer_id=session.get("customer"),
        sub_id=sub_id,
        plan=plan,
        status=sub["status"],
        period_end=sub.get("current_period_end"),
    )
    logger.info("stripe: subscription created user=%s plan=%s", user_id, plan)


async def _on_subscription_updated(sub: dict) -> None:
    plan = sub.get("metadata", {}).get("plan", "starter")
    await _upsert_sub_by_stripe_id(
        sub_id=sub["id"],
        customer_id=sub.get("customer"),
        plan=plan,
        status=sub["status"],
        period_end=sub.get("current_period_end"),
    )


async def _on_subscription_canceled(sub: dict) -> None:
    plan = sub.get("metadata", {}).get("plan", "starter")
    await _upsert_sub_by_stripe_id(
        sub_id=sub["id"],
        customer_id=sub.get("customer"),
        plan=plan,
        status="canceled",
        period_end=sub.get("current_period_end"),
    )


async def _on_payment_failed(invoice: dict) -> None:
    sub_id = invoice.get("subscription")
    if not sub_id:
        return
    await _upsert_sub_by_stripe_id(
        sub_id=sub_id,
        customer_id=invoice.get("customer"),
        plan=None,
        status="past_due",
        period_end=None,
    )


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _get_or_create_customer(user_id: str, user_email: str) -> str:
    existing = await _get_stripe_customer_id(user_id)
    if existing:
        return existing
    stripe   = _stripe()
    customer = stripe.Customer.create(email=user_email, metadata={"user_id": user_id})
    return customer["id"]


async def _get_stripe_customer_id(user_id: str) -> Optional[str]:
    from db.database import AsyncSessionLocal
    from db.models import Subscription
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Subscription.stripe_customer_id).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def _upsert_sub(
    user_id: str, customer_id: Optional[str], sub_id: str,
    plan: str, status: str, period_end: Optional[int],
) -> None:
    from db.database import AsyncSessionLocal
    from db.models import Subscription
    from sqlalchemy import select
    period_dt = datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else None
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
        sub = result.scalar_one_or_none()
        if sub:
            sub.stripe_customer_id     = customer_id or sub.stripe_customer_id
            sub.stripe_subscription_id = sub_id
            sub.plan                   = plan
            sub.status                 = status
            sub.current_period_end     = period_dt
            sub.updated_at             = datetime.now(timezone.utc)
        else:
            db.add(Subscription(
                user_id=user_id, stripe_customer_id=customer_id,
                stripe_subscription_id=sub_id, plan=plan,
                status=status, current_period_end=period_dt,
            ))
        await db.commit()


async def _upsert_sub_by_stripe_id(
    sub_id: str, customer_id: Optional[str],
    plan: Optional[str], status: str, period_end: Optional[int],
) -> None:
    from db.database import AsyncSessionLocal
    from db.models import Subscription
    from sqlalchemy import select
    period_dt = datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else None
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status             = status
            sub.current_period_end = period_dt
            if plan:
                sub.plan = plan
            sub.updated_at = datetime.now(timezone.utc)
            await db.commit()
