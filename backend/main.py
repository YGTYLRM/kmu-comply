import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from config import settings
from routes.admin import router as admin_router
from routes.analysis import router as analysis_router
from routes.billing import router as billing_router
from routes.companies import router as companies_router
from routes.completions import router as completions_router
from routes.expert_review import router as expert_review_router
from routes.misc import router as misc_router
from routes.notifications import router as notifications_router
from routes.scanning import router as scanning_router
from state import job_manager

if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[FastApiIntegration(), AsyncioIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)


def _check_production_config() -> None:
    if settings.environment != "production":
        return
    errors = []
    if not settings.chroma_server_url:
        errors.append(
            "CHROMA_SERVER_URL must be set in production — ChromaDB embedded mode "
            "is single-writer and will corrupt under concurrent access."
        )
    if not settings.document_encryption_key:
        errors.append(
            "DOCUMENT_ENCRYPTION_KEY must be set in production — without it, "
            "uploaded documents use an ephemeral key lost on restart."
        )
    if not settings.admin_api_key:
        errors.append(
            "ADMIN_API_KEY must be set in production — without it, the regulation "
            "update approval API is inaccessible."
        )
    if not settings.database_url:
        errors.append(
            "DATABASE_URL must be set in production — rate limiting, report "
            "persistence, and job ownership require PostgreSQL."
        )
    if errors:
        print("\n[STARTUP ERROR] Production config validation failed:\n", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}\n", file=sys.stderr)
        sys.exit(1)


def _cleanup_orphaned_chroma_collections() -> None:
    try:
        import chromadb
        from rag.ingest import CHROMA_DIR
        from state import job_manager
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        candidates = [c.name for c in client.list_collections() if c.name.startswith("job_")]
        orphans = []
        for name in candidates:
            job_id = name[len("job_"):]
            # Skip collections whose job is still active in memory
            if job_id in job_manager._jobs:
                continue
            orphans.append(name)
        for name in orphans:
            client.delete_collection(name)
        if orphans:
            logger.info("startup: deleted %d orphaned job collections: %s", len(orphans), orphans)
    except Exception as exc:
        logger.warning("startup: orphan cleanup failed: %s", exc)


async def _document_purge_loop():
    """Periodically purge expired document sessions (runs every hour)."""
    from services.document_store import document_store
    while True:
        await asyncio.sleep(3600)
        try:
            purged = document_store.purge_expired(settings.document_ttl_seconds)
            if purged:
                logger.info("document purge: cleaned %d expired session(s)", purged)
        except Exception as exc:
            logger.warning("document purge failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_production_config()
    _cleanup_orphaned_chroma_collections()
    from services.document_store import document_store
    document_store.recover_sessions()
    await job_manager.start()
    purge_task = asyncio.create_task(_document_purge_loop())
    yield
    purge_task.cancel()
    await job_manager.stop()
    from services.pdf_generator import close_browser
    close_browser()


app = FastAPI(
    title="Complio API",
    description="Autonomous regulatory compliance analysis for German SMEs",
    version="0.1.0",
    lifespan=lifespan,
)

_allowed_origins = [
    o.strip()
    for o in (settings.allowed_origins or "http://localhost:3000,http://localhost:3001").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Key", "Stripe-Signature"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response


class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        import asyncio
        try:
            return await asyncio.wait_for(call_next(request), timeout=60.0)
        except asyncio.TimeoutError:
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Request timed out"}, status_code=504)


app.add_middleware(TimeoutMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
# Extract real client IP from X-Forwarded-For when behind a reverse proxy.
# In production, restrict to your actual proxy IPs via PROXY_TRUSTED_HOSTS env var.
_trusted = [h.strip() for h in (settings.proxy_trusted_hosts or "*").split(",") if h.strip()]
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=_trusted if _trusted != ["*"] else "*")

app.include_router(analysis_router)
app.include_router(companies_router)
app.include_router(completions_router)
app.include_router(notifications_router)
app.include_router(expert_review_router)
app.include_router(billing_router)
app.include_router(admin_router)
app.include_router(misc_router)
app.include_router(scanning_router)
