import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from routes.admin import router as admin_router
from routes.analysis import router as analysis_router
from routes.billing import router as billing_router
from routes.companies import router as companies_router
from routes.completions import router as completions_router
from routes.expert_review import router as expert_review_router
from routes.misc import router as misc_router
from routes.notifications import router as notifications_router
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
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        orphans = [c.name for c in client.list_collections() if c.name.startswith("job_")]
        for name in orphans:
            client.delete_collection(name)
        if orphans:
            logger.info("startup: deleted %d orphaned job collections: %s", len(orphans), orphans)
    except Exception as exc:
        logger.warning("startup: orphan cleanup failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_production_config()
    _cleanup_orphaned_chroma_collections()
    if settings.database_url:
        from db.database import init_db
        await init_db()
    await job_manager.start()
    yield
    await job_manager.stop()


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
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(analysis_router)
app.include_router(companies_router)
app.include_router(completions_router)
app.include_router(notifications_router)
app.include_router(expert_review_router)
app.include_router(billing_router)
app.include_router(admin_router)
app.include_router(misc_router)
