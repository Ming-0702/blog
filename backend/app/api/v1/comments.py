"""评论相关 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.models import User, Post, Comment
from app.schemas.comment import CommentCreate, CommentOut
from app.api.deps import get_current_user
from app.utils.response import success, fail

router = APIRouter(prefix="/comments", tags=["评论"])


@router.get("/post/{post_id}")
async def list_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    """获取文章的所有评论（含楼中楼回复）"""
    # 获取顶级评论（parent_id 为 NULL）
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .order_by(desc(Comment.created_at))
    )
    top_comments = result.scalars().all()

    # 获取所有回复
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id, Comment.parent_id.isnot(None))
        .order_by(Comment.created_at)
    )
    replies = result.scalars().all()

    # 组装回复到对应的父评论
    reply_map: dict[int, list[CommentOut]] = {}
    for reply in replies:
        reply_out = CommentOut(
            id=reply.id, content=reply.content, post_id=reply.post_id,
            author_id=reply.author_id, parent_id=reply.parent_id,
            like_count=reply.like_count, created_at=reply.created_at, replies=[]
        )
        pid = reply.parent_id
        if pid not in reply_map:
            reply_map[pid] = []
        reply_map[pid].append(reply_out)

    comments_out = []
    for c in top_comments:
        co = CommentOut(
            id=c.id, content=c.content, post_id=c.post_id,
            author_id=c.author_id, parent_id=c.parent_id,
            like_count=c.like_count, created_at=c.created_at,
            replies=reply_map.get(c.id, []),
        )
        comments_out.append(co)

    return success([co.model_dump() for co in comments_out])


@router.post("")
async def create_comment(
    post_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 验证文章存在
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return fail("文章不存在", status_code=404)

    # 如果是回复，验证父评论存在
    if data.parent_id:
        result = await db.execute(select(Comment).where(Comment.id == data.parent_id))
        parent = result.scalar_one_or_none()
        if not parent:
            return fail("父评论不存在", status_code=404)

    comment = Comment(
        content=data.content,
        post_id=post_id,
        author_id=current_user.id,
        parent_id=data.parent_id,
    )
    db.add(comment)

    # 更新文章评论计数
    post.comment_count += 1
    await db.commit()
    await db.refresh(comment)

    return success(CommentOut.model_validate(comment).model_dump())


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        return fail("评论不存在", status_code=404)
    if comment.author_id != current_user.id:
        return fail("无权删除此评论", status_code=403)

    await db.delete(comment)
    # 更新文章评论计数
    post_result = await db.execute(select(Post).where(Post.id == comment.post_id))
    post = post_result.scalar_one_or_none()
    if post:
        post.comment_count -= 1
    await db.commit()

    return success(msg="删除成功")
