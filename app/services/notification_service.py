import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder
from app.models.task import Task, Priority
from app.models.user import User


async def create_reminder_for_task(db: AsyncSession, task: Task, user: User) -> Reminder | None:
    if not task.due_date:
        return None

    from app.services.reminder_service import calculate_reminder_time, should_send_at_due_date
    reminder_time = calculate_reminder_time(task.due_date, task.priority)

    if user.focus_mode_active and task.priority != Priority.urgente:
        return None

    reminder = Reminder(
        user_id=user.id,
        task_id=task.id,
        reminder_type="task_due",
        scheduled_at=reminder_time,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder


async def snooze_reminder(db: AsyncSession, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Reminder:
    result = await db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user_id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise ValueError("Lembrete nao encontrado")

    reminder.snoozed_until = datetime.now(timezone.utc) + timedelta(minutes=15)
    reminder.is_sent = False
    await db.commit()
    await db.refresh(reminder)
    return reminder



