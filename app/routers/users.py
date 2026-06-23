import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest, UserPreferencesRequest, FCMTokenRequest
from app.utils.deps import get_current_user_id, get_current_user_obj
from app.utils.security import hash_password
from app.services.lgpd_service import export_user_data, schedule_account_deletion

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user_obj)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdateRequest,
    user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db),
):
    if data.name:
        user.name = data.name
    if data.email:
        existing = await db.execute(select(User).where(User.email == data.email, User.id != user.id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="E-mail ja esta em uso")
        user.email = data.email
    if data.password:
        user.password_hash = hash_password(data.password)
    if data.photo_url is not None:
        user.photo_url = data.photo_url

    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/me/preferences", response_model=UserResponse)
async def update_preferences(
    data: UserPreferencesRequest,
    user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db),
):
    if data.font_size:
        user.font_size = data.font_size
    if data.dark_mode is not None:
        user.dark_mode = data.dark_mode
    if data.accessibility_profile is not None:
        user.accessibility_profile = data.accessibility_profile
    if data.rest_start is not None:
        user.rest_start = data.rest_start
    if data.rest_end is not None:
        user.rest_end = data.rest_end
    if data.motivational_time is not None:
        user.motivational_time = data.motivational_time

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/me/fcm-token")
async def register_fcm_token(
    data: FCMTokenRequest,
    user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db),
):
    user.fcm_token = data.fcm_token
    await db.commit()
    return {"message": "Token FCM registrado com sucesso"}


@router.post("/me/export-data")
async def export_data(user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        data = await export_user_data(db, user_id)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/me", status_code=200)
async def delete_account(user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        await schedule_account_deletion(db, user_id)
        return {"message": "Conta marcada para exclusao. Os dados serao removidos em ate 30 dias."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
