from datetime import timedelta

from app.models.task import Priority


PRIORITY_REMINDER_MAP = {
    Priority.urgente: timedelta(hours=1, minutes=15),
    Priority.alta: timedelta(hours=2),
    Priority.media: timedelta(days=1),
    Priority.baixa: timedelta(0),
}


def get_reminder_advance(priority: str) -> timedelta:
    p = Priority(priority)
    return PRIORITY_REMINDER_MAP.get(p, timedelta(hours=1))


def calculate_reminder_time(due_date, priority: str):
    advance = get_reminder_advance(priority)
    return due_date - advance


def should_send_at_due_date(priority: str) -> bool:
    return priority == Priority.urgente
