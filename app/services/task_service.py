import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskStatus, Priority
from app.models.subtask import Subtask
from app.models.category import Category
from app.schemas.task import TaskCreate, TaskUpdate


DEFAULT_CATEGORIES = [
    {"name": "Estudos", "color": "#4A90D9"},
    {"name": "Trabalho", "color": "#D94A4A"},
    {"name": "Saude", "color": "#4AD97A"},
    {"name": "Pessoal", "color": "#D9A84A"},
]


async def ensure_default_categories(db: AsyncSession, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(Category).where(Category.user_id == user_id, Category.is_default == True)
    )
    existing = result.scalars().all()
    if len(existing) >= len(DEFAULT_CATEGORIES):
        return

    existing_names = {c.name for c in existing}
    for cat_data in DEFAULT_CATEGORIES:
        if cat_data["name"] not in existing_names:
            category = Category(
                user_id=user_id,
                name=cat_data["name"],
                color=cat_data["color"],
                is_default=True,
            )
            db.add(category)
    await db.commit()


async def create_task(db: AsyncSession, user_id: uuid.UUID, data: TaskCreate) -> Task:
    task = Task(
        user_id=user_id,
        title=data.title,
        description=data.description,
        category_id=data.category_id,
        priority=data.priority,
        due_date=data.due_date,
        estimated_time=data.estimated_time,
        event_time=data.event_time,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task_with_progress(task: Task) -> dict:
    total = len(task.subtasks)
    if total == 0:
        progress = 0
    else:
        completed = sum(1 for s in task.subtasks if s.is_completed)
        progress = round((completed / total) * 100)
    return progress


async def get_tasks(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: str | None = None,
    priority: str | None = None,
    category_id: uuid.UUID | None = None,
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    order_by: str = "created_at",
    order_dir: str = "desc",
    include_deleted: bool = False,
) -> list[Task]:
    query = select(Task).options(selectinload(Task.subtasks)).where(Task.user_id == user_id)

    if not include_deleted:
        query = query.where(Task.is_deleted == False)

    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    if category_id:
        query = query.where(Task.category_id == category_id)
    if due_before:
        query = query.where(Task.due_date <= due_before)
    if due_after:
        query = query.where(Task.due_date >= due_after)

    order_column = getattr(Task, order_by, Task.created_at)
    if order_dir == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    result = await db.execute(query)
    return result.scalars().all()


async def update_task(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID, data: TaskUpdate) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id, Task.is_deleted == False)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError("Tarefa nao encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id, Task.is_deleted == False)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError("Tarefa nao encontrada")

    task.is_deleted = True
    task.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return True


async def complete_task(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id, Task.is_deleted == False)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError("Tarefa nao encontrada")

    task.status = TaskStatus.concluida
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task


async def create_subtask(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID, title: str) -> Subtask:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id, Task.is_deleted == False)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError("Tarefa nao encontrada")

    subtask = Subtask(task_id=task_id, title=title)
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)
    return subtask


async def toggle_subtask(db: AsyncSession, subtask_id: uuid.UUID, user_id: uuid.UUID) -> Subtask:
    result = await db.execute(
        select(Subtask).join(Task).where(Subtask.id == subtask_id, Task.user_id == user_id)
    )
    subtask = result.scalar_one_or_none()
    if not subtask:
        raise ValueError("Subtarefa nao encontrada")

    subtask.is_completed = not subtask.is_completed
    await db.commit()
    await db.refresh(subtask)
    return subtask


async def create_category(db: AsyncSession, user_id: uuid.UUID, name: str, color: str) -> Category:
    category = Category(user_id=user_id, name=name, color=color, is_default=False)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def get_categories(db: AsyncSession, user_id: uuid.UUID) -> list[Category]:
    result = await db.execute(
        select(Category).where(Category.user_id == user_id).order_by(Category.is_default.desc())
    )
    return result.scalars().all()
