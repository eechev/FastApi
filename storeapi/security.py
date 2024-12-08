import logging

from passlib.context import CryptContext

from storeapi.database import database, user_table

logger = logging.getLogger(__name__)


pwd_context = CryptContext(schemes=["bcrypt"])


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
