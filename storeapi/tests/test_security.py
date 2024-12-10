import pytest
from jose import jwt

from storeapi import security


def test_access_token_minutes():
    assert security.access_token_expire_minutes() == 30


def test_confirmation_token_minutes():
    assert security.confirmation_token_expire_minutes() == 1440


def test_create_access_token():
    token = security.create_access_token("test@example.com")
    assert token
    assert {"sub": "test@example.com", "type": "access"}.items() <= jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


def test_create_confirmation_token():
    token = security.create_confirmation_token("test@example.com")
    assert token
    assert {"sub": "test@example.com", "type": "confirmation"}.items() <= jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


def test_get_subject_for_token_type_valid_confirmation():
    email = "test@example.com"
    token = security.create_confirmation_token(email)
    assert email == security.get_subject_for_token_type(token, "confirmation")


def test_get_subject_for_token_type_valid_access():
    email = "test@example.com"
    token = security.create_access_token(email)
    assert email == security.get_subject_for_token_type(token, "access")


def test_get_subject_for_token_type_expired(mocker):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token("test@example.com")
    with pytest.raises(security.HTTPException) as exc_ifo:
        security.get_subject_for_token_type(token, "access")

    assert "Token has expired" in exc_ifo.value.detail


def test_get_subject_for_invalid_token():
    token = "invalid token"
    with pytest.raises(security.HTTPException) as exc_ifo:
        security.get_subject_for_token_type(token, "access")

    assert "Invalid token" in exc_ifo.value.detail


def test_get_subject_with_missing_sub_token():
    email = "test@example.com"
    token = security.create_access_token(email)
    payload = jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    )
    del payload["sub"]
    token = jwt.encode(payload, key=security.SECRET_KEY, algorithm=security.ALGORITHM)
    with pytest.raises(security.HTTPException) as exc_ifo:
        security.get_subject_for_token_type(token, "access")

    assert "Tokens is missing 'sub' field" in exc_ifo.value.detail


def test_get_subject_with_incorrect_token_type():
    email = "test@example.com"
    token = security.create_access_token(email)
    with pytest.raises(security.HTTPException) as exc_ifo:
        security.get_subject_for_token_type(token, "confirmation")

    assert "Token has incorrect type, expected 'confirmation'" in exc_ifo.value.detail


def test_password_hashing():
    password = "password1234"
    hashed_password = security.get_password_hash(password)
    assert security.verify_password(password, hashed_password)


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])
    assert user is not None
    assert user["email"] == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example.com")
    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(confirmed_user: dict):
    user = await security.authenticate_user(
        confirmed_user["email"], confirmed_user["password"]
    )
    assert user
    assert user["email"] == confirmed_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test@example.com", "password1234")


@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)
    assert user["email"] == registered_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid token")


@pytest.mark.anyio
async def test_get_current_user_wrong_token_type(registered_user: dict):
    token = security.create_confirmation_token(registered_user["email"])
    with pytest.raises(security.HTTPException):
        await security.get_current_user(token)
