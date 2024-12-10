import httpx
import pytest
from httpx import Request

from storeapi.tasks import APIResponseError, send_simple_email


@pytest.mark.anyio
async def test_send_simple_email(mock_httpx_client):
    await send_simple_email("test@example.com", "Test Subject", "Test Body")
    mock_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_simple_email_api_error(mock_httpx_client):
    request = Request(method="POST", url="//")
    mock_response = httpx.Response(status_code=500, content="", request=request)
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(APIResponseError):
        await send_simple_email("test@example.com", "Test Subject", "Test Body")
