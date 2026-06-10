import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_token):
    response = await client.post(
        "/tasks",
        json={"title": "Minha tarefa", "priority": "alta"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minha tarefa"
    assert data["priority"] == "alta"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, auth_token):
    response = await client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, auth_token):
    create = await client.post(
        "/tasks",
        json={"title": "Para editar", "priority": "media"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    task_id = create.json()["id"]

    response = await client.patch(
        f"/tasks/{task_id}",
        json={"title": "Editada"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Editada"


@pytest.mark.asyncio
async def test_complete_task(client: AsyncClient, auth_token):
    create = await client.post(
        "/tasks",
        json={"title": "Para concluir", "priority": "baixa"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    task_id = create.json()["id"]

    response = await client.post(
        f"/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "concluida"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_token):
    create = await client.post(
        "/tasks",
        json={"title": "Para deletar", "priority": "baixa"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    task_id = create.json()["id"]

    response = await client.delete(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_subtask(client: AsyncClient, auth_token):
    create = await client.post(
        "/tasks",
        json={"title": "Tarefa com subtarefa", "priority": "media"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    task_id = create.json()["id"]

    response = await client.post(
        f"/tasks/{task_id}/subtasks",
        json={"title": "Subtarefa 1"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Subtarefa 1"


@pytest.mark.asyncio
async def test_filter_tasks(client: AsyncClient, auth_token):
    response = await client.get(
        "/tasks?priority=alta",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
