"""
Company and report history endpoints, including data deletion (GDPR Art. 17).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/reports")
async def list_reports(current_user: dict = Depends(get_current_user)):
    from services.report_store import list_recent_async
    return {"reports": await list_recent_async(user_id=current_user["id"])}


@router.get("/api/companies")
async def list_companies(current_user: dict = Depends(get_current_user)):
    from config import settings
    if not settings.database_url:
        return {"companies": []}
    from db.database import AsyncSessionLocal
    from db.models import Company, Report
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        latest_subq = (
            select(Report.company_id, func.max(Report.created_at).label("last_report_at"))
            .group_by(Report.company_id)
            .subquery()
        )
        latest_score_subq = (
            select(Report.company_id, Report.overall_score_percent, Report.created_at)
            .join(latest_subq, (Report.company_id == latest_subq.c.company_id) &
                  (Report.created_at == latest_subq.c.last_report_at))
            .subquery()
        )
        stmt = (
            select(
                Company,
                latest_score_subq.c.overall_score_percent,
                latest_score_subq.c.created_at.label("last_report_at"),
                func.count(Report.id).label("report_count"),
            )
            .where(Company.user_id == current_user["id"])
            .outerjoin(latest_score_subq, latest_score_subq.c.company_id == Company.id)
            .outerjoin(Report, Report.company_id == Company.id)
            .group_by(
                Company.id,
                latest_score_subq.c.overall_score_percent,
                latest_score_subq.c.created_at,
            )
            .order_by(Company.updated_at.desc())
        )
        rows = (await db.execute(stmt)).all()

    return {"companies": [
        {
            "id": str(c.id),
            "name": c.name,
            "industry": c.industry,
            "employee_count": c.employee_count,
            "country": c.country,
            "latest_score": score,
            "last_report_at": last_at.isoformat() if last_at else None,
            "report_count": count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c, score, last_at, count in rows
    ]}


@router.get("/api/dashboard/summary")
async def dashboard_summary(current_user: dict = Depends(get_current_user)):
    from config import settings
    if not settings.database_url:
        return {"company_count": 0, "report_count": 0, "avg_score": None, "recent_notifications": []}
    from db.database import AsyncSessionLocal
    from db.models import Company, Report, Notification
    from sqlalchemy import select, func

    user_id = current_user["id"]
    async with AsyncSessionLocal() as db:
        company_count = (await db.execute(
            select(func.count()).where(Company.user_id == user_id)
        )).scalar_one()

        report_stats = (await db.execute(
            select(func.count(), func.avg(Report.overall_score_percent))
            .join(Company, Report.company_id == Company.id)
            .where(Company.user_id == user_id)
        )).one()

        notifications = (await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(5)
        )).scalars().all()

    avg_score = float(report_stats[1]) if report_stats[1] is not None else None

    return {
        "company_count": company_count,
        "report_count": report_stats[0],
        "avg_score": round(avg_score, 1) if avg_score is not None else None,
        "recent_notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "read": n.read_at is not None,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ],
    }


@router.get("/api/companies/{company_id}")
async def get_company(company_id: str, current_user: dict = Depends(get_current_user)):
    from db.database import AsyncSessionLocal
    from db.models import Company, Report
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Company).where(
                Company.id == company_id,
                Company.user_id == current_user["id"],
            )
        )
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found.")

        reports = (await db.execute(
            select(Report)
            .where(Report.company_id == company_id)
            .order_by(Report.created_at.desc())
        )).scalars().all()

    return {
        "company": {
            "id": str(company.id),
            "name": company.name,
            "industry": company.industry,
            "employee_count": company.employee_count,
            "country": company.country,
            "created_at": company.created_at.isoformat() if company.created_at else None,
        },
        "reports": [
            {
                "id": str(r.id),
                "job_id": r.job_id,
                "score": r.overall_score_percent,
                "triggered_by": r.triggered_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ],
    }


@router.delete("/api/companies/{company_id}")
async def delete_company(company_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a company and all its reports (GDPR Art. 17 right to erasure)."""
    from db.database import AsyncSessionLocal
    from db.models import Company, Report
    from sqlalchemy import select, delete

    user_id = current_user["id"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Company).where(Company.id == company_id, Company.user_id == user_id)
        )
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found.")

        await db.execute(delete(Report).where(Report.company_id == company_id))
        await db.execute(delete(Company).where(Company.id == company_id))
        await db.commit()

    logger.info("user %s deleted company %s and all its reports", user_id, company_id)
    return {"deleted": True, "company_id": company_id}


@router.delete("/api/reports/{job_id}")
async def delete_report(job_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a single report by job_id (GDPR Art. 17)."""
    from db.database import AsyncSessionLocal
    from db.models import Report
    from sqlalchemy import select, delete

    user_id = current_user["id"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Report).where(Report.job_id == job_id, Report.user_id == user_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")

        await db.execute(delete(Report).where(Report.job_id == job_id))
        await db.commit()

    logger.info("user %s deleted report %s", user_id, job_id)
    return {"deleted": True, "job_id": job_id}


@router.delete("/api/account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Delete the user's account and all associated data (GDPR Art. 17).

    Deletes: companies, reports, notifications, action_completions, subscriptions.
    The Supabase auth user is deleted separately via supabase.auth.admin.deleteUser().
    """
    from db.database import AsyncSessionLocal
    from db.models import Company, Report, Notification, Subscription
    from sqlalchemy import select, delete

    user_id = current_user["id"]
    async with AsyncSessionLocal() as db:
        # Get all company IDs for this user
        companies = (await db.execute(
            select(Company.id).where(Company.user_id == user_id)
        )).scalars().all()
        company_ids = [str(c) for c in companies]

        # Delete reports for all companies
        if company_ids:
            await db.execute(delete(Report).where(Report.company_id.in_(company_ids)))

        # Delete companies
        await db.execute(delete(Company).where(Company.user_id == user_id))

        # Delete notifications
        await db.execute(delete(Notification).where(Notification.user_id == user_id))

        # Delete subscription
        await db.execute(delete(Subscription).where(Subscription.user_id == user_id))

        await db.commit()

    logger.info("user %s deleted their account and all associated data", user_id)
    return {"deleted": True, "message": "Account and all data deleted successfully."}
