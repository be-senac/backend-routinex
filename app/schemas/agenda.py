import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.task import Priority, TaskStatus


class AgendaItem(BaseModel):
    id: uuid.UUID
    title: str
    event_time: str | None = None
    due_date: datetime | None = None
    priority: Priority
    status: TaskStatus
    type: str = "task"
    category_name: str | None = None
    category_color: str | None = None
    progress: int = 0

    model_config = {"from_attributes": True}


class DailyAgendaResponse(BaseModel):
    date: str
    items: list[AgendaItem]


class WeeklyAgendaResponse(BaseModel):
    days: list[DailyAgendaResponse]


class OptimizeDayResponse(BaseModel):
    items: list[AgendaItem]
    total_hours: float
