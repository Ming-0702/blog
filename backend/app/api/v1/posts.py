"""博客文章相关 API"""
import re
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.config import settings
from app.models import User, Post, Tag
from app.schemas.post import PostCreate, PostUpdate, PostOut, PostPage, PostListOut
from app.api.deps import get_current_user, get_author_user
from app.utils.response import success, fail
from app.core.config import settings as s

router = APIRouter(prefix="/posts", tags=["博客"])


def strip_markdown(text: str) -> str:
    if not text: return ""
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'#{1,6}\s+', '', text)
    text = re.sub(r'\*{1,3}([^*]+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+?)_{1,3}', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()
    text = re.sub(r'。{2,}', '。', text)
    return text[:200]


def _tags_of(post):
    return [t.name for t in (post.tags or [])]


def _author_of(post):
    a = post.author
    return {"author_name": a.nickname or a.username if a else "", "author_avatar": a.avatar_url or ""}


def _post_list_out(p):
    d = PostListOut.model_validate(p).model_dump(mode="json")
    d.update(_author_of(p))
    d["tags"] = _tags_of(p)
    if d.get("summary"): d["summary"] = strip_markdown(d["summary"])
    return d


def _post_out(p):
    d = PostOut.model_validate(p).model_dump(mode="json")
    d.update(_author_of(p))
    d["tags"] = _tags_of(p)
    if d.get("summary"): d["summary"] = strip_markdown(d["summary"])
    return d


async def _sync_tags(db: AsyncSession, post: Post, tag_names: list[str]):
    """同步文章的标签"""
    if tag_names is None: return
    post.tags.clear()
    for name in tag_names:
        name = name.strip().lower()
        if not name: continue
        slug = re.sub(r'[^a-z0-9一-鿿]+', '-', name).strip('-')
        result = await db.execute(select(Tag).where(Tag.slug == slug))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name, slug=slug)
            db.add(tag)
            await db.flush()
        post.tags.append(tag)


# ===== 路由 =====

@router.get("/tags")
async def list_tags(db: AsyncSession = Depends(get_db)):
    """所有标签"""
    result = await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    return success([{"id": t.id, "name": t.name, "slug": t.slug} for t in tags])


@router.get("/search")
async def search_posts(q: str, db: AsyncSession = Depends(get_db)):
    """全文搜索，返回匹配片段+高亮"""
    if not q.strip(): return success([])
    t = f"%{q}%"
    result = await db.execute(
        select(Post).options(joinedload(Post.author))
        .where(Post.status == "published",
               (Post.title.ilike(t)) | (Post.content.ilike(t)) | (Post.summary.ilike(t)))
        .order_by(desc(Post.created_at)).limit(20)
    )
    posts = result.unique().scalars().all()

    def make_snippets(text, keyword, max_n=3):
        """提取多处匹配上下文"""
        if not text or not keyword: return []
        import re as _re
        kw = _re.escape(keyword)
        results, last_end = [], 0
        for m in _re.finditer(kw, text, _re.IGNORECASE):
            idx = m.start()
            if idx < last_end: continue
            start, end = max(0, idx - 50), min(len(text), idx + len(keyword) + 70)
            snip = text[start:end]
            if start > 0: snip = "..." + snip
            if end < len(text): snip = snip + "..."
            snip = _re.sub(f"({kw})", r"<mark>\1</mark>", snip, flags=_re.IGNORECASE)
            results.append(snip)
            last_end = end
            if len(results) >= max_n: break
        return results

    items = []
    import re as _re
    for p in posts:
        d = _post_list_out(p)
        kw = q.strip()
        kw_lower = kw.lower()
        title_hit = kw_lower in (p.title or "").lower()
        snips = make_snippets(p.content, kw)
        if not snips and p.summary:
            snips = make_snippets(p.summary, kw)
        d["title_match"] = title_hit
        d["snippets"] = snips
        d["match_count"] = len(_re.findall(_re.escape(kw), p.content or "", _re.IGNORECASE))
        d["match_count"] += 1 if title_hit else 0
        items.append(d)
    return success(items)


@router.get("")
async def list_posts(
    page: int = 1, page_size: int = 20, status: str = "published",
    q: str = "", tag: str = "", db: AsyncSession = Depends(get_db),
):
    conditions = [Post.status == status]
    if q:
        t = f"%{q}%"
        conditions.append((Post.title.ilike(t)) | (Post.summary.ilike(t)) | (Post.content.ilike(t)))

    base = select(Post).options(joinedload(Post.author)).where(*conditions)

    if tag:
        base = base.join(Post.tags).where(Tag.slug == tag)

    query = base.order_by(desc(Post.is_pinned), desc(Post.created_at))
    total_query = select(func.count()).select_from(Post).where(*conditions)
    if tag:
        total_query = total_query.join(Post.tags).where(Tag.slug == tag)

    total = (await db.execute(total_query)).scalar()
    posts = (await db.execute(query.offset((page - 1) * page_size).limit(page_size))).unique().scalars().all()

    return success(PostPage(
        items=[_post_list_out(p) for p in posts],
        total=total, page=page, page_size=page_size,
    ).model_dump(mode="json"))


@router.get("/hot")
async def hot_posts(limit: int = 5, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text
    posts = (await db.execute(
        select(Post).options(joinedload(Post.author))
        .where(Post.status == "published")
        .order_by(desc(text("like_count + comment_count"))).limit(limit)
    )).unique().scalars().all()
    return success([_post_list_out(p) for p in posts])


@router.get("/random")
async def random_post(db: AsyncSession = Depends(get_db)):
    post = (await db.execute(
        select(Post).options(joinedload(Post.author))
        .where(Post.status == "published").order_by(func.random()).limit(1)
    )).unique().scalars().first()
    if not post: return fail("还没有文章", status_code=404)
    return success(_post_out(post))


@router.get("/drafts")
async def list_drafts(current_user: User = Depends(get_author_user), db: AsyncSession = Depends(get_db)):
    posts = (await db.execute(
        select(Post).options(joinedload(Post.author))
        .where(Post.status == "draft").order_by(desc(Post.created_at))
    )).unique().scalars().all()
    return success([_post_list_out(p) for p in posts])


from fastapi.responses import Response

@router.get("/rss", include_in_schema=False)
async def rss_feed(db: AsyncSession = Depends(get_db)):
    """RSS 2.0 feed"""
    result = await db.execute(
        select(Post).options(joinedload(Post.author))
        .where(Post.status == "published")
        .order_by(desc(Post.is_pinned), desc(Post.created_at)).limit(20)
    )
    posts = result.unique().scalars().all()
    items = []
    for p in posts:
        aname = p.author.nickname or p.author.username if p.author else "Anonymous"
        items.append(f"""    <item>
      <title>{p.title}</title>
      <link>http://localhost:5173/posts/{p.id}</link>
      <description><![CDATA[{p.summary or strip_markdown(p.content)}]]></description>
      <author>{aname}</author>
      <pubDate>{p.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
      <guid isPermaLink="true">http://localhost:5173/posts/{p.id}</guid>
    </item>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>时不时丢点东西的神秘盒子</title>
<link>http://localhost:5173</link>
<description>偶尔更新，随心记录</description>
<language>zh-CN</language>
{''.join(items)}</channel></rss>"""
    return Response(content=xml, media_type="application/rss+xml")


@router.get("/{post_id}")
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = (await db.execute(
        select(Post).options(joinedload(Post.author)).where(Post.id == post_id)
    )).unique().scalars().first()
    if not post: return fail("文章不存在", status_code=404)
    post.view_count += 1
    await db.commit(); await db.refresh(post)
    post = (await db.execute(
        select(Post).options(joinedload(Post.author)).where(Post.id == post_id)
    )).unique().scalars().first()
    return success(_post_out(post))


@router.post("")
async def create_post(
    data: PostCreate, current_user: User = Depends(get_author_user),
    db: AsyncSession = Depends(get_db),
):
    post = Post(
        title=data.title, content=data.content,
        summary=data.summary or strip_markdown(data.content),
        cover_image=data.cover_image or "",
        status=data.status or "published", is_pinned=data.is_pinned, author_id=current_user.id,
    )
    db.add(post)
    await db.commit(); await db.refresh(post)
    if data.tags:
        await _sync_tags(db, post, data.tags)
        await db.commit(); await db.refresh(post)
    post.author = current_user
    return success(_post_out(post))


@router.put("/{post_id}")
async def update_post(
    post_id: int, data: PostUpdate,
    current_user: User = Depends(get_author_user),
    db: AsyncSession = Depends(get_db),
):
    post = (await db.execute(
        select(Post).options(joinedload(Post.author)).where(Post.id == post_id)
    )).unique().scalars().first()
    if not post: return fail("文章不存在", status_code=404)
    if post.author_id != current_user.id: return fail("无权修改此文章", status_code=403)
    if data.title is not None: post.title = data.title
    if data.content is not None: post.content = data.content
    if data.summary is not None: post.summary = data.summary
    elif data.content is not None: post.summary = strip_markdown(data.content)
    if data.cover_image is not None: post.cover_image = data.cover_image
    if data.status is not None: post.status = data.status
    if data.is_pinned is not None: post.is_pinned = data.is_pinned
    await db.commit()
    if data.tags is not None:
        await _sync_tags(db, post, data.tags)
        await db.commit()
    await db.refresh(post)
    post.author = current_user
    return success(_post_out(post))


@router.delete("/{post_id}")
async def delete_post(post_id: int, current_user: User = Depends(get_author_user), db: AsyncSession = Depends(get_db)):
    post = (await db.execute(select(Post).where(Post.id == post_id))).unique().scalar_one_or_none()
    if not post: return fail("文章不存在", status_code=404)
    if post.author_id != current_user.id: return fail("无权删除此文章", status_code=403)
    await db.delete(post); await db.commit()
    return success(msg="删除成功")


# ===== AI 摘要 =====

@router.post("/generate-summary")
async def generate_summary(
    data: PostCreate,
    current_user: User = Depends(get_author_user),
):
    """调用 AI 生成文章摘要"""
    if not settings.AI_API_KEY:
        return fail("AI 服务未配置（需要 AI_API_KEY）", status_code=400)

    import httpx
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.AI_API_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                json={
                    "model": settings.AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个文章摘要助手。用一句话中文总结文章核心内容，不超过150字。"},
                        {"role": "user", "content": data.content[:3000]},
                    ],
                    "max_tokens": 200,
                    "temperature": 0.7,
                },
            )
            resp.raise_for_status()
            result = resp.json()
            summary = result["choices"][0]["message"]["content"].strip()
            return success({"summary": summary})
    except Exception as e:
        return fail(f"AI 摘要生成失败: {str(e)}", status_code=500)


# ===== 文件上传创建文章 =====

@router.post("/upload")
async def upload_post(
    file: UploadFile = File(...),
    current_user: User = Depends(get_author_user),
    db: AsyncSession = Depends(get_db),
):
    """上传 PDF 或 Markdown 文件创建文章"""
    filename = (file.filename or "").lower()
    raw = await file.read()

    if filename.endswith(".pdf"):
        try:
            from io import BytesIO
            from PyPDF2 import PdfReader
            reader = PdfReader(BytesIO(raw))
            content = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            return fail("PDF 解析需要安装 PyPDF2: pip install PyPDF2", status_code=500)
        except Exception as e:
            return fail(f"PDF 解析失败: {str(e)}", status_code=500)
    elif filename.endswith((".md", ".markdown", ".txt")):
        content = raw.decode("utf-8", errors="replace")
    else:
        return fail("仅支持 PDF / Markdown / TXT 文件", status_code=400)

    if not content.strip():
        return fail("文件内容为空", status_code=400)

    # 文件名作为标题
    title = re.sub(r"\.[^.]+$", "", file.filename or "未命名")
    title = title.replace("-", " ").replace("_", " ")

    post = Post(
        title=title,
        content=content,
        summary=strip_markdown(content),
        status="published",
        author_id=current_user.id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    post.author = current_user
    return success(_post_out(post))
