"""用户相关 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.schemas.user import UserOut, UserUpdate
from app.api.deps import get_current_user
from app.utils.response import success

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from app.utils.response import fail
        return fail("用户不存在", status_code=404)
    return success(UserOut.model_validate(user).model_dump())


@router.put("/me")
async def update_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.bio is not None:
        current_user.bio = data.bio
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    await db.commit()
    await db.refresh(current_user)
    return success(UserOut.model_validate(current_user).model_dump())
