"""评论相关 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models import User, Post, Comment
from app.schemas.comment import CommentCreate, CommentUpdate, CommentOut
from app.api.deps import get_current_user
from app.utils.response import success, fail

router = APIRouter(prefix="/comments", tags=["评论"])


def _c_out(c, author_name="", author_avatar=""):
    return CommentOut(
        id=c.id, content=c.content, post_id=c.post_id,
        author_id=c.author_id, parent_id=c.parent_id,
        like_count=c.like_count, created_at=c.created_at,
        author_name=author_name, author_avatar=author_avatar, replies=[],
    ).model_dump(mode="json")


@router.get("/post/{post_id}")
async def list_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    all_comments = (await db.execute(
        select(Comment).options(joinedload(Comment.author))
        .where(Comment.post_id == post_id).order_by(Comment.created_at)
    )).unique().scalars().all()

    author_map = {}
    for c in all_comments:
        a = c.author
        author_map[c.author_id] = {
            "name": a.nickname or a.username if a else "",
            "avatar": a.avatar_url or "",
        }

    top = [c for c in all_comments if c.parent_id is None]
    replies = [c for c in all_comments if c.parent_id is not None]

    reply_map: dict = {}
    for r in replies:
        m = author_map.get(r.author_id, {})
        out = _c_out(r, m.get("name", ""), m.get("avatar", ""))
        reply_map.setdefault(r.parent_id, []).append(out)

    return success([
        {**_c_out(c, author_map.get(c.author_id, {}).get("name", ""), author_map.get(c.author_id, {}).get("avatar", "")),
         "replies": reply_map.get(c.id, [])}
        for c in top
    ])


@router.post("")
async def create_comment(
    post_id: int, data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not post: return fail("文章不存在", status_code=404)

    parent = None
    if data.parent_id:
        parent = (await db.execute(select(Comment).where(Comment.id == data.parent_id))).scalar_one_or_none()
        if not parent: return fail("父评论不存在", status_code=404)

    comment = Comment(
        content=data.content, post_id=post_id,
        author_id=current_user.id, parent_id=data.parent_id,
    )
    db.add(comment)
    post.comment_count += 1
    await db.commit()
    await db.refresh(comment)

    aname = current_user.nickname or current_user.username
    aavatar = current_user.avatar_url or ""

    if post.author_id != current_user.id:
        from app.api.v1.websocket import notify_user
        await notify_user(post.author_id, "new_comment", {
            "post_id": post_id, "comment_id": comment.id,
            "from_user": aname, "content_preview": data.content[:50],
        })
    if data.parent_id and parent and parent.author_id != current_user.id:
        await notify_user(parent.author_id, "new_reply", {
            "post_id": post_id, "comment_id": comment.id,
            "from_user": aname, "content_preview": data.content[:50],
        })

    return success(_c_out(comment, aname, aavatar))


@router.put("/{comment_id}")
async def update_comment(
    comment_id: int, data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = (await db.execute(
        select(Comment).options(joinedload(Comment.author)).where(Comment.id == comment_id)
    )).unique().scalars().first()
    if not comment: return fail("评论不存在", status_code=404)
    if comment.author_id != current_user.id: return fail("无权编辑此评论", status_code=403)

    comment.content = data.content
    await db.commit()
    await db.refresh(comment)

    return success(_c_out(comment, current_user.nickname or current_user.username,
                         current_user.avatar_url or ""))


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = (await db.execute(select(Comment).where(Comment.id == comment_id))).scalar_one_or_none()
    if not comment: return fail("评论不存在", status_code=404)
    if comment.author_id != current_user.id: return fail("无权删除此评论", status_code=403)

    reply_count = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.parent_id == comment_id)
    )
    deleted_total = 1 + (reply_count.scalar() or 0)

    await db.delete(comment)
    post = (await db.execute(select(Post).where(Post.id == comment.post_id))).scalar_one_or_none()
    if post:
        post.comment_count = max(0, post.comment_count - deleted_total)
    await db.commit()

    return success(msg="删除成功")
