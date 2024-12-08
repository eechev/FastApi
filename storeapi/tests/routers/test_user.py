import pytest
from fastapi import status
from httpx import AsyncClient


async def register_user(async_client: AsyncClient, email: str, password: str):
    return await async_client.post(
        "/register", json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    response = await register_user(async_client, "test@example.com", "password1234")
    assert response.status_code == status.HTTP_201_CREATED
    assert "User successfully created" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_with_existing_email(
    async_client: AsyncClient, registered_user: dict
):
    response = await register_user(
        async_client, registered_user["email"], "pASsword1234"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "A user with that email already exists" in response.json()["detail"]
