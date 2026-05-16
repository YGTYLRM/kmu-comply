"""
Company and report history endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException

from services.auth_service import get_current_user

router = APIRouter()


@router.get("/api/reports")
async def list_reports(current_user: dict = Depends(get_current_user)):
    from services.report_store import list_recent_async
    return {"reports": await list_recent_async(user_id=current_user["id"])}


@router.get("/api/companies")
async def list_companies(current_user: dict = Depends(get_current_user)):
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
