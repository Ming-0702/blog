"""认证相关 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models import User
from app.schemas.user import UserRegister, UserLogin, Token, UserOut
from app.api.deps import get_current_user
from app.utils.response import success, fail

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        return fail("用户名已存在")

    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        return fail("邮箱已被注册")

    # 创建用户
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        nickname=data.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 生成令牌
    token = create_access_token({"user_id": user.id})
    return success({
        "user": UserOut.model_validate(user).model_dump(),
        "access_token": token,
    })


@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    # 支持用户名或邮箱登录
    result = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.username)
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        return fail("用户名或密码错误", status_code=status.HTTP_401_UNAUTHORIZED)

    token = create_access_token({"user_id": user.id})
    return success({
        "user": UserOut.model_validate(user).model_dump(),
        "access_token": token,
    })


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return success(UserOut.model_validate(current_user).model_dump())
