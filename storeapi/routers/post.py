import logging

from fastapi import APIRouter, HTTPException, status

from storeapi.database import comment_table, database, post_table
from storeapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)

router = APIRouter()

logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    logger.info("Finding post with id {}".format(post_id))
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(query)
    post = await database.fetch_one(query)
    if not post:
        logger.error("Post not found with id {}".format(post_id))
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return post


@router.post("/post", response_model=UserPost, status_code=status.HTTP_201_CREATED)
async def create_post(post: UserPostIn):
    logger.info("Creating post")
    data = post.model_dump()
    query = post_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post", response_model=list[UserPost])
async def get_all_posts():
    logger.info("Getting all posts")
    query = post_table.select()
    logger.debug(query)
    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(comment: CommentIn):
    logger.info("Creating comment for post id {}".format(comment.post_id))
    await find_post(comment.post_id)
    data = comment.model_dump()
    query = comment_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_post_comments(post_id: int):
    logger.info("Getting comments for post {}".format(post_id))
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug(query)
    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info("Getting post with comments for post {}".format(post_id))
    return {
        "post": await find_post(post_id),
        "comments": await get_post_comments(post_id),
    }
