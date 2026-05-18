"""
Shared application state — one instance per process.
Import from here to avoid circular deps between routes and main.
"""
from collections import OrderedDict, defaultdict
from services.job_manager import JobManager
from config import settings

job_manager = JobManager(ttl_seconds=settings.job_ttl_seconds)

_JOB_OWNERS_MAX = 10_000


class _BoundedOwnerDict(OrderedDict):
    """LRU-bounded dict for job_id → user_id mappings."""
    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > _JOB_OWNERS_MAX:
            self.popitem(last=False)


job_owners: dict[str, str] = _BoundedOwnerDict()

# In-memory rate limit fallback �� only used when DATABASE_URL is not set.
analyze_calls_fallback: dict[str, list[float]] = defaultdict(list)

# Contact endpoint rate limit (per IP, in-memory only — intentional).
contact_calls: dict[str, list[float]] = defaultdict(list)
