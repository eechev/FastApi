import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from storeapi.database import database
from storeapi.logging_conf import configure_logging
from storeapi.routers.post import router as post_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting up...")
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.include_router(post_router)
