"""
Async job manager — dual-mode: Celery (Redis) or in-process asyncio.

Mode is selected at startup based on settings.redis_url:
  - REDIS_URL set   → Celery mode: jobs dispatched to a Celery worker via Redis broker;
                       status tracked in Redis; reports persisted to disk + DB as before.
  - REDIS_URL empty → asyncio mode: jobs run as asyncio tasks inside the web process
                       (original behaviour, safe for single-server dev deployments).

The public API (create_job, get_status, get_report) is identical in both modes.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from models.api_responses import StatusResponse, StepProgress
from models.company_profile import CompanyProfile
from models.compliance_report import ComplianceReport
from models.enums import AnalysisStep, JobStatus

logger = logging.getLogger(__name__)


class _Job:
    def __init__(
        self,
        job_id: str,
        profile: CompanyProfile,
        doc_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> None:
        self.job_id       = job_id
        self.profile      = profile
        self.doc_session_id = doc_session_id
        self.user_id      = user_id
        self.company_id   = company_id
        self.status       = JobStatus.PENDING
        self.current_step: Optional[AnalysisStep] = None
        self.steps: list[StepProgress] = []
        self.report: Optional[ComplianceReport] = None
        self.error: Optional[str] = None
        self.created_at   = datetime.now(timezone.utc)

    def to_status_response(self) -> StatusResponse:
        return StatusResponse(
            job_id=self.job_id,
            status=self.status,
            current_step=self.current_step,
            steps=self.steps,
            error=self.error,
        )


async def _db_upsert_job(job_id: str, status: str, current_step: Optional[str] = None, error: Optional[str] = None, user_id: Optional[str] = None, company_id: Optional[str] = None) -> None:
    """Write job state to the DB. Non-fatal — logs on failure."""
    from config import settings
    if not settings.database_url:
        return
    try:
        from db.database import AsyncSessionLocal
        from db.models import JobRecord
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            row = (await db.execute(select(JobRecord).where(JobRecord.id == job_id))).scalar_one_or_none()
            if row:
                row.status       = status
                row.current_step = current_step
                row.error        = error
            else:
                db.add(JobRecord(
                    id=job_id, user_id=user_id, company_id=company_id,
                    status=status, current_step=current_step, error=error,
                ))
            await db.commit()
    except Exception as exc:
        logger.warning("job_manager: DB state write failed for %s: %s", job_id, exc)


async def _db_get_status(job_id: str) -> Optional[StatusResponse]:
    """Look up job status from the DB when not in memory."""
    from config import settings
    if not settings.database_url:
        return None
    try:
        from db.database import AsyncSessionLocal
        from db.models import JobRecord
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            row = (await db.execute(select(JobRecord).where(JobRecord.id == job_id))).scalar_one_or_none()
            if not row:
                return None
            return StatusResponse(
                job_id=job_id,
                status=JobStatus(row.status),
                current_step=AnalysisStep(row.current_step) if row.current_step else None,
                steps=[],
                error=row.error,
            )
    except Exception as exc:
        logger.warning("job_manager: DB status lookup failed for %s: %s", job_id, exc)
        return None


class JobManager:
    """
    Dual-mode job manager: Celery (Redis) when REDIS_URL is set, asyncio otherwise.

    Both modes expose the same interface so routes/dependencies don't change.
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._jobs: dict[str, _Job] = {}   # asyncio mode only
        self._ttl  = ttl_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._celery_mode: bool = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        from config import settings
        self._celery_mode = bool(settings.redis_url)
        if self._celery_mode:
            logger.info("job_manager: Celery mode (REDIS_URL=%s...)", settings.redis_url[:20])
            # In Celery mode, crashed-job recovery is handled per task (task_acks_late)
        else:
            logger.info("job_manager: asyncio mode (no REDIS_URL set)")
            await self._recover_crashed_jobs()

        from services.document_store import document_store
        document_store.recover_sessions()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _recover_crashed_jobs(self) -> None:
        """(asyncio mode only) Mark any RUNNING jobs from a crashed process as FAILED."""
        from config import settings
        if not settings.database_url:
            return
        try:
            from db.database import AsyncSessionLocal
            from db.models import JobRecord
            from sqlalchemy import select
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(JobRecord).where(JobRecord.status == "running")
                )
                crashed = result.scalars().all()
                for row in crashed:
                    row.status = "failed"
                    row.error  = "Job was interrupted by a server restart. Please re-run the screening."
                if crashed:
                    await db.commit()
                    logger.warning(
                        "job_manager: marked %d crashed job(s) as FAILED on startup", len(crashed)
                    )
        except Exception as exc:
            logger.warning("job_manager: crash recovery failed: %s", exc)

    # ── Job creation ──────────────────────────────────────────────────────────

    async def create_job(
        self,
        profile: CompanyProfile,
        doc_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> str:
        job_id = str(uuid.uuid4())

        from services.report_store import save_profile
        save_profile(job_id, profile.model_dump())
        await _db_upsert_job(job_id, "pending", user_id=user_id, company_id=company_id)

        if self._celery_mode:
            await self._create_celery_job(job_id, profile, doc_session_id, user_id, company_id)
        else:
            await self._create_asyncio_job(job_id, profile, doc_session_id, user_id, company_id)

        return job_id

    async def _create_celery_job(
        self,
        job_id: str,
        profile: CompanyProfile,
        doc_session_id: Optional[str],
        user_id: Optional[str],
        company_id: Optional[str],
    ) -> None:
        from services.redis_store import set_job_initial, set_job_owner
        await set_job_initial(job_id, user_id=user_id, company_id=company_id)

        # job_owners fast path — also written to Redis
        if user_id:
            from state import job_owners
            job_owners[job_id] = user_id
            await set_job_owner(job_id, user_id)

        from tasks import run_analysis_celery
        run_analysis_celery.delay(
            job_id,
            profile.model_dump(),
            doc_session_id,
            user_id,
            company_id,
        )
        logger.info("job_manager: dispatched %s to Celery", job_id)

    async def _create_asyncio_job(
        self,
        job_id: str,
        profile: CompanyProfile,
        doc_session_id: Optional[str],
        user_id: Optional[str],
        company_id: Optional[str],
    ) -> None:
        job = _Job(
            job_id=job_id, profile=profile, doc_session_id=doc_session_id,
            user_id=user_id, company_id=company_id,
        )
        self._jobs[job_id] = job
        asyncio.create_task(self._run_pipeline(job))

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self, job_id: str) -> Optional[StatusResponse]:
        """Sync status check — asyncio mode only (in-memory dict)."""
        job = self._jobs.get(job_id)
        if job:
            return job.to_status_response()
        from services.report_store import exists
        if exists(job_id):
            return StatusResponse(
                job_id=job_id, status=JobStatus.COMPLETED,
                current_step=None, steps=[], error=None,
            )
        return None

    async def get_status_async(self, job_id: str) -> Optional[StatusResponse]:
        """Async status — checks Redis (Celery mode) or in-memory (asyncio mode), then DB."""
        if self._celery_mode:
            return await self._status_from_redis(job_id) or await _db_get_status(job_id)
        result = self.get_status(job_id)
        if result:
            return result
        return await _db_get_status(job_id)

    async def _status_from_redis(self, job_id: str) -> Optional[StatusResponse]:
        try:
            from services.redis_store import get_job_state
            state = await get_job_state(job_id)
            if not state:
                # Not in Redis — check disk (fast path for completed jobs)
                from services.report_store import exists
                if exists(job_id):
                    return StatusResponse(
                        job_id=job_id, status=JobStatus.COMPLETED,
                        current_step=None, steps=[], error=None,
                    )
                return None

            status_str = state.get("status", "pending")
            try:
                status = JobStatus(status_str)
            except ValueError:
                status = JobStatus.PENDING

            step_str = state.get("current_step")
            try:
                current_step = AnalysisStep(step_str) if step_str else None
            except ValueError:
                current_step = None

            raw_steps = state.get("_steps", [])
            steps = []
            for s in raw_steps:
                try:
                    steps.append(StepProgress(
                        step=AnalysisStep(s["step"]),
                        status=JobStatus(s.get("status", "running")),
                    ))
                except (ValueError, KeyError):
                    pass

            return StatusResponse(
                job_id=job_id,
                status=status,
                current_step=current_step,
                steps=steps,
                error=state.get("error"),
            )
        except Exception as exc:
            logger.warning("job_manager: redis status check failed for %s: %s", job_id, exc)
            return None

    # ── Report ────────────────────────────────────────────────────────────────

    async def get_report(self, job_id: str) -> Optional[ComplianceReport]:
        job = self._jobs.get(job_id)
        if job and job.status in (JobStatus.COMPLETED, JobStatus.PARTIAL):
            return job.report
        from services.report_store import load_async
        return await load_async(job_id)

    async def _run_pipeline(self, job: _Job) -> None:
        from agent.compliance_agent import run_analysis

        job.status = JobStatus.RUNNING
        await _db_upsert_job(job.job_id, "running", user_id=job.user_id, company_id=job.company_id)

        def on_step(step: AnalysisStep) -> None:
            job.current_step = step
            for sp in job.steps:
                if sp.step == step:
                    sp.status = JobStatus.RUNNING
                    return
            job.steps.append(StepProgress(step=step, status=JobStatus.RUNNING))
            asyncio.create_task(
                _db_upsert_job(job.job_id, "running", current_step=step.value, user_id=job.user_id)
            )

        try:
            report = await run_analysis(
                job.job_id, job.profile,
                on_step=on_step,
                doc_session_id=job.doc_session_id,
            )

            for sp in job.steps:
                sp.status = JobStatus.COMPLETED

            job.report        = report
            job.current_step  = None
            job.status        = JobStatus.PARTIAL if report.requires_manual_review else JobStatus.COMPLETED

            from services.report_store import save as save_report
            save_report(report, user_id=job.user_id)

            await _db_upsert_job(job.job_id, job.status.value, user_id=job.user_id, company_id=job.company_id)

            if job.company_id:
                try:
                    from services.db_service import save_report_to_db
                    await save_report_to_db(job.company_id, report, triggered_by="manual")
                except Exception as exc:
                    logger.warning("job_manager: report DB save failed for %s: %s", job.job_id, exc)

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error  = str(exc)
            await _db_upsert_job(job.job_id, "failed", error=str(exc), user_id=job.user_id)

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(300)

            if not self._celery_mode:
                # asyncio mode: evict expired in-memory jobs
                cutoff = datetime.now(timezone.utc).timestamp() - self._ttl
                expired = [
                    jid for jid, j in self._jobs.items()
                    if j.created_at.timestamp() < cutoff
                ]
                for jid in expired:
                    self._jobs.pop(jid)
                    try:
                        from rag.company_ingest import delete_company_docs
                        delete_company_docs(jid)
                    except Exception:
                        pass
                # In Celery mode, Redis TTL handles expiry automatically.
                # Company doc ChromaDB cleanup is handled per-job in tasks.py.

            # Purge expired document sessions (both modes, separate TTL)
            try:
                from config import settings as _s
                from services.document_store import document_store
                document_store.purge_expired(_s.document_ttl_seconds)
            except Exception:
                pass
