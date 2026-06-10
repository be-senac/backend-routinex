import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "name": "New User",
        "email": "newuser@example.com",
        "password": "Pass1234",
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    data = {"name": "User", "email": "dup@example.com", "password": "Pass1234"}
    await client.post("/auth/register", json=data)
    response = await client.post("/auth/register", json=data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_invalid_password(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "name": "User",
        "email": "invalid@example.com",
        "password": "short",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login(client: AsyncClient, auth_token):
    assert auth_token is not None


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json={
        "name": "Wrong", "email": "wrong@example.com", "password": "Pass1234",
    })
    from app.database import async_session
    from app.models.user import User
    from sqlalchemy import select
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == "wrong@example.com"))
        user = result.scalar_one_or_none()
        if user:
            user.is_active = True
            user.is_confirmed = True
            await db.commit()

    response = await client.post("/auth/login", json={
        "email": "wrong@example.com", "password": "WrongPass1",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient):
    response = await client.post("/auth/forgot-password", json={"email": "test@example.com"})
    assert response.status_code == 200
