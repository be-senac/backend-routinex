import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.subtask import Subtask
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, SubtaskCreate, SubtaskResponse
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services import task_service
from app.utils.deps import get_current_user_id

router = APIRouter(prefix="/tasks", tags=["Tarefas"])


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.create_task(db, user_id, data)
    return task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: str | None = None,
    priority: str | None = None,
    category_id: uuid.UUID | None = None,
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    order_by: str = Query("created_at"),
    order_dir: str = Query("desc"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tasks = await task_service.get_tasks(
        db, user_id, status, priority, category_id, due_before, due_after, order_by, order_dir
    )
    result = []
    for t in tasks:
        progress = await task_service.get_task_with_progress(t)
        result.append(TaskResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            category_id=t.category_id,
            priority=t.priority,
            status=t.status,
            due_date=t.due_date,
            estimated_time=t.estimated_time,
            event_time=t.event_time,
            completed_at=t.completed_at,
            is_deleted=t.is_deleted,
            progress=progress,
            created_at=t.created_at,
            subtasks=[SubtaskResponse(id=s.id, title=s.title, is_completed=s.is_completed, created_at=s.created_at) for s in t.subtasks],
        ))
    return result


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await task_service.update_task(db, task_id, user_id, data)
        return task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{task_id}", status_code=200)
async def delete_task(
    task_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        await task_service.delete_task(db, task_id, user_id)
        return {"message": "Tarefa movida para lixeira"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await task_service.complete_task(db, task_id, user_id)
        return task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{task_id}/subtasks", response_model=SubtaskResponse, status_code=201)
async def create_subtask(
    task_id: uuid.UUID,
    data: SubtaskCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        subtask = await task_service.create_subtask(db, task_id, user_id, data.title)
        return subtask
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/subtasks/{subtask_id}/toggle", response_model=SubtaskResponse)
async def toggle_subtask(
    subtask_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        subtask = await task_service.toggle_subtask(db, subtask_id, user_id)
        return subtask
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    category = await task_service.create_category(db, user_id, data.name, data.color)
    return CategoryResponse(
        id=category.id,
        name=category.name,
        color=category.color,
        is_default=category.is_default,
        created_at=str(category.created_at),
    )


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await task_service.ensure_default_categories(db, user_id)
    categories = await task_service.get_categories(db, user_id)
    return [
        CategoryResponse(id=c.id, name=c.name, color=c.color, is_default=c.is_default, created_at=str(c.created_at))
        for c in categories
    ]
