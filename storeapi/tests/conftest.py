"""
This is a fixture file
"""

from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from storeapi.main import app
from storeapi.routers.post import comment_table, post_table


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

    post_table.clear()
    comment_table.clear()
    yield


@pytest.fixture()
async def async_client(client: TestClient) -> AsyncGenerator:
    async with AsyncClient(
        base_url=client.base_url, transport=ASGITransport(app)
    ) as ac:
        yield ac
