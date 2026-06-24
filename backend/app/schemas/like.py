"""点赞相关 Pydantic schema"""
from pydantic import BaseModel


class LikeCreate(BaseModel):
    target_type: str  # "post" | "comment"
    target_id: int


class LikeOut(BaseModel):
    id: int
    user_id: int
    target_type: str
    target_id: int

    model_config = {"from_attributes": True}
