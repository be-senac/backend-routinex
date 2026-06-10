import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.task import Priority, TaskStatus


class SubtaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class SubtaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    is_completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category_id: uuid.UUID | None = None
    priority: Priority = Priority.media
    due_date: datetime | None = None
    estimated_time: float | None = None
    event_time: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category_id: uuid.UUID | None = None
    priority: Priority | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None
    estimated_time: float | None = None
    event_time: str | None = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    category_id: uuid.UUID | None = None
    priority: Priority
    status: TaskStatus
    due_date: datetime | None = None
    estimated_time: float | None = None
    event_time: str | None = None
    completed_at: datetime | None = None
    is_deleted: bool = False
    progress: int = 0
    created_at: datetime
    subtasks: list[SubtaskResponse] = []

    model_config = {"from_attributes": True}
