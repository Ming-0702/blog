"""博客文章相关 Pydantic schema"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class PostCreate(BaseModel):
    title: str
    content: str
    summary: Optional[str] = ""
    cover_image: Optional[str] = ""
    status: Optional[str] = "published"


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = None


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    summary: str
    cover_image: str
    status: str
    view_count: int
    like_count: int
    comment_count: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostListOut(BaseModel):
    """列表展示时省略完整 content"""
    id: int
    title: str
    summary: str
    cover_image: str
    status: str
    view_count: int
    like_count: int
    comment_count: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostPage(BaseModel):
    items: List[PostListOut]
    total: int
    page: int
    page_size: int
