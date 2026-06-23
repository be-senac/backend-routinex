# scheduler.py
import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("routinex")

scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")


async def recreate_routine_tasks():
    from app.database import async_session
    from app.models.routine import Routine, RecurrenceType
    from app.models.task import Task, TaskStatus, Priority
    from sqlalchemy import select

    async with async_session() as db:
        now = datetime.now(timezone.utc)
        today_weekday = now.weekday()

        result = await db.execute(select(Routine).where(Routine.is_active == True))
        routines = result.scalars().all()

        for routine in routines:
            should_create = False

            if routine.recurrence_type == RecurrenceType.diaria:
                should_create = True
            elif routine.recurrence_type == RecurrenceType.semanal:
                if routine.recurrence_days and today_weekday in routine.recurrence_days:
                    should_create = True
            elif routine.recurrence_type == RecurrenceType.dias_uteis:
                if today_weekday < 5:
                    should_create = True

            if should_create:
                task = Task(
                    user_id=routine.user_id,
                    category_id=routine.category_id,
                    title=routine.title,
                    description=routine.description,
                    priority=routine.priority,
                    status=TaskStatus.pendente,
                    due_date=now,
                    event_time=routine.start_time,
                    estimated_time=routine.estimated_time,
                )
                db.add(task)

        await db.commit()
    logger.info("Rotinas recriadas com sucesso")


async def calculate_streak():
    from app.database import async_session
    from app.models.user import User
    from app.models.task import Task, TaskStatus
    from sqlalchemy import select, func, and_

    async with async_session() as db:
        result = await db.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()

        today = datetime.now(timezone.utc).date()

        for user in users:
            completed_today = await db.execute(
                select(func.count())
                .select_from(Task)
                .where(
                    Task.user_id == user.id,
                    Task.is_deleted == False,
                    Task.status == TaskStatus.concluida,
                    func.date(Task.completed_at) == today,
                )
            )
            count = completed_today.scalar() or 0

            if count > 0:
                user.streak += 1
                user.last_active_date = datetime.now(timezone.utc)
            else:
                user.streak = 0

        await db.commit()
    logger.info("Streaks calculados com sucesso")


async def delete_user_data(user_id: str):
    import uuid as uuid_mod
    from app.database import async_session
    from app.models.user import User
    from app.models.chat_message import ChatMessage
    from app.models.task import Task
    from app.models.subtask import Subtask
    from app.models.category import Category
    from app.models.reminder import Reminder
    from app.models.routine import Routine
    from sqlalchemy import select, delete as sql_delete

    async with async_session() as db:
        uid = uuid_mod.UUID(user_id)

        await db.execute(sql_delete(ChatMessage).where(ChatMessage.user_id == uid))
        await db.execute(sql_delete(Subtask).where(Subtask.task_id.in_(select(Task.id).where(Task.user_id == uid))))
        await db.execute(sql_delete(Reminder).where(Reminder.user_id == uid))
        await db.execute(sql_delete(Task).where(Task.user_id == uid))
        await db.execute(sql_delete(Routine).where(Routine.user_id == uid))
        await db.execute(sql_delete(Category).where(Category.user_id == uid))

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if user:
            user.name = "Usuario Removido"
            user.email = f"removed_{uid}@deleted.com"
            user.password_hash = ""
            user.photo_url = None
            user.fcm_token = None
            user.is_active = False

        await db.commit()
    logger.info(f"Dados do usuario {user_id} removidos")


async def send_reminder(reminder_id: str):
    from app.database import async_session
    from app.models.reminder import Reminder
    from app.models.user import User
    from app.models.task import Task, Priority
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(Reminder).where(Reminder.id == reminder_id))
        reminder = result.scalar_one_or_none()
        if not reminder or reminder.is_sent:
            return

        result = await db.execute(select(User).where(User.id == reminder.user_id))
        user = result.scalar_one_or_none()
        if not user or not user.fcm_token:
            return

        if user.focus_mode_active:
            if reminder.task_id:
                task_result = await db.execute(select(Task).where(Task.id == reminder.task_id))
                task = task_result.scalar_one_or_none()
                if task and task.priority != Priority.urgente:
                    reminder.snoozed_until = datetime.now(timezone.utc) + timedelta(hours=1)
                    await db.commit()
                    return

        try:
            from app.services.firebase_service import send_push_notification
            await send_push_notification(
                user.fcm_token,
                "RoutineX - Lembrete",
                reminder.reminder_type,
            )
        except Exception:
            logger.warning("Firebase not configured, skipping push notification")

        reminder.is_sent = True
        await db.commit()
    logger.info(f"Lembrete {reminder_id} processado")


async def schedule_task_reminders(task_id: str, user_id: str):
    from app.database import async_session
    from app.models.reminder import Reminder
    from app.models.task import Task
    from app.services.reminder_service import get_reminder_advance, should_send_at_due_date
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task or not task.due_date:
            return

        advance = get_reminder_advance(task.priority)
        reminder_time = task.due_date - advance

        reminder = Reminder(
            user_id=user_id,
            task_id=task_id,
            reminder_type="task_due",
            scheduled_at=reminder_time,
        )
        db.add(reminder)
        await db.commit()
        await db.refresh(reminder)

        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=reminder_time),
            args=[str(reminder.id)],
            id=f"reminder_{reminder.id}",
            replace_existing=True,
        )

        if should_send_at_due_date(task.priority):
            due_reminder = Reminder(
                user_id=user_id,
                task_id=task_id,
                reminder_type="task_due_now",
                scheduled_at=task.due_date,
            )
            db.add(due_reminder)
            await db.commit()
            await db.refresh(due_reminder)

            scheduler.add_job(
                send_reminder,
                trigger=DateTrigger(run_date=task.due_date),
                args=[str(due_reminder.id)],
                id=f"reminder_{due_reminder.id}",
                replace_existing=True,
            )


def schedule_account_deletion(user_id: str, delay_days: int = 30):
    run_date = datetime.now(timezone.utc) + timedelta(days=delay_days)
    scheduler.add_job(
        delete_user_data,
        trigger=DateTrigger(run_date=run_date),
        args=[user_id],
        id=f"delete_user_{user_id}",
        replace_existing=True,
    )
    logger.info(f"Exclusao de conta agendada para {run_date} (usuario {user_id})")


def start_scheduler():
    scheduler.add_job(
        recreate_routine_tasks,
        trigger=CronTrigger(hour=0, minute=5, timezone="America/Sao_Paulo"),
        id="recreate_routine_tasks",
        replace_existing=True,
    )
    scheduler.add_job(
        calculate_streak,
        trigger=CronTrigger(hour=23, minute=55, timezone="America/Sao_Paulo"),
        id="calculate_streak",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler iniciado - tarefas diarias registradas")


def shutdown_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler finalizado")