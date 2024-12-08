import logging

from storeapi.database import database, user_table

logger = logging.getLogger(__name__)


async def get_user(email: str):
    logger.debug("Fetching user from database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    return await database.fetch_one(query)
