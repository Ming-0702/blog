"""博客文章相关 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.models import User, Post
from app.schemas.post import PostCreate, PostUpdate, PostOut, PostPage, PostListOut
from app.api.deps import get_current_user
from app.utils.response import success, fail

router = APIRouter(prefix="/posts", tags=["博客"])


@router.get("")
async def list_posts(
    page: int = 1,
    page_size: int = 20,
    status: str = "published",
    db: AsyncSession = Depends(get_db),
):
    query = select(Post).where(Post.status == status).order_by(desc(Post.created_at))
    total_query = select(func.count()).select_from(Post).where(Post.status == status)

    total = (await db.execute(total_query)).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    posts = result.scalars().all()

    return success(PostPage(
        items=[PostListOut.model_validate(p).model_dump() for p in posts],
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump())


@router.get("/{post_id}")
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return fail("文章不存在", status_code=404)

    # 增加阅读计数
    post.view_count += 1
    await db.commit()
    await db.refresh(post)

    return success(PostOut.model_validate(post).model_dump())


@router.post("")
async def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post = Post(
        title=data.title,
        content=data.content,
        summary=data.summary or data.content[:200],
        cover_image=data.cover_image or "",
        status=data.status or "published",
        author_id=current_user.id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return success(PostOut.model_validate(post).model_dump())


@router.put("/{post_id}")
async def update_post(
    post_id: int,
    data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return fail("文章不存在", status_code=404)
    if post.author_id != current_user.id:
        return fail("无权修改此文章", status_code=403)

    if data.title is not None:
        post.title = data.title
    if data.content is not None:
        post.content = data.content
    if data.summary is not None:
        post.summary = data.summary
    if data.cover_image is not None:
        post.cover_image = data.cover_image
    if data.status is not None:
        post.status = data.status

    await db.commit()
    await db.refresh(post)
    return success(PostOut.model_validate(post).model_dump())


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return fail("文章不存在", status_code=404)
    if post.author_id != current_user.id:
        return fail("无权删除此文章", status_code=403)

    await db.delete(post)
    await db.commit()
    return success(msg="删除成功")
