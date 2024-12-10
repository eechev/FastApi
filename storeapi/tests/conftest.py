"""
This is a fixture file
"""

import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

os.environ["ENV_STATE"] = "test"

from storeapi.database import database, user_table
from storeapi.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    """Selects the anyio backend for pytest-asyncio.

    This fixture is required to be session-scoped because it sets a global
    variable that is used by pytest-asyncio to select the async backend.

    It is also a good idea to make it a fixture, rather than just calling
    `anyio.run()` in a test, because this allows the fixture to be reused
    in other tests.

    See https://github.com/anyio/pytest-asyncio#backend-selection
    """

    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    """Fixture that ensures the post and comment tables are empty before and after
    each test.

    This fixture is marked as `autouse=True`, which means that it will be run
    before and after each test, even if the test does not directly use this
    fixture.

    The `yield` statement is used to define the point at which the fixture is
    considered to be "done". In this case, the fixture is considered to be
    "done" after the `yield` statement. This means that the code above the
    `yield` statement will be run before each test, and the code below the
    `yield` statement will be run after each test.
    """

    await database.connect()
    # Execute PRAGMA statements to adjust SQLite settings
    # await database.execute("PRAGMA busy_timeout = 30000")
    # Wait up to 30 seconds
    yield
    await database.disconnect()


@pytest.fixture()
async def async_client(client: TestClient) -> AsyncGenerator:
    async with AsyncClient(
        base_url=client.base_url, transport=ASGITransport(app)
    ) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.com", "password": "password1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    assert user
    user_details["id"] = user["id"]
    return user_details


@pytest.fixture()
async def confirmed_user(async_client: AsyncClient, registered_user: dict) -> dict:
    query = (
        user_table.update()
        .where(user_table.c.email == registered_user["email"])
        .values(confirmed=True)
    )
    await database.execute(query)
    return registered_user


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict) -> str:
    response = await async_client.post(
        "/token",
        data={
            "username": confirmed_user["email"],
            "password": confirmed_user["password"],
        },
    )
    return response.json()["access_token"]
