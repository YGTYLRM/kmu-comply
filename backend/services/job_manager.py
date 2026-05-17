"""
Async job manager with PostgreSQL-backed persistence.

Jobs are written to the `jobs` table at creation and on every status transition.
On startup, any jobs left in RUNNING state from a previous process are marked FAILED
with a message directing the user to retry — there is no automatic re-run since the
in-flight state (profile, doc session) cannot be reliably recovered after a crash.

The in-memory dict is still used for active jobs (fast status polling). The DB is the
source of truth for jobs that have expired from memory or survived a restart.
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
    Async job manager with DB-backed persistence.
    Active jobs are kept in memory for fast polling.
    The DB is the source of truth after restarts.
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._jobs: dict[str, _Job] = {}
        self._ttl  = ttl_seconds
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
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
        """Mark any jobs left as RUNNING from a previous process as FAILED."""
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

    async def create_job(
        self,
        profile: CompanyProfile,
        doc_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        job = _Job(
            job_id=job_id, profile=profile, doc_session_id=doc_session_id,
            user_id=user_id, company_id=company_id,
        )
        self._jobs[job_id] = job
        from services.report_store import save_profile
        save_profile(job_id, profile.model_dump())
        await _db_upsert_job(job_id, "pending", user_id=user_id, company_id=company_id)
        asyncio.create_task(self._run_pipeline(job))
        return job_id

    def get_status(self, job_id: str) -> Optional[StatusResponse]:
        job = self._jobs.get(job_id)
        if job:
            return job.to_status_response()
        # Not in memory — check disk then DB (sync wrapper used here)
        from services.report_store import exists
        if exists(job_id):
            return StatusResponse(
                job_id=job_id, status=JobStatus.COMPLETED,
                current_step=None, steps=[], error=None,
            )
        return None

    async def get_status_async(self, job_id: str) -> Optional[StatusResponse]:
        """Async version — checks DB when not in memory."""
        result = self.get_status(job_id)
        if result:
            return result
        return await _db_get_status(job_id)

    def get_report(self, job_id: str) -> Optional[ComplianceReport]:
        job = self._jobs.get(job_id)
        if job and job.status in (JobStatus.COMPLETED, JobStatus.PARTIAL):
            return job.report
        from services.report_store import load
        return load(job_id)

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
            cutoff = datetime.now(timezone.utc).timestamp() - self._ttl
            expired = [
                jid for jid, j in self._jobs.items()
                if j.created_at.timestamp() < cutoff
            ]
            for jid in expired:
                job = self._jobs.pop(jid)
                try:
                    from rag.company_ingest import delete_company_docs
                    delete_company_docs(jid)
                except Exception:
                    pass
                # NOTE: uploaded documents are NOT cleared here — they use their own TTL
                # (DOCUMENT_TTL_SECONDS, default 7 days) so users can re-run analysis
                # without re-uploading. See document_store.purge_expired() below.

            # Purge expired document sessions (separate from job TTL)
            try:
                from config import settings as _s
                from services.document_store import document_store
                document_store.purge_expired(_s.document_ttl_seconds)
            except Exception:
                pass
