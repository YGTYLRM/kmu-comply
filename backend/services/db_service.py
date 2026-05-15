"""
Persists analysis results to the PostgreSQL database.
Called after every completed analysis run (manual or scheduled).
"""
import logging
from datetime import datetime, timezone

from models.company_profile import CompanyProfile
from models.compliance_report import ComplianceReport

logger = logging.getLogger(__name__)


async def upsert_company(user_id: str, profile: CompanyProfile) -> str:
    """
    Create or update a Company record for this user.
    Matches on (user_id, company_name) — re-analyses of the same company
    update the existing record rather than creating a duplicate.
    Returns the company_id.
    """
    from db.database import AsyncSessionLocal
    from db.models import Company, Profile
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Ensure profile row exists
        result = await db.execute(select(Profile).where(Profile.id == user_id))
        if not result.scalar_one_or_none():
            profile_row = Profile(id=user_id)
            db.add(profile_row)
            await db.flush()

        # Find existing company for this user with the same name
        result = await db.execute(
            select(Company).where(
                Company.user_id == user_id,
                Company.name == profile.company_name,
            )
        )
        company = result.scalar_one_or_none()

        data = profile.model_dump()
        fields = {
            "name": data["company_name"],
            "industry": data.get("industry"),
            "country": data.get("country", "DE"),
            "employee_count": data.get("employee_count"),
            "annual_revenue_eur": data.get("annual_revenue_eur"),
            "balance_sheet_total_eur": data.get("balance_sheet_total_eur"),
            "processes_personal_data": data.get("processes_personal_data", False),
            "processes_special_category_data": data.get("processes_special_category_data", False),
            "processing_is_occasional": data.get("processing_is_occasional", False),
            "has_dpo": data.get("has_dpo", False),
            "has_processing_records": data.get("has_processing_records", False),
            "has_supply_chain_abroad": data.get("has_supply_chain_abroad", False),
            "supply_chain_countries": data.get("supply_chain_countries"),
            "annual_energy_consumption_mwh": data.get("annual_energy_consumption_mwh"),
            "has_energy_management_system": data.get("has_energy_management_system", False),
            "has_conducted_energy_audit": data.get("has_conducted_energy_audit", False),
            "is_listed_company": data.get("is_listed_company", False),
            "has_sustainability_report": data.get("has_sustainability_report", False),
            "is_critical_infrastructure_sector": data.get("is_critical_infrastructure_sector", False),
            "uses_ai_systems": data.get("uses_ai_systems", False),
            "has_privacy_policy": data.get("has_privacy_policy"),
            "has_processor_agreements": data.get("has_processor_agreements"),
            "has_data_breach_procedure": data.get("has_data_breach_procedure"),
            "has_tom_documentation": data.get("has_tom_documentation"),
            "has_data_retention_policy": data.get("has_data_retention_policy"),
            "has_data_protection_training": data.get("has_data_protection_training"),
            "transfers_data_outside_eea": data.get("transfers_data_outside_eea"),
            "has_consent_management": data.get("has_consent_management"),
            "has_information_security_policy": data.get("has_information_security_policy"),
            "has_incident_response_plan": data.get("has_incident_response_plan"),
            "has_business_continuity_plan": data.get("has_business_continuity_plan"),
            "has_vulnerability_management": data.get("has_vulnerability_management"),
            "has_mfa_implemented": data.get("has_mfa_implemented"),
            "has_supply_chain_security_assessment": data.get("has_supply_chain_security_assessment"),
            "has_security_awareness_training": data.get("has_security_awareness_training"),
            "ai_systems_are_high_risk": data.get("ai_systems_are_high_risk"),
            "has_ai_risk_assessment": data.get("has_ai_risk_assessment"),
            "has_ai_usage_documentation": data.get("has_ai_usage_documentation"),
            "has_human_oversight_procedure": data.get("has_human_oversight_procedure"),
            "has_gefaehrdungsbeurteilung": data.get("has_gefaehrdungsbeurteilung"),
            "has_gefaehrdungsbeurteilung_documented": data.get("has_gefaehrdungsbeurteilung_documented"),
            "has_first_aid_measures": data.get("has_first_aid_measures"),
            "has_employee_safety_training": data.get("has_employee_safety_training"),
            "has_anti_discrimination_policy": data.get("has_anti_discrimination_policy"),
            "has_agc_complaints_procedure": data.get("has_agc_complaints_procedure"),
            "has_working_time_records": data.get("has_working_time_records"),
            "uses_subcontractors": data.get("uses_subcontractors"),
            "has_whistleblower_channel": data.get("has_whistleblower_channel"),
            "has_whistleblower_policy": data.get("has_whistleblower_policy"),
            "has_lksg_policy_statement": data.get("has_lksg_policy_statement"),
            "has_supplier_code_of_conduct": data.get("has_supplier_code_of_conduct"),
            "has_supplier_risk_assessment": data.get("has_supplier_risk_assessment"),
            "has_lksg_complaints_procedure": data.get("has_lksg_complaints_procedure"),
            "existing_compliance_notes": data.get("existing_compliance_notes"),
            "profile_raw": data,   # full profile snapshot for re-assessment and template generation
            "updated_at": datetime.now(timezone.utc),
        }

        if company:
            for k, v in fields.items():
                setattr(company, k, v)
        else:
            company = Company(user_id=user_id, **fields)
            db.add(company)

        await db.commit()
        await db.refresh(company)
        return company.id


async def save_report_to_db(
    company_id: str,
    report: ComplianceReport,
    triggered_by: str = "manual",
) -> None:
    """Save a completed report and its gap items to the database."""
    from db.database import AsyncSessionLocal
    from db.models import Report, GapItem
    import json

    async with AsyncSessionLocal() as db:
        report_row = Report(
            company_id=company_id,
            job_id=report.job_id,
            overall_score_percent=report.overall_score_percent,
            triggered_by=triggered_by,
            raw_json=json.loads(report.model_dump_json()),
        )
        db.add(report_row)
        await db.flush()

        for gap in report.gap_analysis:
            db.add(GapItem(
                report_id=report_row.id,
                regulation=gap.regulation,
                article_number=getattr(gap, "article_number", None),
                status=gap.status.value if hasattr(gap.status, "value") else str(gap.status),
                finding=getattr(gap, "finding", None),
                evidence=getattr(gap, "evidence", None),
            ))

        await db.commit()
        logger.info("db_service: saved report %s for company %s", report.job_id, company_id)


async def get_all_companies_due_for_reassessment(interval_days: int = 30) -> list[dict]:
    """
    Return all companies whose last report is older than interval_days.
    Used by the scheduler to queue monthly re-assessments.
    """
    from db.database import AsyncSessionLocal
    from db.models import Company, Report, Profile
    from sqlalchemy import select, func

    cutoff = datetime.now(timezone.utc).timestamp() - (interval_days * 86400)
    results = []

    async with AsyncSessionLocal() as db:
        # Get the latest report date per company
        subq = (
            select(Report.company_id, func.max(Report.created_at).label("last_report"))
            .group_by(Report.company_id)
            .subquery()
        )
        stmt = (
            select(Company, Profile.email, subq.c.last_report)
            .join(Profile, Profile.id == Company.user_id)
            .outerjoin(subq, subq.c.company_id == Company.id)
            .where(
                (subq.c.last_report == None) |  # never assessed
                (func.extract("epoch", subq.c.last_report) < cutoff)
            )
        )
        rows = (await db.execute(stmt)).all()
        for company, email, last_report in rows:
            results.append({
                "company_id": company.id,
                "user_id": company.user_id,
                "user_email": email,
                "company_name": company.name,
                "last_report": last_report,
                "profile": _company_to_profile(company),
            })
    return results


async def get_companies_for_regulation(regulation_name: str) -> list[dict]:
    """
    Return all companies that had a specific regulation apply to them in their last report.
    Used when a regulation text changes.
    """
    from db.database import AsyncSessionLocal
    from db.models import Company, Report, GapItem, Profile
    from sqlalchemy import select, func

    results = []
    async with AsyncSessionLocal() as db:
        # Latest report per company
        latest_subq = (
            select(Report.company_id, func.max(Report.created_at).label("last_report"))
            .group_by(Report.company_id)
            .subquery()
        )
        stmt = (
            select(Company, Profile.email)
            .join(Profile, Profile.id == Company.user_id)
            .join(latest_subq, latest_subq.c.company_id == Company.id)
            .join(Report, (Report.company_id == Company.id) & (Report.created_at == latest_subq.c.last_report))
            .join(GapItem, GapItem.report_id == Report.id)
            .where(GapItem.regulation == regulation_name)
            .distinct()
        )
        rows = (await db.execute(stmt)).all()
        for company, email in rows:
            results.append({
                "company_id": company.id,
                "user_id": company.user_id,
                "user_email": email,
                "company_name": company.name,
                "profile": _company_to_profile(company),
            })
    return results


async def get_report_by_job_id(job_id: str) -> dict | None:
    """
    Load a full report JSON from the DB by job_id.
    Returns the raw_json dict or None if not found.
    """
    from db.database import AsyncSessionLocal
    from db.models import Report
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Report.raw_json).where(Report.job_id == job_id)
            )
            return result.scalar_one_or_none()
    except Exception as exc:
        logger.warning("db_service: get_report_by_job_id failed for %s: %s", job_id, exc)
        return None


async def report_exists_in_db(job_id: str) -> bool:
    """Return True if a report with this job_id exists in the DB."""
    from db.database import AsyncSessionLocal
    from db.models import Report
    from sqlalchemy import select, func

    try:
        async with AsyncSessionLocal() as db:
            count = (await db.execute(
                select(func.count()).where(Report.job_id == job_id)
            )).scalar_one()
            return count > 0
    except Exception:
        return False


async def list_reports_for_user(user_id: str, limit: int = 50) -> list[dict]:
    """
    Return report summaries for a user from the DB, newest first.
    Replaces the O(n) filesystem scan in report_store.list_recent().
    """
    from db.database import AsyncSessionLocal
    from db.models import Report, Company
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(
                    Report.job_id,
                    Report.overall_score_percent,
                    Report.created_at,
                    Company.name.label("company_name"),
                    Report.raw_json,
                )
                .join(Company, Company.id == Report.company_id)
                .where(Company.user_id == user_id)
                .order_by(Report.created_at.desc())
                .limit(limit)
            )
            rows = (await db.execute(stmt)).all()
            results = []
            for job_id, score, created_at, company_name, raw in rows:
                applicable = 0
                if raw:
                    applicable = sum(
                        1 for r in raw.get("applicable_regulations", []) if r.get("applies")
                    )
                results.append({
                    "job_id": job_id,
                    "company_name": company_name,
                    "generated_at": created_at.isoformat() if created_at else None,
                    "overall_score_percent": score,
                    "applicable_regulation_count": applicable,
                })
            return results
    except Exception as exc:
        logger.warning("db_service: list_reports_for_user failed: %s", exc)
        return []


async def get_job_owner(job_id: str) -> str | None:
    """
    Return the user_id that owns a completed job, queried from the DB.
    Returns None if the job is not yet persisted (still running) or unknown.
    """
    from db.database import AsyncSessionLocal
    from db.models import Report, Company
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Company.user_id)
                .join(Report, Report.company_id == Company.id)
                .where(Report.job_id == job_id)
                .limit(1)
            )
            return result.scalar_one_or_none()
    except Exception:
        return None


def _company_to_profile(company) -> dict:
    """Convert a Company ORM object back to a CompanyProfile-compatible dict."""
    return {
        "company_name": company.name,
        "industry": company.industry or "Other",
        "country": company.country or "DE",
        "employee_count": company.employee_count or 1,
        "annual_revenue_eur": company.annual_revenue_eur,
        "balance_sheet_total_eur": company.balance_sheet_total_eur,
        "processes_personal_data": company.processes_personal_data,
        "processes_special_category_data": company.processes_special_category_data,
        "processing_is_occasional": company.processing_is_occasional,
        "has_dpo": company.has_dpo,
        "has_processing_records": company.has_processing_records,
        "has_supply_chain_abroad": company.has_supply_chain_abroad,
        "supply_chain_countries": company.supply_chain_countries or [],
        "annual_energy_consumption_mwh": company.annual_energy_consumption_mwh,
        "has_energy_management_system": company.has_energy_management_system,
        "has_conducted_energy_audit": company.has_conducted_energy_audit,
        "is_listed_company": company.is_listed_company,
        "has_sustainability_report": company.has_sustainability_report,
        "is_critical_infrastructure_sector": company.is_critical_infrastructure_sector,
        "uses_ai_systems": company.uses_ai_systems,
        "has_privacy_policy": company.has_privacy_policy,
        "has_processor_agreements": company.has_processor_agreements,
        "has_data_breach_procedure": company.has_data_breach_procedure,
        "has_tom_documentation": company.has_tom_documentation,
        "has_data_retention_policy": company.has_data_retention_policy,
        "has_data_protection_training": company.has_data_protection_training,
        "transfers_data_outside_eea": company.transfers_data_outside_eea,
        "has_consent_management": company.has_consent_management,
        "has_information_security_policy": company.has_information_security_policy,
        "has_incident_response_plan": company.has_incident_response_plan,
        "has_business_continuity_plan": company.has_business_continuity_plan,
        "has_vulnerability_management": company.has_vulnerability_management,
        "has_mfa_implemented": company.has_mfa_implemented,
        "has_supply_chain_security_assessment": company.has_supply_chain_security_assessment,
        "has_security_awareness_training": company.has_security_awareness_training,
        "ai_systems_are_high_risk": company.ai_systems_are_high_risk,
        "has_ai_risk_assessment": company.has_ai_risk_assessment,
        "has_ai_usage_documentation": company.has_ai_usage_documentation,
        "has_human_oversight_procedure": company.has_human_oversight_procedure,
        "has_gefaehrdungsbeurteilung": company.has_gefaehrdungsbeurteilung,
        "has_gefaehrdungsbeurteilung_documented": company.has_gefaehrdungsbeurteilung_documented,
        "has_first_aid_measures": company.has_first_aid_measures,
        "has_employee_safety_training": company.has_employee_safety_training,
        "has_anti_discrimination_policy": company.has_anti_discrimination_policy,
        "has_agc_complaints_procedure": company.has_agc_complaints_procedure,
        "has_working_time_records": company.has_working_time_records,
        "uses_subcontractors": company.uses_subcontractors,
        "has_whistleblower_channel": company.has_whistleblower_channel,
        "has_whistleblower_policy": company.has_whistleblower_policy,
        "has_lksg_policy_statement": company.has_lksg_policy_statement,
        "has_supplier_code_of_conduct": company.has_supplier_code_of_conduct,
        "has_supplier_risk_assessment": company.has_supplier_risk_assessment,
        "has_lksg_complaints_procedure": company.has_lksg_complaints_procedure,
        "existing_compliance_notes": company.existing_compliance_notes,
    }
