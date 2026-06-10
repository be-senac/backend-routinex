import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.routine import Routine
from app.schemas.agenda import DailyAgendaResponse, WeeklyAgendaResponse, OptimizeDayResponse, AgendaItem
from app.schemas.task import TaskCreate
from app.services import agenda_service, task_service, ai_service
from app.services.notification_service import create_reminder_for_task
from app.utils.deps import get_current_user_id, get_current_user_obj
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/agenda", tags=["Agenda"])


@router.get("/daily", response_model=DailyAgendaResponse)
async def daily_agenda(
    date: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await agenda_service.get_daily_agenda(db, user_id, date)


@router.get("/weekly", response_model=WeeklyAgendaResponse)
async def weekly_agenda(
    start: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await agenda_service.get_weekly_agenda(db, user_id, start)


@router.post("/routines", status_code=201)
async def create_routine(
    title: str,
    start_time: str,
    recurrence_type: str = "diaria",
    recurrence_days: list[int] | None = None,
    description: str | None = None,
    category_id: uuid.UUID | None = None,
    priority: str = "media",
    estimated_time: float | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    routine = await agenda_service.create_routine(
        db, user_id, title, description, category_id, priority,
        recurrence_type, recurrence_days, start_time, estimated_time,
    )
    return {"id": str(routine.id), "message": "Rotina criada com sucesso"}


@router.get("/routines")
async def list_routines(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    routines = await agenda_service.get_routines(db, user_id)
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "recurrence_type": r.recurrence_type,
            "start_time": r.start_time,
            "is_active": r.is_active,
        }
        for r in routines
    ]


@router.post("/optimize", response_model=OptimizeDayResponse)
async def optimize_day(
    user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db),
):
    pending = await agenda_service.get_pending_tasks_for_optimization(db, user.id)
    if not pending:
        return OptimizeDayResponse(items=[], total_hours=0)

    try:
        result = await ai_service.optimize_day(user, pending)
    except Exception:
        raise HTTPException(status_code=503, detail="Servico de IA temporariamente indisponivel")

    import json
    try:
        schedule = json.loads(result) if isinstance(result, str) else result
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao processar sugestao de IA")

    items = []
    total_hours = 0
    for entry in schedule.get("schedule", []):
        items.append(AgendaItem(
            id=uuid.uuid4(),
            title=entry.get("task_title", ""),
            event_time=entry.get("time"),
            priority="media",
            status=TaskStatus.pendente,
            type="suggestion",
            progress=0,
        ))
        total_hours += entry.get("duration_hours", 0)

    return OptimizeDayResponse(items=items, total_hours=round(total_hours, 1))
