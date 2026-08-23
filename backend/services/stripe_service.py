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
        "amount": 4900,            # €49/month
        "currency": "eur",
        "interval": "month",
        "company_limit": 1,        # 1 company profile — the primary differentiator
        "reassessment_days": 30,   # monthly auto re-assessment
        "features": [
            "1 company profile",
            "14 regulations checked",
            "Full gap analysis & action plan",
            "PDF report export",
            "Monthly automatic re-assessment",
            "Regulation change alerts",
        ],
    },
    "professional": {
        "name": "Complio Professional",
        "amount": 14900,           # €149/month
        "currency": "eur",
        "interval": "month",
        "company_limit": 5,        # 5 companies — main upsell reason
        "reassessment_days": 7,    # weekly re-assessment
        "features": [
            "Up to 5 company profiles",
            "14 regulations checked per company",
            "Full gap analysis & action plan",
            "PDF report export",
            "Weekly automatic re-assessment",
            "Regulation change alerts",
            "Document upload & evidence extraction",
            "Priority support",
        ],
    },
    "enterprise": {
        "name": "Complio Enterprise",
        "amount": 0,               # custom pricing — contact us
        "currency": "eur",
        "interval": "month",
        "company_limit": 999,      # unlimited
        "reassessment_days": 7,
        "features": [
            "Unlimited company profiles",
            "Custom regulation coverage",
            "White-label PDF reports",
            "API access",
            "Dedicated compliance expert review",
            "SLA-backed support",
        ],
    },
    # Annual plans — ~20% discount vs monthly
    "starter_annual": {
        "name": "Complio Starter (Annual)",
        "amount": 47000,           # €470/year (~€39/month, ~20% off €49)
        "currency": "eur",
        "interval": "year",
        "company_limit": 1,
        "reassessment_days": 30,
        "features": [
            "1 company profile",
            "14 regulations checked",
            "Full gap analysis & action plan",
            "PDF report export",
            "Monthly automatic re-assessment",
            "Regulation change alerts",
            "20% discount vs monthly",
        ],
    },
    "professional_annual": {
        "name": "Complio Professional (Annual)",
        "amount": 143000,          # €1,430/year (~€119/month, ~20% off €149)
        "currency": "eur",
        "interval": "year",
        "company_limit": 5,
        "reassessment_days": 7,
        "features": [
            "Up to 5 company profiles",
            "14 regulations checked per company",
            "Document template generation",
            "Expert review access",
            "Weekly automatic re-assessment",
            "Document upload & evidence extraction",
            "Priority support",
            "20% discount vs monthly",
        ],
    },
    # One-time report credit — for lead capture and first-time buyers
    "report_credit": {
        "name": "Complio Single Report",
        "amount": 1900,            # €19 one-time report
        "currency": "eur",
        "interval": "one_time",
        "company_limit": 1,
        "reassessment_days": 0,    # no re-assessment
        "features": [
            "1 compliance screening",
            "14 regulations checked",
            "Full gap analysis & action plan",
            "PDF report export",
            "No subscription required",
        ],
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
    is_one_time = cfg["interval"] == "one_time"
    mode = "payment" if is_one_time else "subscription"

    price_data: dict = {
        "currency": cfg["currency"],
        "unit_amount": cfg["amount"],
        "product_data": {"name": cfg["name"]},
    }
    if not is_one_time:
        price_data["recurring"] = {
            "interval": "year" if cfg["interval"] == "year" else "month"
        }

    session_kwargs: dict = dict(
        customer=customer_id,
        mode=mode,
        line_items=[{"price_data": price_data, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=user_id,
        allow_promotion_codes=True,
    )
    if not is_one_time:
        session_kwargs["subscription_data"] = {"metadata": {"plan": plan, "user_id": user_id}}
    else:
        session_kwargs["payment_intent_data"] = {"metadata": {"plan": plan, "user_id": user_id}}

    session = stripe.checkout.Session.create(**session_kwargs)
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


async def check_feature_access(user_id: str, feature: str) -> tuple[bool, str]:
    """
    Check if the user's plan grants access to a specific feature.
    Features: 'templates', 'document_upload', 'expert_review'
    Returns (allowed, reason_if_denied).
    """
    sub = await get_active_subscription(user_id)
    if not sub:
        return False, "Active subscription required."
    plan = sub["plan"]

    FEATURE_GATES = {
        "templates":       {"professional", "enterprise"},
        "document_upload": {"starter", "professional", "enterprise"},
        "expert_review":   {"professional", "enterprise"},
    }
    allowed_plans = FEATURE_GATES.get(feature, {"starter", "professional", "enterprise"})
    if plan not in allowed_plans:
        plan_names = " or ".join(p.capitalize() for p in sorted(allowed_plans))
        return False, (
            f"This feature requires a {plan_names} plan. "
            f"Your current plan is {plan.capitalize()}. Upgrade to access it."
        )
    return True, ""


async def check_company_limit(user_id: str) -> tuple[bool, str]:
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
        raise ValueError(f"Invalid signature: {exc}") from exc

    etype = event["type"]
    logger.info("stripe: event %s", etype)

    # event["data"]["object"] is a stripe.StripeObject, not a plain dict — its
    # __getattr__ forwards ANY unknown attribute (including "get" itself) to
    # __getitem__, so obj.get(...) raises AttributeError instead of behaving
    # like dict.get(). Convert to a plain dict once here so every handler
    # below can use ordinary dict semantics.
    obj = event["data"]["object"].to_dict()

    if etype == "checkout.session.completed":
        if obj.get("mode") == "subscription":
            await _on_subscription_created(obj)

    elif etype in ("customer.subscription.updated", "customer.subscription.created"):
        await _on_subscription_updated(obj)

    elif etype == "customer.subscription.deleted":
        await _on_subscription_canceled(obj)

    elif etype == "invoice.payment_failed":
        await _on_payment_failed(obj)


def _period_end(sub: dict) -> Optional[int]:
    """Stripe moved current_period_end off the top-level Subscription object
    onto each subscription item (a subscription can now have items with
    independently-timed billing cycles) — the top-level field is always None
    under current API versions. Read it from the first item instead."""
    top = sub.get("current_period_end")
    if top is not None:
        return top
    items = sub.get("items", {}).get("data", [])
    return items[0].get("current_period_end") if items else None


async def _on_subscription_created(session: dict) -> None:
    user_id = session.get("client_reference_id")
    sub_id  = session.get("subscription")
    if not user_id or not sub_id:
        return
    stripe = _stripe()
    sub    = stripe.Subscription.retrieve(sub_id).to_dict()
    plan   = sub.get("metadata", {}).get("plan", "starter")
    await _upsert_sub(
        user_id=user_id,
        customer_id=session.get("customer"),
        sub_id=sub_id,
        plan=plan,
        status=sub["status"],
        period_end=_period_end(sub),
    )
    logger.info("stripe: subscription created user=%s plan=%s", user_id, plan)


async def _on_subscription_updated(sub: dict) -> None:
    plan = sub.get("metadata", {}).get("plan", "starter")
    await _upsert_sub_by_stripe_id(
        sub_id=sub["id"],
        customer_id=sub.get("customer"),
        plan=plan,
        status=sub["status"],
        period_end=_period_end(sub),
    )


async def _on_subscription_canceled(sub: dict) -> None:
    plan = sub.get("metadata", {}).get("plan", "starter")
    await _upsert_sub_by_stripe_id(
        sub_id=sub["id"],
        customer_id=sub.get("customer"),
        plan=plan,
        status="canceled",
        period_end=_period_end(sub),
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
    # current_period_end is DateTime (naive) — the `subscriptions` table stores
    # everything as TIMESTAMP WITHOUT TIME ZONE (see db/models.py's _now()),
    # and asyncpg rejects a tz-aware datetime bound to that column type.
    period_dt = datetime.fromtimestamp(period_end, tz=timezone.utc).replace(tzinfo=None) if period_end else None
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
        sub = result.scalar_one_or_none()
        if sub:
            sub.stripe_customer_id     = customer_id or sub.stripe_customer_id
            sub.stripe_subscription_id = sub_id
            sub.plan                   = plan
            sub.status                 = status
            sub.current_period_end     = period_dt
            # updated_at: no explicit assignment needed — Subscription.updated_at
            # has onupdate=_now (a naive datetime.utcnow(), matching the column
            # type); setting a tz-aware value here previously broke the UPDATE.
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
    # current_period_end is DateTime (naive) — the `subscriptions` table stores
    # everything as TIMESTAMP WITHOUT TIME ZONE (see db/models.py's _now()),
    # and asyncpg rejects a tz-aware datetime bound to that column type.
    period_dt = datetime.fromtimestamp(period_end, tz=timezone.utc).replace(tzinfo=None) if period_end else None
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
            # updated_at: handled by the model's onupdate=_now, see _upsert_sub.
            await db.commit()
