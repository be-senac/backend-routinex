import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services import notification_service
from app.utils.deps import get_current_user_id, get_current_user_obj

router = APIRouter(prefix="/notifications", tags=["Notificacoes"])


@router.post("/register")
async def register_fcm(data: dict, user: User = Depends(get_current_user_obj), db: AsyncSession = Depends(get_db)):
    token = data.get("fcm_token")
    if not token:
        raise HTTPException(status_code=400, detail="fcm_token e obrigatorio")
    user.fcm_token = token
    await db.commit()
    return {"message": "Token FCM registrado"}


@router.post("/reminders/{reminder_id}/snooze")
async def snooze_reminder(
    reminder_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        reminder = await notification_service.snooze_reminder(db, reminder_id, user_id)
        return {"message": "Lembrete adiado por 15 minutos", "snoozed_until": str(reminder.snoozed_until)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/focus-mode/start")
async def start_focus_mode(
    user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db),
):
    user.focus_mode_active = True
    from datetime import datetime, timezone
    user.focus_mode_started_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Modo foco ativado. Apenas notificacoes de tarefas urgentes serao enviadas."}


@router.post("/focus-mode/stop")
async def stop_focus_mode(
    user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db),
):
    user.focus_mode_active = False
    user.focus_mode_started_at = None
    await db.commit()
    return {"message": "Modo foco desativado. Todas as notificacoes pendentes serao entregues."}
