"""用户相关 API"""
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.schemas.user import UserOut, UserUpdate
from app.api.deps import get_current_user
from app.utils.response import success, fail

router = APIRouter(prefix="/users", tags=["用户"])
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "avatars"


@router.get("/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from app.utils.response import fail
        return fail("用户不存在", status_code=404)
    return success(UserOut.model_validate(user).model_dump(mode="json"))


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
    return success(UserOut.model_validate(current_user).model_dump(mode="json"))


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传用户头像，最大 2MB，支持 JPG/PNG/GIF/WebP"""
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in ALLOWED_TYPES:
        return fail("仅支持 JPG/PNG/GIF/WebP 格式", status_code=400)

    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        return fail("头像大小不能超过 2MB", status_code=400)

    ext = (file.filename or "avatar.png").rsplit(".", 1)[-1].lower()
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / filename

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)

    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(current_user)

    return success({
        "avatar_url": avatar_url,
        "user": UserOut.model_validate(current_user).model_dump(mode="json"),
    })
