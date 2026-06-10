import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token, decode_access_token, create_token
from app.utils.email import send_confirmation_email, send_reset_password_email


async def register_user(db: AsyncSession, name: str, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise ValueError("E-mail ja cadastrado")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        is_active=False,
        is_confirmed=False,
        consent_date=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_token(email, timedelta(hours=24))
    user.confirmation_token = token
    await db.commit()

    send_confirmation_email(email, token)
    return user


async def confirm_email(db: AsyncSession, token: str) -> bool:
    payload = decode_access_token(token)
    if not payload:
        raise ValueError("Token invalido ou expirado")

    email = payload.get("sub")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Usuario nao encontrado")

    user.is_confirmed = True
    user.is_active = True
    user.confirmation_token = None
    await db.commit()
    return True


async def login_user(db: AsyncSession, email: str, password: str) -> str:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Credenciais invalidas")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = (user.locked_until - datetime.now(timezone.utc)).seconds // 60
        raise ValueError(f"Conta bloqueada. Tente novamente em {remaining} minutos")

    if not verify_password(password, user.password_hash):
        user.login_attempts += 1
        if user.login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_MINUTES)
            user.login_attempts = 0
        await db.commit()
        raise ValueError("Credenciais invalidas")

    if not user.is_active:
        raise ValueError("Conta nao confirmada. Verifique seu e-mail.")

    user.login_attempts = 0
    user.locked_until = None
    await db.commit()

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return token


async def forgot_password(db: AsyncSession, email: str) -> bool:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return True

    token = create_token(email, timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES))
    user.confirmation_token = token
    await db.commit()

    send_reset_password_email(email, token)
    return True


async def reset_password(db: AsyncSession, token: str, new_password: str) -> bool:
    payload = decode_access_token(token)
    if not payload:
        raise ValueError("Token invalido ou expirado")

    email = payload.get("sub")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Usuario nao encontrado")

    user.password_hash = hash_password(new_password)
    user.confirmation_token = None
    await db.commit()
    return True


async def get_current_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Usuario nao encontrado")
    return user
