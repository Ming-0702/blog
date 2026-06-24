"""点赞相关 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models import User, Post, Comment, Like
from app.schemas.like import LikeCreate
from app.api.deps import get_current_user
from app.utils.response import success, fail

router = APIRouter(prefix="/likes", tags=["点赞"])


@router.post("")
async def toggle_like(
    data: LikeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """切换点赞状态（已赞则取消，未赞则点赞）"""
    # 验证目标存在
    if data.target_type == "post":
        result = await db.execute(select(Post).where(Post.id == data.target_id))
        target = result.scalar_one_or_none()
    elif data.target_type == "comment":
        result = await db.execute(select(Comment).where(Comment.id == data.target_id))
        target = result.scalar_one_or_none()
    else:
        return fail("无效的点赞类型")

    if not target:
        return fail("目标不存在", status_code=404)

    # 检查是否已点赞
    result = await db.execute(
        select(Like).where(
            and_(
                Like.user_id == current_user.id,
                Like.target_type == data.target_type,
                Like.target_id == data.target_id,
            )
        )
    )
    existing_like = result.scalar_one_or_none()

    if existing_like:
        # 取消点赞
        await db.delete(existing_like)
        target.like_count -= 1
        await db.commit()
        return success({"liked": False, "like_count": target.like_count})
    else:
        # 添加点赞
        like = Like(
            user_id=current_user.id,
            target_type=data.target_type,
            target_id=data.target_id,
        )
        db.add(like)
        target.like_count += 1
        await db.commit()
        return success({"liked": True, "like_count": target.like_count})


@router.get("/status")
async def get_like_status(
    target_type: str,
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检查当前用户是否已点赞"""
    result = await db.execute(
        select(Like).where(
            and_(
                Like.user_id == current_user.id,
                Like.target_type == target_type,
                Like.target_id == target_id,
            )
        )
    )
    liked = result.scalar_one_or_none() is not None
    return success({"liked": liked})
