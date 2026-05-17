"""
Celery tasks for Complio.

Currently one task: run_analysis_celery — executes the full 6-step analysis
pipeline in a Celery worker process, writing progress to Redis and the final
report to disk + DB.

The analysis pipeline is async; we run it via asyncio.run() which creates a
fresh event loop per task (standard pattern for Celery + async code).
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from celery_app import celery_app
from models.enums import AnalysisStep, JobStatus

logger = logging.getLogger(__name__)


@celery_app.task(
    name="complio.run_analysis",
    bind=True,
    max_retries=0,        # no auto-retry — LLM failures surface to users
    ignore_result=True,   # results stored on disk/DB, not in Celery backend
)
def run_analysis_celery(
    self,
    job_id: str,
    profile_dict: dict,
    doc_session_id: str | None,
    user_id: str | None,
    company_id: str | None,
) -> None:
    """Celery task: execute the full compliance analysis pipeline."""
    try:
        asyncio.run(_pipeline(job_id, profile_dict, doc_session_id, user_id, company_id))
    except Exception as exc:
        logger.error("celery task %s crashed: %s", job_id, exc)
        # Write failure state synchronously before exiting
        try:
            from services.redis_store import sync_set_job_status
            sync_set_job_status(job_id, "failed", error=str(exc))
        except Exception:
            pass
        raise


async def _pipeline(
    job_id: str,
    profile_dict: dict,
    doc_session_id: str | None,
    user_id: str | None,
    company_id: str | None,
) -> None:
    """Async core of the Celery task — runs inside asyncio.run()."""
    from models.company_profile import CompanyProfile
    from agent.compliance_agent import run_analysis
    from services.redis_store import (
        sync_set_job_status,
        sync_append_step,
        sync_set_all_steps_complete,
    )
    from services.report_store import save as disk_save

    profile = CompanyProfile(**profile_dict)

    # Mark running in Redis (sync — we're setting up, not yet in async flow)
    sync_set_job_status(job_id, "running")

    def on_step(step: AnalysisStep) -> None:
        """Sync callback called by the pipeline at each step transition."""
        sync_append_step(job_id, step.value, "running")

    try:
        report = await run_analysis(
            job_id=job_id,
            profile=profile,
            on_step=on_step,
            doc_session_id=doc_session_id,
        )

        # Persist report
        disk_save(report, user_id=user_id)

        if company_id:
            try:
                from services.db_service import save_report_to_db
                await save_report_to_db(company_id, report, triggered_by="manual")
            except Exception as exc:
                logger.warning("tasks: DB report save failed for %s: %s", job_id, exc)

        # Update DB job record
        from services.job_manager import _db_upsert_job
        final = "partial" if report.requires_manual_review else "completed"
        await _db_upsert_job(job_id, final, user_id=user_id, company_id=company_id)

        # Mark complete in Redis
        sync_set_all_steps_complete(job_id)
        sync_set_job_status(job_id, final)

        # Clean up per-job ChromaDB company document collection
        try:
            from rag.company_ingest import delete_company_docs
            delete_company_docs(job_id)
        except Exception:
            pass

        logger.info(
            "tasks: job %s complete — %.1f%%, %d gaps, %d actions",
            job_id, report.overall_score_percent,
            len(report.gap_analysis), len(report.action_plan),
        )

    except Exception as exc:
        logger.error("tasks: pipeline failed for job %s: %s", job_id, exc)
        sync_set_job_status(job_id, "failed", error=str(exc))
        try:
            from services.job_manager import _db_upsert_job
            await _db_upsert_job(job_id, "failed", error=str(exc), user_id=user_id)
        except Exception:
            pass
        raise
