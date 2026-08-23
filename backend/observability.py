"""
Centralized Sentry init — call once per process (web server, scheduler
worker, Celery worker). Each process needs its own init() call since Sentry
hooks into thread-local/process state; a single call in main.py does not
cover worker.py or celery_app.py, which run as separate processes.

event_level=WARNING (Sentry's default is ERROR) because this project's worst
bugs historically were silent degradations logged at logger.warning(), not
exceptions — a corrupted source file served as real legal guidance for
months, gap analysis and action-plan generation both silently returned zero
items, score breakdown silently dropped regulations. All of those logged a
warning and kept going; none of them raised. A WARNING-level Sentry event is
what would have surfaced them without a human doing a manual walkthrough.
If warning volume gets noisy once there's real traffic, dial back to
logging.ERROR — that's a one-line change here, not a redesign.
"""
import logging

from config import settings

logger = logging.getLogger(__name__)


def init_sentry(process_integrations: list | None = None) -> bool:
    """Initialize Sentry for the current process. No-ops if SENTRY_DSN is
    unset. Returns True if Sentry was actually initialized."""
    if not settings.sentry_dsn:
        return False

    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[
            LoggingIntegration(level=logging.INFO, event_level=logging.WARNING),
            *(process_integrations or []),
        ],
        traces_sample_rate=0.1,
        # Compliance data (company profiles, uploaded document content) must
        # never reach Sentry — matches the existing disclosure in
        # datenschutz/page.tsx describing Sentry as error-monitoring only,
        # no personal user content.
        send_default_pii=False,
    )
    logger.info("sentry initialized (environment=%s)", settings.environment)
    return True
