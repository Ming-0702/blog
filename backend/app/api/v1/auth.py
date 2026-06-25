"""认证相关 API"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
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
        "user": UserOut.model_validate(user).model_dump(mode="json"),
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
        "user": UserOut.model_validate(user).model_dump(mode="json"),
        "access_token": token,
    })


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return success(UserOut.model_validate(current_user).model_dump(mode="json"))


# ===== GitHub OAuth =====

@router.get("/github/login")
async def github_login():
    """返回 GitHub OAuth 授权 URL"""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
    )
    return success({"auth_url": github_auth_url})


@router.get("/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    """GitHub OAuth 回调：用 code 换 token、获取用户信息、创建/登录用户"""
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        return fail("GitHub OAuth 未配置", status_code=400)

    # 1. 用 code 换 access_token
    async with AsyncClient() as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token or "error" in token_data:
            return fail("GitHub 授权失败", status_code=400)

        # 2. 获取 GitHub 用户信息
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        gh_user = user_res.json()

    github_id = gh_user["id"]
    gh_username = gh_user.get("login", "")
    gh_email = gh_user.get("email") or f"{gh_username}@github.user"
    gh_avatar = gh_user.get("avatar_url", "")

    # 3. 查找或创建用户
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if not user:
        # 检查邮箱是否已存在（关联已有账号）
        result = await db.execute(select(User).where(User.email == gh_email))
        user = result.scalar_one_or_none()
        if user:
            user.github_id = github_id
            user.github_username = gh_username
            if not user.avatar_url:
                user.avatar_url = gh_avatar
        else:
            # 创建新用户
            user = User(
                username=f"gh_{gh_username}",
                email=gh_email,
                hashed_password=hash_password(os.urandom(16).hex()),
                nickname=gh_username,
                avatar_url=gh_avatar,
                github_id=github_id,
                github_username=gh_username,
            )
            db.add(user)

    await db.commit()
    await db.refresh(user)

    # 4. 签发 JWT
    token = create_access_token({"user_id": user.id})
    return success({
        "user": UserOut.model_validate(user).model_dump(mode="json"),
        "access_token": token,
    })
