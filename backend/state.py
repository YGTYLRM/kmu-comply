"""
Shared application state — one instance per process.
Import from here to avoid circular deps between routes and main.
"""
from collections import defaultdict
from services.job_manager import JobManager
from config import settings

job_manager = JobManager(ttl_seconds=settings.job_ttl_seconds)

# Maps job_id → user_id for ownership checks (fast in-memory path).
# DB is the fallback for jobs that survived a restart.
job_owners: dict[str, str] = {}

# In-memory rate limit fallback — only used when DATABASE_URL is not set.
analyze_calls_fallback: dict[str, list[float]] = defaultdict(list)

# Contact endpoint rate limit (per IP, in-memory only — intentional).
contact_calls: dict[str, list[float]] = defaultdict(list)
