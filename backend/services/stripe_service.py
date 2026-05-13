"""
Stripe Checkout integration for Complio.
Uses inline price_data so no pre-created products needed in the dashboard.
"""
from __future__ import annotations
import uuid, time
from typing import Optional
import stripe
from config import settings

PLANS = {
    "starter": {
        "name": "Complio Starter Report",
        "amount": 7900,       # EUR 79.00 in cents
        "currency": "eur",
        "mode": "payment",
        "description": "Single compliance screening — all regulations, full gap analysis, PDF report.",
    },
    "professional": {
        "name": "Complio Professional",
        "amount": 14900,      # EUR 149.00 in cents
        "currency": "eur",
        "mode": "subscription",
        "description": "Unlimited monthly screenings with priority processing.",
    },
}

# In-memory store: session_id -> {plan, paid_at, token, token_used}
_sessions: dict[str, dict] = {}
# token -> session_id (reverse lookup)
_tokens: dict[str, str] = {}

TOKEN_TTL = 60 * 60 * 24 * 30  # 30 days


def _stripe():
    stripe.api_key = settings.stripe_secret_key
    return stripe


def create_checkout_session(plan: str, success_url: str, cancel_url: str) -> str:
    if plan not in PLANS:
        raise ValueError(f"Unknown plan: {plan}")
    p = PLANS[plan]
    s = _stripe()

    price_data = {
        "currency": p["currency"],
        "product_data": {
            "name": p["name"],
            "description": p["description"],
        },
        "unit_amount": p["amount"],
    }
    if p["mode"] == "subscription":
        price_data["recurring"] = {"interval": "month"}

    session = s.checkout.Session.create(
        mode=p["mode"],
        line_items=[{"price_data": price_data, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        billing_address_collection="auto",
    )
    return session.url


def handle_webhook(payload: bytes, sig_header: str) -> Optional[str]:
    """Verify webhook signature, mark session paid, return access token."""
    s = _stripe()
    try:
        event = s.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except stripe.SignatureVerificationError:
        return None

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        token = _mint_token(session["id"])
        return token
    return None


def _mint_token(session_id: str) -> str:
    token = str(uuid.uuid4())
    _sessions[session_id] = {
        "paid_at": time.time(),
        "token": token,
        "token_used": False,
    }
    _tokens[token] = session_id
    return token


def verify_session(session_id: str) -> Optional[str]:
    """Called from success page — confirms payment via Stripe API and mints token."""
    s = _stripe()
    try:
        session = s.checkout.Session.retrieve(session_id)
    except Exception:
        return None

    if session.get("payment_status") not in ("paid", "no_payment_required"):
        # subscription sessions use "no_payment_required" initially; check status
        if session.get("status") != "complete":
            return None

    if session_id in _sessions:
        return _sessions[session_id]["token"]

    return _mint_token(session_id)


def validate_token(token: str) -> bool:
    """Check that a token is valid and not expired."""
    session_id = _tokens.get(token)
    if not session_id:
        return False
    rec = _sessions.get(session_id, {})
    if time.time() - rec.get("paid_at", 0) > TOKEN_TTL:
        return False
    return True
