import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from models.company_profile import CompanyProfile
from models.compliance_report import ComplianceReport
from models.api_responses import StatusResponse, StepProgress
from models.enums import AnalysisStep, JobStatus


class _Job:
    def __init__(self, job_id: str, profile: CompanyProfile) -> None:
        self.job_id = job_id
        self.profile = profile
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

    async def create_job(self, profile: CompanyProfile) -> str:
        job_id = str(uuid.uuid4())
        job = _Job(job_id=job_id, profile=profile)
        self._jobs[job_id] = job
        asyncio.create_task(self._run_placeholder(job))
        return job_id

    def get_status(self, job_id: str) -> Optional[StatusResponse]:
        job = self._jobs.get(job_id)
        return job.to_status_response() if job else None

    def get_report(self, job_id: str) -> Optional[ComplianceReport]:
        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.COMPLETED:
            return job.report
        return None

    async def _run_placeholder(self, job: _Job) -> None:
        """
        Placeholder pipeline runner — replaced by the real agent pipeline in Phase 3.
        Currently only runs Step 1 (threshold determination) for Phase 1 demo.
        """
        from services.threshold_engine import determine_applicable_regulations

        job.status = JobStatus.RUNNING

        try:
            step = StepProgress(
                step=AnalysisStep.PROFILE_VALIDATION,
                status=JobStatus.RUNNING,
            )
            job.steps.append(step)
            job.current_step = AnalysisStep.PROFILE_VALIDATION

            applicable = determine_applicable_regulations(job.profile)

            step.status = JobStatus.COMPLETED
            step.message = f"{sum(1 for r in applicable if r.applies)}/{len(applicable)} regulations applicable."

            job.status = JobStatus.PARTIAL
            job.current_step = None
            job.error = "Full pipeline not yet implemented (Phase 3). Applicability determination completed."

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
                del self._jobs[jid]
