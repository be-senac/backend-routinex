import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_daily_agenda(client: AsyncClient, auth_token):
    response = await client.get(
        "/agenda/daily?date=2026-06-09",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "date" in data
    assert "items" in data


@pytest.mark.asyncio
async def test_weekly_agenda(client: AsyncClient, auth_token):
    response = await client.get(
        "/agenda/weekly?start=2026-06-09",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "days" in data


@pytest.mark.asyncio
async def test_create_routine(client: AsyncClient, auth_token):
    response = await client.post(
        "/agenda/routines?title=Academia&start_time=07:00&recurrence_type=diaria",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_routines(client: AsyncClient, auth_token):
    response = await client.get(
        "/agenda/routines",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
