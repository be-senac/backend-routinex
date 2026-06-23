import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, extract, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.category import Category
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary, DashboardCharts, DashboardKPIs,
    DailyDistribution, CategoryDistribution, MonthlyEvolution,
)


def _start_of_week(dt: datetime) -> datetime:
    return dt - timedelta(days=dt.weekday())


def _start_of_previous_week(dt: datetime) -> datetime:
    return _start_of_week(dt) - timedelta(weeks=1)


async def get_dashboard_summary(db: AsyncSession, user_id: uuid.UUID) -> DashboardSummary:
    now = datetime.now(timezone.utc)
    this_week_start = _start_of_week(now)
    prev_week_start = _start_of_previous_week(now)
    prev_week_end = this_week_start

    base_filter = and_(
        Task.user_id == user_id,
        Task.is_deleted == False,
    )

    this_completed = await db.execute(
        select(func.count()).select_from(Task).where(
            base_filter,
            Task.status == TaskStatus.concluida,
            Task.completed_at >= this_week_start,
        )
    )
    this_in_progress = await db.execute(
        select(func.count()).select_from(Task).where(
            base_filter,
            Task.status == TaskStatus.em_andamento,
            Task.created_at >= this_week_start,
        )
    )
    this_overdue = await db.execute(
        select(func.count()).select_from(Task).where(
            base_filter,
            Task.status != TaskStatus.concluida,
            Task.due_date < now,
            Task.due_date >= this_week_start,
        )
    )
    prev_completed = await db.execute(
        select(func.count()).select_from(Task).where(
            base_filter,
            Task.status == TaskStatus.concluida,
            Task.completed_at >= prev_week_start,
            Task.completed_at < prev_week_end,
        )
    )
    prev_in_progress = await db.execute(
        select(func.count()).select_from(Task).where(
            base_filter,
            Task.status == TaskStatus.em_andamento,
            Task.created_at >= prev_week_start,
            Task.created_at < prev_week_end,
        )
    )
    prev_overdue = await db.execute(
        select(func.count()).select_from(Task).where(
            base_filter,
            Task.status != TaskStatus.concluida,
            Task.due_date < prev_week_end,
            Task.due_date >= prev_week_start,
        )
    )

    return DashboardSummary(
        completed=this_completed.scalar() or 0,
        in_progress=this_in_progress.scalar() or 0,
        overdue=this_overdue.scalar() or 0,
        completed_previous_week=prev_completed.scalar() or 0,
        in_progress_previous_week=prev_in_progress.scalar() or 0,
        overdue_previous_week=prev_overdue.scalar() or 0,
    )


async def get_dashboard_charts(db: AsyncSession, user_id: uuid.UUID) -> DashboardCharts:
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    daily_completed = await db.execute(
        select(
            func.date(Task.completed_at).label("date"),
            func.count().label("completed"),
        )
        .where(
            Task.user_id == user_id,
            Task.is_deleted == False,
            Task.status == TaskStatus.concluida,
            Task.completed_at >= seven_days_ago,
        )
        .group_by(func.date(Task.completed_at))
    )
    daily_created = await db.execute(
        select(
            func.date(Task.created_at).label("date"),
            func.count().label("created"),
        )
        .where(
            Task.user_id == user_id,
            Task.is_deleted == False,
            Task.created_at >= seven_days_ago,
        )
        .group_by(func.date(Task.created_at))
    )

    completed_by_date = {str(row.date): row.completed for row in daily_completed.all()}
    created_by_date = {str(row.date): row.created for row in daily_created.all()}

    all_dates = set(completed_by_date.keys()) | set(created_by_date.keys())
    daily_dist = [
        DailyDistribution(
            date=d,
            completed=completed_by_date.get(d, 0),
            created=created_by_date.get(d, 0),
        )
        for d in sorted(all_dates)
    ]

    cat_result = await db.execute(
        select(
            Category.name.label("category"),
            Category.color.label("color"),
            func.count().label("count"),
        )
        .join(Task, Task.category_id == Category.id)
        .where(
            Task.user_id == user_id,
            Task.is_deleted == False,
            Task.status == TaskStatus.concluida,
        )
        .group_by(Category.name, Category.color)
    )
    cat_dist = [
        CategoryDistribution(category=row.category, color=row.color, count=row.count)
        for row in cat_result.all()
    ]

    six_months_ago = now - timedelta(days=180)
    monthly_result = await db.execute(
        select(
            func.to_char(Task.completed_at, "YYYY-MM").label("month"),
            func.count().label("total"),
        )
        .where(
            Task.user_id == user_id,
            Task.is_deleted == False,
            Task.status == TaskStatus.concluida,
            Task.completed_at >= six_months_ago,
        )
        .group_by(func.to_char(Task.completed_at, "YYYY-MM"))
    )
    monthly_evo = [
        MonthlyEvolution(month=row.month, completion_rate=float(row.total))
        for row in monthly_result.all()
    ]

    return DashboardCharts(
        daily_distribution=daily_dist,
        category_distribution=cat_dist,
        monthly_evolution=monthly_evo,
    )


async def get_dashboard_kpis(db: AsyncSession, user_id: uuid.UUID) -> DashboardKPIs:
    base_filter = and_(
        Task.user_id == user_id,
        Task.is_deleted == False,
    )

    total_created = await db.execute(
        select(func.count()).select_from(Task).where(base_filter)
    )
    total_completed = await db.execute(
        select(func.count()).select_from(Task).where(
            base_filter, Task.status == TaskStatus.concluida
        )
    )
    on_time_completed = await db.execute(
        select(func.count()).select_from(Task).where(
            base_filter,
            Task.status == TaskStatus.concluida,
            Task.completed_at <= Task.due_date,
        )
    )

    created = total_created.scalar() or 0
    completed = total_completed.scalar() or 0
    on_time = on_time_completed.scalar() or 0

    completion_rate = round((completed / created) * 100, 1) if created > 0 else 0.0
    punctuality_rate = round((on_time / completed) * 100, 1) if completed > 0 else 0.0

    user_result = await db.execute(select(User.streak).where(User.id == user_id))
    streak = user_result.scalar() or 0

    return DashboardKPIs(
        completion_rate=completion_rate,
        punctuality_rate=punctuality_rate,
        streak=streak,
    )
