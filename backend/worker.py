"""
Complio monitoring worker (APScheduler).

Runs the APScheduler jobs in a separate process from the FastAPI web server so
the scheduler survives web restarts and doesn't fire duplicate jobs behind a
load balancer.

Start:
    cd backend/
    python worker.py

In production, run alongside uvicorn as a separate process or container.

── With Celery (REDIS_URL set) ──────────────────────────────────────────────
Also start a Celery worker to process analysis jobs:

    celery -A celery_app worker --loglevel=info --concurrency=2

Or via the helper:
    python celery_app.py worker --loglevel=info --concurrency=2

Process map:
  1. uvicorn main:app      — FastAPI web server (submits jobs to Celery)
  2. python worker.py      — APScheduler (regulation checks, re-assessments)
  3. celery -A celery_app  — Analysis workers (runs the 6-step pipeline)

── Without Celery (REDIS_URL not set) ───────────────────────────────────────
Analysis jobs run as asyncio tasks inside the uvicorn process (single-server
dev mode). Only process 1 and 2 are needed.

Cron jobs (UTC):
    02:00 Sun — Fetch regulation updates from official sources (staged for review)
    03:00 — Regulation change detection + re-ingestion + section diff
    04:00 — Scheduled company re-assessments (7d Professional, 30d Starter)
    05:00 Mon — Document ageing alerts
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("worker")


async def main() -> None:
    from config import settings
    from services.scheduler import start_scheduler, stop_scheduler

    # Initialise DB connection (same as web server startup)
    if settings.database_url:
        from db.database import init_db
        await init_db()
        logger.info("worker: database initialised")

    start_scheduler()
    logger.info("worker: scheduler running — regulation check 03:00 UTC, reassessments 04:00 UTC")

    stop_event = asyncio.Event()

    def _handle_signal(sig_name: str) -> None:
        logger.info("worker: received %s, shutting down", sig_name)
        stop_event.set()

    loop = asyncio.get_running_loop()

    # SIGTERM (Linux/production) + SIGINT (Ctrl-C / development)
    try:
        loop.add_signal_handler(signal.SIGTERM, lambda: _handle_signal("SIGTERM"))
    except (NotImplementedError, OSError):
        # Windows does not support SIGTERM via add_signal_handler
        pass
    try:
        loop.add_signal_handler(signal.SIGINT, lambda: _handle_signal("SIGINT"))
    except (NotImplementedError, OSError):
        pass

    await stop_event.wait()
    stop_scheduler()
    logger.info("worker: stopped cleanly")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("worker: interrupted")
