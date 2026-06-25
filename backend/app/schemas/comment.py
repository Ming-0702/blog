"""评论相关 Pydantic schema"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    content: str


class CommentOut(BaseModel):
    id: int
    content: str
    post_id: int
    author_id: int
    author_name: str = ""
    author_avatar: str = ""
    parent_id: Optional[int] = None
    like_count: int
    created_at: datetime
    replies: List["CommentOut"] = []

    model_config = {"from_attributes": True}
