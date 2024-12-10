import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from storeapi.database import comment_table, database, like_table, post_table
from storeapi.models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
    UserPostWithLikes,
)
from storeapi.models.user import User
from storeapi.security import get_current_user
from storeapi.tasks import generate_and_add_to_post

router = APIRouter()

logger = logging.getLogger(__name__)


class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


select_post_and_likes = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


async def find_post(post_id: int):
    logger.info("Finding post with id {}".format(post_id))
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(query)
    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Post with id {} not found".format(post_id)
        )
    return post


@router.post("/post", response_model=UserPost, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: UserPostIn,
    current_user: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    request: Request,
    prompt: str | None = None,
):
    logger.info("Creating post")
    data = {**post.model_dump(), "user_id": current_user.id}
    query = post_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)

    if prompt:
        background_tasks.add_task(
            generate_and_add_to_post,
            current_user.email,
            last_record_id,
            str(request.url_for("get_post_with_comments", post_id=last_record_id)),
            database,
            prompt,
        )

    return {**data, "id": last_record_id}


@router.get("/post", response_model=list[UserPostWithLikes])
async def get_all_posts(sorting: PostSorting = PostSorting.new):
    logger.info("Getting all posts")

    match sorting:
        case PostSorting.new:
            query = select_post_and_likes.order_by(post_table.c.id.desc())
        case PostSorting.old:
            query = select_post_and_likes.order_by(post_table.c.id.asc())
        case PostSorting.most_likes:
            query = select_post_and_likes.order_by(sqlalchemy.desc("likes"))

    logger.debug(query)
    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating comment for post id {}".format(comment.post_id))
    await find_post(comment.post_id)
    data = {**comment.model_dump(), "user_id": current_user.id}
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

    query = select_post_and_likes.where(post_table.c.id == post_id)
    logger.debug(query)
    post = await database.fetch_one(query)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post with id {} not found".format(post_id),
        )

    return {
        "post": post,
        "comments": await get_post_comments(post_id),
    }


@router.post("/like", response_model=PostLike, status_code=status.HTTP_201_CREATED)
async def post_like(
    like: PostLikeIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating like for post id {}".format(like.post_id))
    post = await find_post(like.post_id)
    if not post:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Post with id {} not found".format(like.post_id)
        )
    data = {**like.model_dump(), "user_id": current_user.id}
    query = like_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}
