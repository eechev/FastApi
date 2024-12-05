from pydantic import BaseModel

"""_summary_

Models

"""


class UserPostIn(BaseModel):
    body: str


class UserPost(UserPostIn):
    id: int


class CommentIn(BaseModel):
    body: str
    post_id: int


class Comment(CommentIn):
    id: int


class UserPostWithComments(BaseModel):
    post: UserPost
    comments: list[Comment]
