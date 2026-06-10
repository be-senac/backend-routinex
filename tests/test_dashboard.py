import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient, auth_token):
    response = await client.get(
        "/dashboard/summary",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "completed" in data
    assert "in_progress" in data
    assert "overdue" in data


@pytest.mark.asyncio
async def test_dashboard_charts(client: AsyncClient, auth_token):
    response = await client.get(
        "/dashboard/charts",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_kpis(client: AsyncClient, auth_token):
    response = await client.get(
        "/dashboard/kpis",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "completion_rate" in data
    assert "punctuality_rate" in data
    assert "streak" in data
