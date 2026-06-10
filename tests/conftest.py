import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import async_session, Base, engine


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_token(client: AsyncClient):
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "Test1234",
    }
    await client.post("/auth/register", json=user_data)

    from app.database import async_session
    from app.models.user import User
    from sqlalchemy import select
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one_or_none()
        if user:
            user.is_active = True
            user.is_confirmed = True
            await db.commit()

    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234",
    })
    data = response.json()
    return data.get("access_token")
