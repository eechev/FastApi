import datetime
import logging
from typing import Annotated

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

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def access_token_minutes() -> int:
    return 30


def create_access_token(email: str):
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_minutes()
    )
    jwt_data = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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
        raise credentials_exception
    if not verify_password(password, user["password"]):
        raise credentials_exception
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])

    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except JWTError as e:
        raise credentials_exception from e

    email = payload.get("sub")
    if email is None:
        raise credentials_exception
    user = await get_user(email)
    if user is None:
        raise credentials_exception
    return user
