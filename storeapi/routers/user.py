import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from storeapi.database import database, user_table
from storeapi.models.user import UserIn
from storeapi.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user,
)

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserIn):
    logger.info("Registering user", extra={"email": user.email})
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists",
        )

    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=hashed_password)
    logger.debug(query)
    await database.execute(query)
    return {"detail": "User successfully created"}


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    authenticated_user = await authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(authenticated_user["email"])
    return {"access_token": access_token, "token_type": "bearer"}
