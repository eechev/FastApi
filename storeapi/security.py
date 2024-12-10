import datetime
import logging
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from storeapi.database import database, user_table

logger = logging.getLogger(__name__)

SECRET_KEY = "5f4dcc3b5aa765d61d8327deb882cf995f4dcc3b5aa765d61d8327deb882cf99"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"])


def create_credentials_exception(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def access_token_expire_minutes() -> int:
    return 30


def confirmation_token_expire_minutes() -> int:
    return 1440


def create_access_token(email: str):
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_confirmation_token(email: str):
    logger.debug("Creating confirmation token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirmation_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "confirmation"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_subject_for_token_type(
    token: str, token_type: Literal["access", "confirmation"]
) -> str:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])

    except ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired") from e
    except JWTError as e:
        raise create_credentials_exception("Invalid token") from e

    sub_email = payload.get("sub")
    if not sub_email:
        raise create_credentials_exception("Tokens is missing 'sub' field")

    type = payload.get("type")
    if type != token_type:
        raise create_credentials_exception(
            "Token has incorrect type, expected '{}'".format(token_type)
        )

    return sub_email


def get_password_hash(password: str) -> str:
    logger.debug("Hashing password...")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug("Verifying password...")
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    logger.debug("Fetching user from database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    return await database.fetch_one(query)


async def authenticate_user(email: str, password: str):
    logger.debug(
        "Authenticating user",
        extra={
            "email": email,
        },
    )
    user = await get_user(email)
    if not user:
        raise create_credentials_exception("Incorrect username or password")
    if not verify_password(password, user["password"]):
        raise create_credentials_exception("Incorrect username or password")
    if not user["confirmed"]:
        raise create_credentials_exception("User has not confirmed email")
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    email = get_subject_for_token_type(token, "access")

    user = await get_user(email)
    if user is None:
        raise create_credentials_exception("Could not find user for this token")

    return user
