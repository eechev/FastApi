import pytest
from fastapi import status
from httpx import AsyncClient

from storeapi.security import create_access_token
from storeapi.tests.helpers import create_comment, create_post, like_post


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    return await create_comment(
        "Test Comment", created_post["id"], logged_in_token, async_client
    )


@pytest.fixture()
def mock_generate_cute_creature_api(mocker):
    return mocker.patch(
        "storeapi.tasks._generate_cute_creature_api",
        return_value={"output_url": "http://example.com/cute-creature.jpg"},
    )


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str
):
    print("testing create post")
    body = "Test Post"

    response = await async_client.post(
        "/post",
        json={"body": body, "header": "header"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert {
        "id": 1,
        "body": body,
        "user_id": confirmed_user["id"],
        "image_url": None,
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_with_prompt(
    async_client: AsyncClient,
    confirmed_user: dict,
    logged_in_token: str,
    mock_generate_cute_creature_api,
):
    print("testing create post with prompt")
    body = "Test Post"

    response = await async_client.post(
        "/post?prompt=cat",
        json={"body": body, "header": "header"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert {
        "id": 1,
        "body": body,
        "user_id": confirmed_user["id"],
        "image_url": None,
    }.items() <= response.json().items()

    mock_generate_cute_creature_api.assert_called()


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    confirmed_user: dict,
    logged_in_token: str,
):
    body = "Test Comment"
    response = await async_client.post(
        "/comment",
        json={
            "body": body,
            "post_id": created_post["id"],
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": confirmed_user["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.anyio
async def test_create_post_without_body(
    async_client: AsyncClient, logged_in_token: str
):
    response = await async_client.post(
        "/post", json={}, headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_post_without_token(async_client: AsyncClient):
    response = await async_client.post("/post", json={"body": "Test Post"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_create_post_with_expired_token(
    async_client: AsyncClient, registered_user: dict, mocker
):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = create_access_token(registered_user["email"])
    response = await async_client.post(
        "/post",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/post")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{**created_post, "likes": 0}]


@pytest.mark.anyio
@pytest.mark.parametrize("sorting, expected_order", [("new", [2, 1]), ("old", [1, 2])])
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    await create_post("Test Post 1", logged_in_token, async_client)
    await create_post("Test Post 2", logged_in_token, async_client)
    response = await async_client.get("/post", params={"sorting": sorting})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_sort_likes(
    async_client: AsyncClient, logged_in_token: str
):
    await create_post("Test Post 1", logged_in_token, async_client)
    await create_post("Test Post 2", logged_in_token, async_client)
    await like_post(1, async_client, logged_in_token)

    response = await async_client.get("/post", params={"sorting": "most_likes"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    post_ids = [post["id"] for post in data]
    assert post_ids == [1, 2]


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "post": {**created_post, "likes": 0},
        "comments": [created_comment],
    }


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}/comment")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_post_with_empty_comments(
    async_client: AsyncClient, created_post: dict
):
    response = await async_client.get(f"/post/{created_post['id']}/comment")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_not_found(async_client: AsyncClient):
    response = await async_client.get("/post/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_get_comments_on_post_that_does_not_exist(
    async_client: AsyncClient, created_post: dict
):
    response = await async_client.get("/post/2/comment")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_with_comments_post_not_found(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get("/post/2")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_get_all_posts_wrong_sorting(async_client: AsyncClient):
    response = await async_client.get("/post", params={"sorting": "wrong"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
