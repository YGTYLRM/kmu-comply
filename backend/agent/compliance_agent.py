"""
Main orchestrator — runs the full 6-step compliance analysis pipeline.

Usage:
    report = await run_analysis(job_id, profile, on_step=callback)
"""
import asyncio
import logging
from collections.abc import Callable

from agent.actions import assemble_report
from agent.planning import (
    determine_applicability,
    generate_action_plan,
    retrieve_regulatory_context,
    run_gap_analysis,
)
from agent.profiling import enrich_profile
from agent.validation import validate_report
from models.company_profile import CompanyProfile
from models.compliance_report import ComplianceReport
from models.enums import AnalysisStep

logger = logging.getLogger(__name__)


async def run_analysis(
    job_id: str,
    profile: CompanyProfile,
    on_step: Callable[[AnalysisStep], None] | None = None,
    doc_session_id: str | None = None,
) -> ComplianceReport:
    """
    Execute the full 6-step compliance analysis pipeline.

    Steps that fail validation are logged and added to
    report.requires_manual_review — the pipeline never aborts mid-run.
    The optional on_step callback receives the current AnalysisStep at each
    transition, allowing callers to track progress without coupling to internals.
    """
    loop = asyncio.get_running_loop()
    failures: list[str] = []

    def notify(step: AnalysisStep) -> None:
        if on_step:
            try:
                on_step(step)
            except Exception:
                pass

    # Step 1 — profile enrichment
    notify(AnalysisStep.PROFILE_VALIDATION)
    logger.info("job %s step 1: profile enrichment", job_id)
    enriched = await loop.run_in_executor(None, enrich_profile, profile)

    # Step 2 — applicability (deterministic, no LLM)
    notify(AnalysisStep.APPLICABILITY_DETERMINATION)
    logger.info("job %s step 2: applicability determination", job_id)
    applicability = await loop.run_in_executor(None, determine_applicability, enriched)

    # Step 3 — RAG retrieval + optional company doc ingestion
    notify(AnalysisStep.ARTICLE_RETRIEVAL)
    logger.info("job %s step 3: article retrieval", job_id)
    chunks, empty_regs = await loop.run_in_executor(
        None, retrieve_regulatory_context, enriched, applicability
    )
    if empty_regs:
        logger.warning(
            "job %s: %d regulation(s) have empty KB — will produce CANNOT_ASSESS: %s",
            job_id, len(empty_regs), empty_regs,
        )

    # Ingest company documents if provided (decrypted in memory via document_store)
    if doc_session_id:
        from rag.company_ingest import ingest_company_documents
        from services.document_store import document_store
        if document_store.list_files(doc_session_id):
            logger.info("job %s: ingesting company documents from session %s", job_id, doc_session_id)
            await loop.run_in_executor(
                None, ingest_company_documents, job_id, doc_session_id
            )

    # Step 4 — gap analysis (with company doc evidence if available)
    # Regulations with empty KB are passed separately — they get CANNOT_ASSESS
    # without calling the LLM, preventing ungrounded legal citation hallucination.
    notify(AnalysisStep.GAP_ANALYSIS)
    logger.info("job %s step 4: gap analysis", job_id)
    gaps = await loop.run_in_executor(
        None, run_gap_analysis, enriched, chunks, failures, job_id, empty_regs
    )

    # Step 5 — action plan
    notify(AnalysisStep.ACTION_PLAN)
    logger.info("job %s step 5: action plan", job_id)
    actions = await loop.run_in_executor(
        None, generate_action_plan, enriched, gaps, failures
    )

    # Step 6 — report assembly
    notify(AnalysisStep.REPORT_ASSEMBLY)
    logger.info("job %s step 6: report assembly", job_id)
    report = await loop.run_in_executor(
        None, assemble_report, job_id, enriched, applicability, chunks, gaps, actions, failures
    )

    # Self-validation
    issues = validate_report(report)
    if issues:
        report.requires_manual_review.extend(
            i for i in issues if i not in report.requires_manual_review
        )
        logger.warning("job %s: %d validation issue(s)", job_id, len(issues))

    logger.info(
        "job %s: complete — score %.1f%%, %d gaps, %d actions, %d manual review item(s)",
        job_id, report.overall_score_percent, len(gaps), len(actions),
        len(report.requires_manual_review),
    )
    return report
