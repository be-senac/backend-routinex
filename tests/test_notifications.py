import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_token):
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_update_preferences(client: AsyncClient, auth_token):
    response = await client.patch(
        "/users/me/preferences",
        json={"dark_mode": True, "font_size": "grande"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["dark_mode"] is True
    assert response.json()["font_size"] == "grande"


@pytest.mark.asyncio
async def test_export_data(client: AsyncClient, auth_token):
    response = await client.post(
        "/users/me/export-data",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "user" in data


@pytest.mark.asyncio
async def test_focus_mode(client: AsyncClient, auth_token):
    start = await client.post(
        "/notifications/focus-mode/start",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert start.status_code == 200

    stop = await client.post(
        "/notifications/focus-mode/stop",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert stop.status_code == 200
