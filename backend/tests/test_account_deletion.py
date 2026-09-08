"""
Live integration test for DELETE /api/account (GDPR Art. 17).

Found via a manual self-audit (see SESSION_LOG.md Session 31c) that this
endpoint silently left most of a user's data behind — including the Supabase
auth account itself — despite the privacy policy explicitly promising full
self-service deletion. That bug had zero test coverage and shipped
undetected. This test exists so a future regression here needs one command
to catch, not another live manual audit.

Requires real Supabase + Postgres credentials (creates and deletes a real,
clearly-marked throwaway auth user against the configured project) — skipped
automatically when those aren't configured.

Run manually:
    cd backend
    python -m pytest tests/test_account_deletion.py -m integration -v
"""
import uuid

import pytest

from config import settings

pytestmark = pytest.mark.integration

_SKIP_REASON = "DATABASE_URL / SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not configured"
requires_live_supabase = pytest.mark.skipif(
    not (settings.database_url and settings.supabase_url and settings.supabase_service_role_key),
    reason=_SKIP_REASON,
)


@requires_live_supabase
async def test_delete_account_removes_everything():
    from db.database import AsyncSessionLocal
    from db.models import Profile, ActionCompletion, ExpertReviewRequest, RateLimitEvent, JobRecord
    from routes.companies import delete_account
    from services.auth_service import get_supabase
    from sqlalchemy import select

    sb = get_supabase()
    test_email = f"complio-test-account-deletion-{uuid.uuid4().hex[:8]}@example.com"
    created = sb.auth.admin.create_user({
        "email": test_email,
        "password": uuid.uuid4().hex,
        "email_confirm": True,
    })
    user_id = created.user.id

    try:
        async with AsyncSessionLocal() as db:
            db.add(Profile(id=user_id, name="Test Account Deletion", email=test_email))
            db.add(ActionCompletion(
                user_id=user_id, job_id="test-job",
                regulation="gdpr_dsgvo", article_number="Art. 30",
            ))
            db.add(ExpertReviewRequest(
                user_id=user_id, job_id="test-job",
                company_name="Test GmbH", user_email=test_email,
            ))
            db.add(RateLimitEvent(user_id=user_id, endpoint="/api/analyze"))
            db.add(JobRecord(id=f"test-job-{uuid.uuid4().hex[:8]}", user_id=user_id, status="completed"))
            await db.commit()

        result = await delete_account(current_user={"id": user_id, "email": test_email})
        assert result["deleted"] is True

        async with AsyncSessionLocal() as db:
            for model, id_field in (
                (Profile, Profile.id),
                (ActionCompletion, ActionCompletion.user_id),
                (ExpertReviewRequest, ExpertReviewRequest.user_id),
                (RateLimitEvent, RateLimitEvent.user_id),
                (JobRecord, JobRecord.user_id),
            ):
                rows = (await db.execute(select(model).where(id_field == user_id))).scalars().all()
                assert rows == [], f"{model.__tablename__} still has rows for a deleted user"

        with pytest.raises(Exception):
            sb.auth.admin.get_user_by_id(user_id)

    finally:
        # Best-effort cleanup in case an assertion failed before delete_account
        # ran (or before it finished) — never leave a real test user behind.
        try:
            sb.auth.admin.delete_user(user_id)
        except Exception:
            pass
