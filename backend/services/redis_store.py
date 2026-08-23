"""
Redis-backed job state store.

Used when REDIS_URL is configured (Celery mode). Provides fast in-process
job status without hitting the database on every poll request.

Key schema (all keys expire after JOB_TTL):
  job:{job_id}        HASH  status, current_step, error, user_id, created_at
  job:{job_id}:steps  LIST  JSON-encoded StepProgress entries (append-only)

All functions gracefully return None/empty on Redis errors so the caller
can fall back to the database.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

JOB_TTL = 7200  # 2 hours — reports live on disk, Redis is ephemeral


def _url() -> str:
    from config import settings
    return settings.redis_url


# ── Async helpers (FastAPI context) ───────────────────────────────────────────

_pool = None


def _async_redis():
    """Return an async Redis client backed by a shared connection pool."""
    global _pool
    from redis.asyncio import ConnectionPool, Redis
    if _pool is None:
        _pool = ConnectionPool.from_url(_url(), decode_responses=True, max_connections=20)
    return Redis(connection_pool=_pool)


async def set_job_initial(
    job_id: str,
    user_id: Optional[str],
    company_id: Optional[str] = None,
) -> None:
    r = _async_redis()
    try:
        mapping: dict[str, str] = {
            "status": "pending",
            "created_at": str(time.time()),
        }
        if user_id:
            mapping["user_id"] = user_id
        if company_id:
            mapping["company_id"] = company_id
        await r.hset(f"job:{job_id}", mapping=mapping)
        await r.expire(f"job:{job_id}", JOB_TTL)
    except Exception as exc:
        logger.warning("redis_store: set_job_initial failed: %s", exc)
    finally:
        await r.close()


async def set_job_status(
    job_id: str,
    status: str,
    current_step: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    r = _async_redis()
    try:
        mapping: dict[str, str] = {"status": status}
        if current_step is not None:
            mapping["current_step"] = current_step
        if error is not None:
            mapping["error"] = error
        await r.hset(f"job:{job_id}", mapping=mapping)
        await r.expire(f"job:{job_id}", JOB_TTL)
    except Exception as exc:
        logger.warning("redis_store: set_job_status failed: %s", exc)
    finally:
        await r.close()


async def append_step(job_id: str, step_name: str, step_status: str) -> None:
    r = _async_redis()
    try:
        entry = json.dumps({"step": step_name, "status": step_status})
        key = f"job:{job_id}:steps"
        await r.rpush(key, entry)
        await r.expire(key, JOB_TTL)
    except Exception as exc:
        logger.warning("redis_store: append_step failed: %s", exc)
    finally:
        await r.close()


async def get_job_state(job_id: str) -> Optional[dict]:
    r = _async_redis()
    try:
        data = await r.hgetall(f"job:{job_id}")
        if not data:
            return None
        steps_raw = await r.lrange(f"job:{job_id}:steps", 0, -1)
        data["_steps"] = [json.loads(s) for s in steps_raw]
        return data
    except Exception as exc:
        logger.warning("redis_store: get_job_state failed: %s", exc)
        return None
    finally:
        await r.close()


async def get_job_owner(job_id: str) -> Optional[str]:
    r = _async_redis()
    try:
        return await r.hget(f"job:{job_id}", "user_id")
    except Exception as exc:
        logger.warning("redis_store: get_job_owner failed: %s", exc)
        return None
    finally:
        await r.close()


async def set_job_owner(job_id: str, user_id: str) -> None:
    r = _async_redis()
    try:
        await r.hset(f"job:{job_id}", "user_id", user_id)
    except Exception as exc:
        logger.warning("redis_store: set_job_owner failed: %s", exc)
    finally:
        await r.close()


# ── Sync helpers (Celery task context — called inside asyncio.run()) ──────────

def _sync_redis():
    """Return a sync Redis client for use inside Celery tasks (non-async context)."""
    import redis
    return redis.Redis.from_url(_url(), decode_responses=True)


def sync_set_job_status(
    job_id: str,
    status: str,
    current_step: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    try:
        r = _sync_redis()
        mapping: dict[str, str] = {"status": status}
        if current_step is not None:
            mapping["current_step"] = current_step
        if error is not None:
            mapping["error"] = error
        r.hset(f"job:{job_id}", mapping=mapping)
        r.expire(f"job:{job_id}", JOB_TTL)
    except Exception as exc:
        logger.warning("redis_store: sync_set_job_status failed: %s", exc)


def sync_append_step(job_id: str, step_name: str, step_status: str = "running") -> None:
    try:
        r = _sync_redis()
        entry = json.dumps({"step": step_name, "status": step_status})
        key = f"job:{job_id}:steps"
        r.rpush(key, entry)
        r.expire(key, JOB_TTL)
    except Exception as exc:
        logger.warning("redis_store: sync_append_step failed: %s", exc)


def sync_set_all_steps_complete(job_id: str) -> None:
    try:
        r = _sync_redis()
        steps_raw = r.lrange(f"job:{job_id}:steps", 0, -1)
        r.delete(f"job:{job_id}:steps")
        for s_raw in steps_raw:
            entry = json.loads(s_raw)
            entry["status"] = "completed"
            r.rpush(f"job:{job_id}:steps", json.dumps(entry))
        r.expire(f"job:{job_id}:steps", JOB_TTL)
    except Exception as exc:
        logger.warning("redis_store: sync_set_all_steps_complete failed: %s", exc)
