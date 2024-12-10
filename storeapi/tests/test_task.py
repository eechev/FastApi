import httpx
import pytest
from databases import Database
from fastapi import status
from httpx import Request

from storeapi.database import post_table
from storeapi.tasks import (
    APIResponseError,
    _generate_cute_creature_api,
    generate_and_add_to_post,
    send_simple_email,
)


@pytest.mark.anyio
async def test_send_simple_email(mock_httpx_client):
    await send_simple_email("test@example.com", "Test Subject", "Test Body")
    mock_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_simple_email_api_error(mock_httpx_client):
    request = Request(method="POST", url="//")
    mock_response = httpx.Response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="", request=request
    )
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(APIResponseError):
        await send_simple_email("test@example.com", "Test Subject", "Test Body")


@pytest.mark.anyio
async def test_generate_cute_creature_api_success(mock_httpx_client):
    json_data = {"output_url": "https://example.com/cute-creature.jpg"}

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_200_OK,
        json=json_data,
        request=Request(method="POST", url="//"),
    )

    result = await _generate_cute_creature_api("A sad cat.")

    assert result == json_data


@pytest.mark.anyio
async def test_generate_cute_creature_api_error(mock_httpx_client):
    request = Request(method="POST", url="//")
    mock_response = httpx.Response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="", request=request
    )
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(
        APIResponseError, match="API request failed with status code 500"
    ):
        await _generate_cute_creature_api("A sad cat.")


@pytest.mark.anyio
async def test_generate_cute_creature_api_json_error(mock_httpx_client):
    request = Request(method="POST", url="//")
    mock_response = httpx.Response(
        status_code=status.HTTP_200_OK, content="Not JSON", request=request
    )
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(APIResponseError, match="API response parsing failed"):
        await _generate_cute_creature_api("A sad cat.")


@pytest.mark.anyio
async def test_generate_and_add_to_post_success(
    mock_httpx_client, created_post: dict, confirmed_user: dict, db: Database
):
    json_data = {"output_url": "https://example.com/cute-creature.jpg"}

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_200_OK,
        json=json_data,
        request=Request(method="POST", url="//"),
    )

    await generate_and_add_to_post(
        confirmed_user["email"],
        created_post["id"],
        "/post/1",
        db,
        "A cute cat sitting on a chair.",
    )

    query = post_table.select().where(post_table.c.id == created_post["id"])
    updated_post = await db.fetch_one(query)
    assert updated_post
    assert updated_post["image_url"] == json_data["output_url"]
