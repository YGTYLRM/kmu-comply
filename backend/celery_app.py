"""
Celery application instance.

Import this module to get the Celery app. Tasks are auto-discovered from tasks.py.

Start a worker:
    cd backend/
    celery -A celery_app worker --loglevel=info --concurrency=2

Or with the helper script:
    python celery_app.py worker
"""
from celery import Celery
from config import settings
from observability import init_sentry

# Separate process from uvicorn and worker.py — this is where the actual
# 6-step analysis pipeline runs when REDIS_URL is set (tasks.py), so it's
# the most important process to have this wired: the historical "gap
# analysis silently returned zero items" / "action plan silently empty"
# bugs both lived in code that runs here.
if settings.sentry_dsn:
    from sentry_sdk.integrations.celery import CeleryIntegration
    init_sentry([CeleryIntegration()])

_broker = settings.redis_url or "redis://localhost:6379/0"

celery_app = Celery(
    "complio",
    broker=_broker,
    backend=_broker,
    include=["tasks"],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timing
    timezone="UTC",
    enable_utc=True,

    # Reliability
    task_acks_late=True,           # ack only after the task completes (safe on crash)
    task_reject_on_worker_lost=True,  # re-queue if worker dies mid-task
    worker_prefetch_multiplier=1,  # one task at a time per worker (analysis is heavy)

    # Results
    task_track_started=True,
    result_expires=7200,           # 2h — reports are on disk, Celery result is ephemeral

    # Timeouts (analysis can take up to 5 min)
    task_soft_time_limit=360,      # sends SoftTimeLimitExceeded after 6 min
    task_time_limit=420,           # SIGKILL after 7 min
)

if __name__ == "__main__":
    # Allow: python celery_app.py worker --loglevel=info
    celery_app.start()
