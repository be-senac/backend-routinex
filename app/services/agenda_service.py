import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskStatus
from app.models.routine import Routine, RecurrenceType
from app.models.category import Category
from app.schemas.agenda import AgendaItem, DailyAgendaResponse, WeeklyAgendaResponse


async def get_daily_agenda(db: AsyncSession, user_id: uuid.UUID, date_str: str) -> DailyAgendaResponse:
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())

    result = await db.execute(
        select(Task)
        .options(selectinload(Task.subtasks), selectinload(Task.category))
        .where(
            Task.user_id == user_id,
            Task.is_deleted == False,
            and_(
                (Task.due_date >= start) & (Task.due_date <= end)
            )
        )
        .order_by(Task.event_time.asc(), Task.due_date.asc())
    )
    tasks = result.scalars().all()

    items = []
    for t in tasks:
        total = len(t.subtasks)
        progress = round((sum(1 for s in t.subtasks if s.is_completed) / total) * 100) if total else 0
        items.append(AgendaItem(
            id=t.id,
            title=t.title,
            event_time=t.event_time,
            due_date=t.due_date,
            priority=t.priority,
            status=t.status,
            type="task",
            category_name=t.category.name if t.category else None,
            category_color=t.category.color if t.category else None,
            progress=progress,
        ))

    return DailyAgendaResponse(date=date_str, items=items)


async def get_weekly_agenda(db: AsyncSession, user_id: uuid.UUID, start_str: str) -> WeeklyAgendaResponse:
    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    days = []
    for i in range(7):
        day_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        daily = await get_daily_agenda(db, user_id, day_str)
        days.append(daily)
    return WeeklyAgendaResponse(days=days)


async def create_routine(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    description: str | None,
    category_id: uuid.UUID | None,
    priority: str,
    recurrence_type: str,
    recurrence_days: list[int] | None,
    start_time: str,
    estimated_time: float | None,
) -> Routine:
    routine = Routine(
        user_id=user_id,
        title=title,
        description=description,
        category_id=category_id,
        priority=priority,
        recurrence_type=recurrence_type,
        recurrence_days=recurrence_days,
        start_time=start_time,
        estimated_time=estimated_time,
    )
    db.add(routine)
    await db.commit()
    await db.refresh(routine)
    return routine


async def get_routines(db: AsyncSession, user_id: uuid.UUID) -> list[Routine]:
    result = await db.execute(
        select(Routine).where(Routine.user_id == user_id, Routine.is_active == True)
    )
    return result.scalars().all()


async def get_pending_tasks_for_optimization(db: AsyncSession, user_id: uuid.UUID) -> list[Task]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.subtasks))
        .where(
            Task.user_id == user_id,
            Task.is_deleted == False,
            Task.status != TaskStatus.concluida,
        )
        .order_by(Task.priority.desc(), Task.due_date.asc())
    )
    return result.scalars().all()
