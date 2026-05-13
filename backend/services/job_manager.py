import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from models.company_profile import CompanyProfile
from models.compliance_report import ComplianceReport
from models.api_responses import StatusResponse, StepProgress
from models.enums import AnalysisStep, JobStatus


class _Job:
    def __init__(self, job_id: str, profile: CompanyProfile, doc_session_id: Optional[str] = None) -> None:
        self.job_id = job_id
        self.profile = profile
        self.doc_session_id = doc_session_id
        self.status = JobStatus.PENDING
        self.current_step: Optional[AnalysisStep] = None
        self.steps: list[StepProgress] = []
        self.report: Optional[ComplianceReport] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)

    def to_status_response(self) -> StatusResponse:
        return StatusResponse(
            job_id=self.job_id,
            status=self.status,
            current_step=self.current_step,
            steps=self.steps,
            error=self.error,
        )


class JobManager:
    """
    In-memory async job manager for analysis runs.
    Replaced by a persistent queue (e.g., Redis + Celery) in production.
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._jobs: dict[str, _Job] = {}
        self._ttl = ttl_seconds
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def create_job(self, profile: CompanyProfile, doc_session_id: Optional[str] = None) -> str:
        job_id = str(uuid.uuid4())
        job = _Job(job_id=job_id, profile=profile, doc_session_id=doc_session_id)
        self._jobs[job_id] = job
        from services.report_store import save_profile
        save_profile(job_id, profile.model_dump())
        asyncio.create_task(self._run_pipeline(job))
        return job_id

    def get_status(self, job_id: str) -> Optional[StatusResponse]:
        job = self._jobs.get(job_id)
        if job:
            return job.to_status_response()
        from services.report_store import exists
        if exists(job_id):
            return StatusResponse(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                current_step=None,
                steps=[],
                error=None,
            )
        return None

    def get_report(self, job_id: str) -> Optional[ComplianceReport]:
        job = self._jobs.get(job_id)
        if job and job.status in (JobStatus.COMPLETED, JobStatus.PARTIAL):
            return job.report
        from services.report_store import load
        return load(job_id)

    async def _run_pipeline(self, job: _Job) -> None:
        from agent.compliance_agent import run_analysis

        job.status = JobStatus.RUNNING

        def on_step(step: AnalysisStep) -> None:
            job.current_step = step
            for sp in job.steps:
                if sp.step == step:
                    sp.status = JobStatus.RUNNING
                    return
            job.steps.append(StepProgress(step=step, status=JobStatus.RUNNING))

        try:
            report = await run_analysis(
                job.job_id, job.profile,
                on_step=on_step,
                doc_session_id=job.doc_session_id,
            )

            for sp in job.steps:
                sp.status = JobStatus.COMPLETED

            job.report = report
            job.current_step = None
            job.status = (
                JobStatus.PARTIAL if report.requires_manual_review else JobStatus.COMPLETED
            )
            from services.report_store import save as save_report
            save_report(report)

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(300)
            cutoff = datetime.now(timezone.utc).timestamp() - self._ttl
            expired = [
                jid
                for jid, j in self._jobs.items()
                if j.created_at.timestamp() < cutoff
            ]
            for jid in expired:
                job = self._jobs.pop(jid)
                # Clean up per-job ChromaDB collection and temp docs
                try:
                    from rag.company_ingest import delete_company_docs
                    delete_company_docs(jid)
                except Exception:
                    pass
                if job.doc_session_id:
                    try:
                        from services.document_store import document_store
                        document_store.clear(job.doc_session_id)
                    except Exception:
                        pass
