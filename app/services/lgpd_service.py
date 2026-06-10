import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.chat_message import ChatMessage
from app.models.category import Category
from app.models.reminder import Reminder
from app.models.routine import Routine
from app.models.subtask import Subtask


async def export_user_data(db: AsyncSession, user_id: uuid.UUID) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Usuario nao encontrado")

    data = {
        "user": {
            "name": user.name,
            "email": user.email,
            "font_size": user.font_size,
            "dark_mode": user.dark_mode,
            "accessibility_profile": user.accessibility_profile,
            "consent_date": str(user.consent_date) if user.consent_date else None,
            "created_at": str(user.created_at),
        },
        "tasks": [],
        "categories": [],
        "routines": [],
        "chat_messages": [],
    }

    tasks_result = await db.execute(select(Task).where(Task.user_id == user_id, Task.is_deleted == False))
    for t in tasks_result.scalars().all():
        data["tasks"].append({
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "due_date": str(t.due_date) if t.due_date else None,
            "created_at": str(t.created_at),
        })

    cat_result = await db.execute(select(Category).where(Category.user_id == user_id))
    for c in cat_result.scalars().all():
        data["categories"].append({"name": c.name, "color": c.color})

    routines_result = await db.execute(select(Routine).where(Routine.user_id == user_id))
    for r in routines_result.scalars().all():
        data["routines"].append({
            "title": r.title,
            "recurrence_type": r.recurrence_type,
            "start_time": r.start_time,
        })

    messages_result = await db.execute(
        select(ChatMessage).where(ChatMessage.user_id == user_id).order_by(ChatMessage.created_at)
    )
    for m in messages_result.scalars().all():
        data["chat_messages"].append({
            "role": m.role,
            "content": m.content,
            "created_at": str(m.created_at),
        })

    return data


async def schedule_account_deletion(db: AsyncSession, user_id: uuid.UUID) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Usuario nao encontrado")

    user.is_active = False

    from app.scheduler import schedule_account_deletion
    schedule_account_deletion(str(user_id), delay_days=30)

    await db.commit()
    return True
