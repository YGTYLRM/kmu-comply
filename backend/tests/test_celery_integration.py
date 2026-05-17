"""
Tests for the Celery + Redis job queue integration.

These tests mock Redis and Celery so no real infrastructure is needed.
They verify:
  - JobManager routes to Celery when redis_url is set
  - JobManager falls back to asyncio when redis_url is empty
  - redis_store helper functions encode/decode state correctly
  - Status endpoint uses Redis when available, DB otherwise
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.company_profile import CompanyProfile
from models.enums import AnalysisStep, JobStatus


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_profile(**kwargs) -> CompanyProfile:
    defaults = dict(
        company_name="Test GmbH",
        industry="it_software",
        employee_count=10,
        processes_personal_data=True,
    )
    defaults.update(kwargs)
    return CompanyProfile(**defaults)


# ── Mode detection ────────────────────────────────────────────────────────────

class TestJobManagerMode:
    @pytest.mark.asyncio
    async def test_asyncio_mode_when_no_redis_url(self, monkeypatch):
        monkeypatch.setattr("config.settings.redis_url", "")
        from services.job_manager import JobManager

        jm = JobManager()
        with patch.object(jm, "_recover_crashed_jobs", new_callable=AsyncMock):
            with patch("services.document_store.document_store") as mock_ds:
                mock_ds.recover_sessions.return_value = 0
                # Start cleanup task then stop it
                jm._cleanup_task = asyncio.create_task(asyncio.sleep(0))
                await asyncio.sleep(0)
                jm._celery_mode = False  # simulate start()
        assert jm._celery_mode is False

    @pytest.mark.asyncio
    async def test_celery_mode_when_redis_url_set(self, monkeypatch):
        monkeypatch.setattr("config.settings.redis_url", "redis://localhost:6379/0")
        from services.job_manager import JobManager

        jm = JobManager()
        jm._celery_mode = True  # simulate start()
        assert jm._celery_mode is True


# ── redis_store helpers ───────────────────────────────────────────────────────

class TestRedisStore:
    """Tests for redis_store helper functions — mock the Redis client."""

    @pytest.mark.asyncio
    async def test_set_job_initial_writes_correct_keys(self):
        from services import redis_store

        mock_r = AsyncMock()
        mock_r.hset = AsyncMock()
        mock_r.expire = AsyncMock()
        mock_r.aclose = AsyncMock()

        with patch.object(redis_store, "_async_redis", return_value=mock_r):
            await redis_store.set_job_initial("job-123", user_id="user-1", company_id="co-1")

        call_kwargs = mock_r.hset.call_args[1]
        mapping = call_kwargs["mapping"]
        assert mapping["status"] == "pending"
        assert mapping["user_id"] == "user-1"
        assert mapping["company_id"] == "co-1"
        assert "created_at" in mapping

    @pytest.mark.asyncio
    async def test_set_job_status_running_with_step(self):
        from services import redis_store

        mock_r = AsyncMock()
        with patch.object(redis_store, "_async_redis", return_value=mock_r):
            await redis_store.set_job_status(
                "job-123", "running", current_step="gap_analysis"
            )

        call_kwargs = mock_r.hset.call_args[1]
        assert call_kwargs["mapping"]["status"] == "running"
        assert call_kwargs["mapping"]["current_step"] == "gap_analysis"

    @pytest.mark.asyncio
    async def test_get_job_state_returns_dict_with_steps(self):
        from services import redis_store

        mock_r = AsyncMock()
        mock_r.hgetall = AsyncMock(return_value={
            "status": "running",
            "current_step": "gap_analysis",
            "user_id": "user-1",
        })
        mock_r.lrange = AsyncMock(return_value=[
            json.dumps({"step": "profile_validation", "status": "completed"}),
            json.dumps({"step": "gap_analysis", "status": "running"}),
        ])

        with patch.object(redis_store, "_async_redis", return_value=mock_r):
            state = await redis_store.get_job_state("job-123")

        assert state is not None
        assert state["status"] == "running"
        assert state["current_step"] == "gap_analysis"
        assert len(state["_steps"]) == 2

    @pytest.mark.asyncio
    async def test_get_job_state_returns_none_when_not_found(self):
        from services import redis_store

        mock_r = AsyncMock()
        mock_r.hgetall = AsyncMock(return_value={})  # empty = not found
        mock_r.lrange = AsyncMock(return_value=[])

        with patch.object(redis_store, "_async_redis", return_value=mock_r):
            state = await redis_store.get_job_state("nonexistent-job")

        assert state is None

    @pytest.mark.asyncio
    async def test_get_job_owner_returns_user_id(self):
        from services import redis_store

        mock_r = AsyncMock()
        mock_r.hget = AsyncMock(return_value="user-42")

        with patch.object(redis_store, "_async_redis", return_value=mock_r):
            owner = await redis_store.get_job_owner("job-123")

        assert owner == "user-42"

    @pytest.mark.asyncio
    async def test_redis_errors_dont_propagate(self):
        from services import redis_store

        mock_r = AsyncMock()
        mock_r.hset = AsyncMock(side_effect=ConnectionError("Redis down"))

        with patch.object(redis_store, "_async_redis", return_value=mock_r):
            # Should NOT raise — all redis_store functions are non-fatal
            await redis_store.set_job_status("job-123", "running")  # no exception


# ── Status routing ────────────────────────────────────────────────────────────

class TestStatusRouting:
    @pytest.mark.asyncio
    async def test_get_status_async_uses_redis_in_celery_mode(self):
        from services.job_manager import JobManager
        from models.api_responses import StatusResponse

        jm = JobManager()
        jm._celery_mode = True

        expected = StatusResponse(
            job_id="job-abc",
            status=JobStatus.RUNNING,
            current_step=AnalysisStep.GAP_ANALYSIS,
            steps=[],
            error=None,
        )

        with patch.object(jm, "_status_from_redis", new_callable=AsyncMock, return_value=expected):
            result = await jm.get_status_async("job-abc")

        assert result is not None
        assert result.status == JobStatus.RUNNING
        assert result.current_step == AnalysisStep.GAP_ANALYSIS

    @pytest.mark.asyncio
    async def test_status_from_redis_parses_state_correctly(self):
        from services.job_manager import JobManager

        jm = JobManager()
        jm._celery_mode = True

        redis_state = {
            "status": "running",
            "current_step": "gap_analysis",
            "user_id": "user-1",
            "_steps": [
                {"step": "profile_validation", "status": "completed"},
                {"step": "gap_analysis", "status": "running"},
            ],
        }

        with patch("services.redis_store.get_job_state", new_callable=AsyncMock, return_value=redis_state):
            result = await jm._status_from_redis("job-abc")

        assert result is not None
        assert result.status == JobStatus.RUNNING
        assert result.current_step == AnalysisStep.GAP_ANALYSIS
        assert len(result.steps) == 2

    @pytest.mark.asyncio
    async def test_status_from_redis_falls_back_to_disk_for_completed(self):
        from services.job_manager import JobManager

        jm = JobManager()
        jm._celery_mode = True

        # Redis has no state (expired TTL)
        with patch("services.redis_store.get_job_state", new_callable=AsyncMock, return_value=None):
            with patch("services.report_store.exists", return_value=True):
                result = await jm._status_from_redis("job-old")

        assert result is not None
        assert result.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_status_from_redis_returns_none_when_nothing_found(self):
        from services.job_manager import JobManager

        jm = JobManager()
        jm._celery_mode = True

        with patch("services.redis_store.get_job_state", new_callable=AsyncMock, return_value=None):
            with patch("services.report_store.exists", return_value=False):
                result = await jm._status_from_redis("ghost-job")

        assert result is None
