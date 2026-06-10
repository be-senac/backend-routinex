import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.dashboard import DashboardSummary, DashboardCharts, DashboardKPIs
from app.services import dashboard_service
from app.utils.deps import get_current_user_id

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_service.get_dashboard_summary(db, user_id)


@router.get("/charts", response_model=DashboardCharts)
async def dashboard_charts(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_service.get_dashboard_charts(db, user_id)


@router.get("/kpis", response_model=DashboardKPIs)
async def dashboard_kpis(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_service.get_dashboard_kpis(db, user_id)
