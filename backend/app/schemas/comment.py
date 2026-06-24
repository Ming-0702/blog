"""评论相关 Pydantic schema"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None


class CommentOut(BaseModel):
    id: int
    content: str
    post_id: int
    author_id: int
    parent_id: Optional[int] = None
    like_count: int
    created_at: datetime
    # 嵌套回复（楼中楼）
    replies: List["CommentOut"] = []

    model_config = {"from_attributes": True}
