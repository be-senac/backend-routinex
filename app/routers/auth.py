from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest, ConfirmEmailRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


@router.post("/register", status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await auth_service.register_user(db, data.name, data.email, data.password)
        return {"message": "Usuario registrado. Verifique seu e-mail para confirmar a conta."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        token = await auth_service.login_user(db, data.email, data.password)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/confirm-email")
async def confirm_email(data: ConfirmEmailRequest, db: AsyncSession = Depends(get_db)):
    try:
        await auth_service.confirm_email(db, data.token)
        return {"message": "E-mail confirmado com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.forgot_password(db, data.email)
    return {"message": "Se o e-mail estiver cadastrado, voce recebera um link de redefinicao."}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        await auth_service.reset_password(db, data.token, data.new_password)
        return {"message": "Senha redefinida com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
