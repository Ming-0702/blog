"""
MCP Server - 让 AI Agent 管理你的博客

通过 MCP 协议暴露博客功能，AI Agent（如 Claude Code）可以直接：
- 查看/搜索文章
- 创建/编辑/删除文章
- 管理评论
- 查看用户信息

启动方式：
    python -m app.mcp_server
"""
import sys
from pathlib import Path

# 确保能正确导入 app 包
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from typing import Optional
from mcp.server.fastmcp import FastMCP
from sqlalchemy import select, func, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import hash_password
from app.models import User, Post, Comment, Like, Tag
from app.models.digest import NewsDigest
from app.models.trending import TrendingRepo
from app.models.paper import PaperDigest

# 创建 MCP Server
mcp = FastMCP("MyBlog MCP Server", instructions="MyBlog 博客管理工具 - AI Agent 可通过此服务器管理博客内容")


# ===== 工具函数 =====
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


# ===== MCP Tools =====

@mcp.tool(description="获取博客文章列表，支持分页和状态过滤")
async def list_posts(page: int = 1, page_size: int = 20, status: str = "published") -> str:
    """获取文章列表"""
    async with async_session() as db:
        query = select(Post).where(Post.status == status).order_by(Post.created_at.desc())
        total_query = select(func.count()).select_from(Post).where(Post.status == status)
        total = (await db.execute(total_query)).scalar()
        result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
        posts = result.scalars().all()

        lines = [f"共 {total} 篇文章（第 {page}/{max(1, (total + page_size - 1) // page_size)} 页）", ""]
        for p in posts:
            lines.append(f"- [{p.id}] {p.title}")
            lines.append(f"  作者: {p.author_id}  ❤️ {p.like_count}  💬 {p.comment_count}  👁️ {p.view_count}")
            lines.append(f"  {p.created_at.strftime('%Y-%m-%d %H:%M')}")
            if p.summary:
                lines.append(f"  📝 {p.summary[:100]}")
            lines.append("")
        return "\n".join(lines)


@mcp.tool(description="根据文章 ID 获取单篇文章的详细内容")
async def get_post(post_id: int) -> str:
    """获取文章详情"""
    async with async_session() as db:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            return "❌ 文章不存在"

        post.view_count += 1
        await db.commit()

        return (
            f"# {post.title}\n\n"
            f"**作者ID**: {post.author_id}  |  **状态**: {post.status}\n"
            f"**❤️ {post.like_count}**  **💬 {post.comment_count}**  **👁️ {post.view_count}**\n"
            f"**创建时间**: {post.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"---\n\n{post.content}"
        )


@mcp.tool(description="搜索文章标题和内容，支持关键词匹配")
async def search_posts(keyword: str, page: int = 1, page_size: int = 10) -> str:
    """搜索文章"""
    async with async_session() as db:
        query = (
            select(Post)
            .where(Post.status == "published")
            .where(or_(Post.title.ilike(f"%{keyword}%"), Post.content.ilike(f"%{keyword}%")))
            .order_by(Post.created_at.desc())
        )
        total_query = (
            select(func.count())
            .select_from(Post)
            .where(Post.status == "published")
            .where(or_(Post.title.ilike(f"%{keyword}%"), Post.content.ilike(f"%{keyword}%")))
        )
        total = (await db.execute(total_query)).scalar()
        result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
        posts = result.scalars().all()

        lines = [f'🔍 搜索 "{keyword}" 共找到 {total} 篇', ""]
        for p in posts:
            lines.append(f"- [{p.id}] {p.title}")
            lines.append(f"  ❤️ {p.like_count}  💬 {p.comment_count}")
            lines.append("")
        if not posts:
            lines.append("(无结果)")
        return "\n".join(lines)


@mcp.tool(description="发布一篇新文章（需要提供用户名和密码进行鉴权）")
async def create_post(
    username: str,
    password: str,
    title: str,
    content: str,
    summary: Optional[str] = "",
) -> str:
    """创建文章（需鉴权）"""
    async with async_session() as db:
        # 验证用户
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            return "❌ 用户名或密码错误"

        from app.core.security import verify_password
        if not verify_password(password, user.hashed_password):
            return "❌ 用户名或密码错误"

        # 创建文章
        post = Post(
            title=title,
            content=content,
            summary=summary or content[:200],
            author_id=user.id,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)

        return f"✅ 文章发布成功！\n文章ID: {post.id}\n标题: {post.title}"


@mcp.tool(description="更新已有文章的内容（需要文章作者的用户名和密码进行鉴权）")
async def update_post(
    post_id: int,
    username: str,
    password: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    summary: Optional[str] = None,
) -> str:
    """更新文章（需作者鉴权）"""
    async with async_session() as db:
        # 验证用户
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            return "❌ 用户名或密码错误"

        from app.core.security import verify_password
        if not verify_password(password, user.hashed_password):
            return "❌ 用户名或密码错误"

        # 查找文章
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            return "❌ 文章不存在"
        if post.author_id != user.id:
            return "❌ 只有作者才能修改文章"

        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        if summary is not None:
            post.summary = summary

        await db.commit()
        return f"✅ 文章已更新: {post.title}"


@mcp.tool(description="删除一篇文章（需要文章作者的用户名和密码进行鉴权）")
async def delete_post(post_id: int, username: str, password: str) -> str:
    """删除文章（需作者鉴权）"""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            return "❌ 用户名或密码错误"

        from app.core.security import verify_password
        if not verify_password(password, user.hashed_password):
            return "❌ 用户名或密码错误"

        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            return "❌ 文章不存在"
        if post.author_id != user.id:
            return "❌ 只有作者才能删除文章"

        await db.delete(post)
        await db.commit()
        return f"✅ 文章已删除: {post.title}"


@mcp.tool(description="获取某篇文章的全部评论")
async def list_comments(post_id: int) -> str:
    """获取文章评论"""
    async with async_session() as db:
        # 验证文章存在
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            return "❌ 文章不存在"

        # 获取顶级评论
        result = await db.execute(
            select(Comment)
            .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
            .order_by(Comment.created_at.desc())
        )
        top_comments = result.scalars().all()

        lines = [f"💬 《{post.title}》的评论 ({len(top_comments)} 条)", ""]
        for c in top_comments:
            lines.append(f"#{c.id} 用户{c.author_id}  {c.created_at.strftime('%m-%d %H:%M')}")
            lines.append(f"  {c.content[:200]}")
            lines.append("")

            # 获取回复
            result = await db.execute(
                select(Comment)
                .where(Comment.parent_id == c.id)
                .order_by(Comment.created_at)
            )
            replies = result.scalars().all()
            for r in replies:
                lines.append(f"  ↳ #{r.id} 用户{r.author_id}: {r.content[:100]}")
            if replies:
                lines.append("")

        if not top_comments:
            lines.append("(暂无评论)")

        return "\n".join(lines)


@mcp.tool(description="获取博客的统计概览信息：文章数、用户数、评论数、自动化数据")
async def blog_stats() -> str:
    """博客统计概览"""
    async with async_session() as db:
        posts_count = (await db.execute(select(func.count()).select_from(Post))).scalar()
        users_count = (await db.execute(select(func.count()).select_from(User))).scalar()
        comments_count = (await db.execute(select(func.count()).select_from(Comment))).scalar()
        news_count = (await db.execute(select(func.count()).select_from(NewsDigest))).scalar()
        trending_count = (await db.execute(select(func.count()).select_from(TrendingRepo))).scalar()
        paper_count = (await db.execute(select(func.count()).select_from(PaperDigest))).scalar()

        # 最近文章
        result = await db.execute(
            select(Post).where(Post.status == "published").order_by(Post.created_at.desc()).limit(5)
        )
        recent = result.scalars().all()

        from app.core.config import settings
        lines = [
            "📊 MyBlog 统计概览",
            "",
            f"👥 用户数: {users_count}",
            f"📝 文章数: {posts_count}",
            f"💬 评论数: {comments_count}",
            "",
            "🤖 自动化数据:",
            f"  📰 资讯摘要: {news_count} 条",
            f"  🔥 Trending 仓库: {trending_count} 个",
            f"  📄 论文速递: {paper_count} 篇",
            f"  状态: {'✅ 已启用' if settings.AUTOMATION_ENABLED else '❌ 未启用'}",
            "",
            "📌 最近文章:",
        ]
        for p in recent:
            lines.append(f"  - [{p.id}] {p.title} ({p.created_at.strftime('%m-%d')})")

        return "\n".join(lines)


@mcp.tool(description="获取用户信息，支持按用户名或用户ID查找")
async def get_user_info(username: Optional[str] = None, user_id: Optional[int] = None) -> str:
    """获取用户信息"""
    async with async_session() as db:
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
        elif username:
            result = await db.execute(select(User).where(User.username == username))
        else:
            return "❌ 请提供用户名或用户ID"

        user = result.scalar_one_or_none()
        if not user:
            return "❌ 用户不存在"

        # 统计用户文章数和评论数
        post_count = (
            await db.execute(
                select(func.count()).select_from(Post).where(Post.author_id == user.id)
            )
        ).scalar()
        comment_count = (
            await db.execute(
                select(func.count()).select_from(Comment).where(Comment.author_id == user.id)
            )
        ).scalar()

        return (
            f"👤 **{user.nickname or user.username}** ({user.username})\n"
            f"ID: {user.id}  |  邮箱: {user.email}\n"
            f"📝 {post_count} 篇文章  |  💬 {comment_count} 条评论\n"
            f"📅 注册时间: {user.created_at.strftime('%Y-%m-%d')}\n"
            f"{'📖 ' + user.bio if user.bio else ''}"
        )


# ===== 新增：暴露现有 API 能力 =====

@mcp.tool(description="获取博客 RSS feed（XML 格式的最近 20 篇已发布文章）")
async def get_rss() -> str:
    """获取 RSS feed"""
    async with async_session() as db:
        result = await db.execute(
            select(Post).where(Post.status == "published")
            .order_by(desc(Post.is_pinned), desc(Post.created_at)).limit(20)
        )
        posts = result.scalars().all()
        lines = [f"📡 RSS Feed — {len(posts)} 篇文章", ""]
        for p in posts:
            lines.append(f"- {p.title}")
            lines.append(f"  链接: /posts/{p.id}")
            lines.append(f"  日期: {p.created_at.strftime('%Y-%m-%d')}")
            lines.append(f"  摘要: {(p.summary or p.content)[:150]}")
            lines.append("")
        return "\n".join(lines)


@mcp.tool(description="查看草稿箱中的文章列表（需要用户名和密码鉴权）")
async def list_drafts(username: str, password: str) -> str:
    """列出草稿"""
    async with async_session() as db:
        from app.core.security import verify_password
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return "❌ 用户名或密码错误"
        result = await db.execute(
            select(Post).where(Post.author_id == user.id, Post.status == "draft")
            .order_by(desc(Post.updated_at))
        )
        drafts = result.scalars().all()
        if not drafts:
            return "📝 草稿箱为空"
        lines = [f"📝 草稿箱 ({len(drafts)} 篇)", ""]
        for d in drafts:
            lines.append(f"- [{d.id}] {d.title or '(无标题)'}")
            lines.append(f"  最后修改: {d.updated_at.strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"  摘要: {(d.summary or d.content)[:100]}")
            lines.append("")
        return "\n".join(lines)


@mcp.tool(description="获取草稿详情（需要用户名和密码鉴权）")
async def get_draft(draft_id: int, username: str, password: str) -> str:
    """获取草稿详情"""
    async with async_session() as db:
        from app.core.security import verify_password
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return "❌ 用户名或密码错误"
        result = await db.execute(select(Post).where(Post.id == draft_id))
        post = result.scalar_one_or_none()
        if not post:
            return "❌ 草稿不存在"
        if post.author_id != user.id:
            return "❌ 只能查看自己的草稿"
        return (
            f"# {post.title or '(无标题)'}\n\n"
            f"**状态**: {post.status}  |  **创建时间**: {post.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"---\n\n{post.content}"
        )


@mcp.tool(description="获取热门文章列表（按浏览量和点赞排序）")
async def get_hot_posts(limit: int = 10) -> str:
    """获取热门文章"""
    async with async_session() as db:
        result = await db.execute(
            select(Post).where(Post.status == "published")
            .order_by(desc(Post.view_count + Post.like_count)).limit(limit)
        )
        posts = result.scalars().all()
        lines = [f"🔥 热门文章 Top {len(posts)}", ""]
        for i, p in enumerate(posts, 1):
            lines.append(f"{i}. [{p.id}] {p.title}")
            lines.append(f"   👁️ {p.view_count}  ❤️ {p.like_count}  💬 {p.comment_count}")
            lines.append("")
        return "\n".join(lines)


@mcp.tool(description="随机获取一篇已发布文章")
async def get_random_post() -> str:
    """随机获取文章"""
    async with async_session() as db:
        result = await db.execute(
            select(Post).where(Post.status == "published").order_by(func.random()).limit(1)
        )
        post = result.scalar_one_or_none()
        if not post:
            return "❌ 没有已发布的文章"
        return (
            f"🎲 随机推荐\n\n"
            f"# {post.title}\n\n"
            f"**❤️ {post.like_count}**  **💬 {post.comment_count}**  **👁️ {post.view_count}**\n\n"
            f"---\n\n{post.content[:500]}"
        )


@mcp.tool(description="列出所有标签及其文章数量")
async def list_tags() -> str:
    """列出所有标签"""
    async with async_session() as db:
        result = await db.execute(
            select(Tag).order_by(Tag.name)
        )
        tags = result.scalars().all()
        if not tags:
            return "🏷️ 暂无标签"
        lines = ["🏷️ 标签列表", ""]
        for t in tags:
            post_count = len(t.posts) if t.posts else 0
            lines.append(f"- {t.name} ({post_count} 篇)")
        return "\n".join(lines)


@mcp.tool(description="根据标签 slug 获取关联的文章列表")
async def get_posts_by_tag(tag_slug: str, page: int = 1, page_size: int = 20) -> str:
    """根据标签获取文章"""
    async with async_session() as db:
        result = await db.execute(select(Tag).where(Tag.slug == tag_slug))
        tag = result.scalar_one_or_none()
        if not tag:
            return f"❌ 标签 '{tag_slug}' 不存在"

        # 获取关联文章（已通过 lazy="selectin" 加载）
        posts = tag.posts if tag.posts else []
        total = len(posts)
        start = (page - 1) * page_size
        paged = posts[start:start + page_size]

        lines = [f"🏷️ #{tag.name} — {total} 篇文章", ""]
        for p in paged:
            lines.append(f"- [{p.id}] {p.title}")
            lines.append(f"  ❤️ {p.like_count}  💬 {p.comment_count}")
            lines.append("")
        if not paged:
            lines.append("(无文章)")
        return "\n".join(lines)


@mcp.tool(description="调用 AI 为给定内容生成中文摘要（需要 AI_API_KEY 配置）")
async def generate_post_summary(content: str, title: str = "") -> str:
    """AI 生成摘要"""
    from app.services.ai_processor import ai_chat
    result = await ai_chat(
        system_prompt="你是一个文章摘要助手。用一句话中文总结文章核心内容，不超过150字。",
        user_content=content[:3000],
        max_tokens=200,
        temperature=0.7,
    )
    if result is None:
        return "❌ AI 服务未配置（需要设置 AI_API_KEY）或调用失败"
    return f"✅ AI 摘要:\n\n{result}"


@mcp.tool(description="切换点赞状态：对文章或评论进行点赞/取消点赞")
async def toggle_like(user_id: int, target_type: str, target_id: int) -> str:
    """切换点赞（需要提供 user_id）"""
    async with async_session() as db:
        user = await db.execute(select(User).where(User.id == user_id))
        if not user.scalar_one_or_none():
            return "❌ 用户不存在"

        # 检查是否已点赞
        existing = await db.execute(
            select(Like).where(
                Like.user_id == user_id,
                Like.target_type == target_type,
                Like.target_id == target_id,
            )
        )
        like = existing.scalar_one_or_none()

        if like:
            await db.delete(like)
            await db.commit()
            return f"💔 已取消对 {target_type}#{target_id} 的点赞"
        else:
            new_like = Like(user_id=user_id, target_type=target_type, target_id=target_id)
            db.add(new_like)
            await db.commit()
            return f"❤️ 已对 {target_type}#{target_id} 点赞"


@mcp.tool(description="查询用户是否已对某个对象点赞")
async def get_like_status(user_id: int, target_type: str, target_id: int) -> str:
    """查询点赞状态"""
    async with async_session() as db:
        result = await db.execute(
            select(Like).where(
                Like.user_id == user_id,
                Like.target_type == target_type,
                Like.target_id == target_id,
            )
        )
        like = result.scalar_one_or_none()
        return f"{'❤️ 已点赞' if like else '🤍 未点赞'} {target_type}#{target_id}"


@mcp.tool(description="获取用户完整信息：资料、文章数、评论数")
async def get_user_profile(user_id: Optional[int] = None, username: Optional[str] = None) -> str:
    """（同 get_user_info，保留兼容）"""
    return await get_user_info(username=username, user_id=user_id)


@mcp.tool(description="更新用户个人资料：昵称、简介（需要用户名和密码鉴权）")
async def update_user_profile(
    username: str,
    password: str,
    nickname: Optional[str] = None,
    bio: Optional[str] = None,
) -> str:
    """更新个人资料"""
    async with async_session() as db:
        from app.core.security import verify_password
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return "❌ 用户名或密码错误"

        if nickname is not None:
            user.nickname = nickname
        if bio is not None:
            user.bio = bio
        await db.commit()
        return f"✅ 资料已更新: {user.nickname or user.username}"


# ===== 自动化查询/触发工具 =====

@mcp.tool(description="获取 AI 资讯摘要列表（新闻/大会 AI 总结）")
async def list_news_digests(
    page: int = 1,
    page_size: int = 20,
    source_type: str = "",
) -> str:
    """列出新闻摘要"""
    async with async_session() as db:
        q = select(NewsDigest)
        total_q = select(func.count()).select_from(NewsDigest)
        if source_type:
            q = q.where(NewsDigest.source_type == source_type)
            total_q = total_q.where(NewsDigest.source_type == source_type)
        q = q.order_by(desc(NewsDigest.published_date), desc(NewsDigest.id))

        total = (await db.execute(total_q)).scalar() or 0
        offset = (page - 1) * page_size
        result = await db.execute(q.offset(offset).limit(page_size))
        items = result.scalars().all()

        label = f"（{source_type}）" if source_type else ""
        lines = [f"📰 AI 资讯摘要{label} — {total} 条（第 {page} 页）", ""]
        for d in items:
            lines.append(f"- [{d.id}] {d.title}")
            lines.append(f"  来源: {d.source_name}  |  {d.published_date.strftime('%Y-%m-%d') if d.published_date else ''}")
            if d.content:
                lines.append(f"  📝 {d.content[:200]}")
            elif d.raw_data:
                lines.append(f"  📄 {str(d.raw_data.get('summary', ''))[:200]}")
            lines.append("")
        if not items:
            lines.append("(暂无资讯摘要，请先触发抓取)")
        return "\n".join(lines)


@mcp.tool(description="获取单条资讯摘要详情")
async def get_news_digest(digest_id: int) -> str:
    """单条摘要"""
    async with async_session() as db:
        result = await db.execute(select(NewsDigest).where(NewsDigest.id == digest_id))
        d = result.scalar_one_or_none()
        if not d:
            return "❌ 摘要不存在"
        return (
            f"# {d.title}\n\n"
            f"**来源**: {d.source_name} ({d.source_type})\n"
            f"**日期**: {d.published_date.strftime('%Y-%m-%d %H:%M') if d.published_date else '未知'}\n"
            f"**AI 处理**: {'✅ 是' if d.is_processed else '❌ 否'}\n\n"
            f"---\n\n{d.content or '(无 AI 摘要，请检查 AI_API_KEY 配置)'}\n\n"
            f"**原文链接**: {d.source_url}"
        )


@mcp.tool(description="手动触发新闻资讯抓取和 AI 摘要生成")
async def trigger_news_fetch() -> str:
    """手动触发新闻抓取"""
    from app.services.news_fetcher import NewsFetcher
    result = await NewsFetcher().run()
    return f"📰 新闻抓取完成: {result['message']}"


@mcp.tool(description="获取 GitHub Trending 仓库列表及 AI 中文解读")
async def list_trending_repos(page: int = 1, page_size: int = 20) -> str:
    """列出 GitHub Trending"""
    async with async_session() as db:
        total = (await db.execute(select(func.count()).select_from(TrendingRepo))).scalar() or 0
        offset = (page - 1) * page_size
        result = await db.execute(
            select(TrendingRepo).order_by(desc(TrendingRepo.fetched_date), desc(TrendingRepo.id))
            .offset(offset).limit(page_size)
        )
        items = result.scalars().all()

        lines = [f"🔥 GitHub Trending 解读 — {total} 个仓库（第 {page} 页）", ""]
        for r in items:
            lines.append(f"- {r.repo_name}")
            lines.append(f"  🔗 {r.repo_url}")
            if r.language:
                lines.append(f"  💻 {r.language}  ⭐ {r.stars_today} today  |  {r.total_stars} total")
            if r.ai_interpretation:
                lines.append(f"  🤖 {r.ai_interpretation[:200]}")
            elif r.description:
                lines.append(f"  📝 {r.description[:200]}")
            lines.append("")
        if not items:
            lines.append("(暂无数据，请先触发抓取)")
        return "\n".join(lines)


@mcp.tool(description="获取单个 GitHub Trending 仓库的详细 AI 解读")
async def get_trending_repo(repo_id: int) -> str:
    """单个仓库详情"""
    async with async_session() as db:
        result = await db.execute(select(TrendingRepo).where(TrendingRepo.id == repo_id))
        r = result.scalar_one_or_none()
        if not r:
            return "❌ 仓库不存在"
        return (
            f"# {r.repo_name}\n\n"
            f"🔗 {r.repo_url}\n"
            f"💻 语言: {r.language or '未知'}\n"
            f"⭐ 今日: {r.stars_today}  |  总计: {r.total_stars}\n"
            f"📅 数据日期: {r.fetched_date}\n\n"
            f"## AI 解读\n\n{r.ai_interpretation or '(无 AI 解读，请检查 AI_API_KEY 配置)'}\n\n"
            f"## 项目描述\n\n{r.description or '(无)'}"
        )


@mcp.tool(description="手动触发 GitHub Trending 抓取和 AI 解读")
async def trigger_trending_fetch() -> str:
    """手动触发"""
    from app.services.github_fetcher import GithubFetcher
    result = await GithubFetcher().run()
    return f"🔥 GitHub Trending 抓取完成: {result['message']}"


@mcp.tool(description="获取 AI 论文速递列表（Arxiv 论文 AI 中文摘要）")
async def list_paper_digests(
    page: int = 1,
    page_size: int = 20,
    category: str = "",
) -> str:
    """列出论文摘要"""
    async with async_session() as db:
        q = select(PaperDigest).order_by(desc(PaperDigest.published_date), desc(PaperDigest.id))
        total_q = select(func.count()).select_from(PaperDigest)
        if category:
            q = q.where(PaperDigest.categories.contains([category]))
            total_q = total_q.where(PaperDigest.categories.contains([category]))

        total = (await db.execute(total_q)).scalar() or 0
        offset = (page - 1) * page_size
        result = await db.execute(q.offset(offset).limit(page_size))
        items = result.scalars().all()

        label = f"（{category}）" if category else ""
        lines = [f"📄 AI 论文速递{label} — {total} 篇（第 {page} 页）", ""]
        for p in items:
            lines.append(f"- [{p.id}] {p.title[:120]}")
            if p.authors:
                authors_str = ", ".join(p.authors[:3])
                if len(p.authors) > 3:
                    authors_str += f" 等{len(p.authors)}人"
                lines.append(f"  ✍️ {authors_str}")
            if p.categories:
                lines.append(f"  🏷️ {', '.join(p.categories[:3])}")
            if p.ai_summary_zh:
                lines.append(f"  🤖 {p.ai_summary_zh[:200]}")
            else:
                lines.append(f"  📝 {p.abstract[:150]}")
            lines.append("")
        if not items:
            lines.append("(暂无论文摘要，请先触发抓取)")
        return "\n".join(lines)


@mcp.tool(description="获取单篇论文的完整 AI 摘要")
async def get_paper_digest(paper_id: int) -> str:
    """单篇论文详情"""
    async with async_session() as db:
        result = await db.execute(select(PaperDigest).where(PaperDigest.id == paper_id))
        p = result.scalar_one_or_none()
        if not p:
            return "❌ 论文不存在"
        authors_str = ", ".join(p.authors) if p.authors else "未知"
        cats_str = ", ".join(p.categories) if p.categories else "未分类"
        return (
            f"# {p.title}\n\n"
            f"**Arxiv ID**: {p.arxiv_id}\n"
            f"**作者**: {authors_str}\n"
            f"**分类**: {cats_str}\n"
            f"**发布日期**: {p.published_date.strftime('%Y-%m-%d') if p.published_date else '未知'}\n"
            f"**链接**: {p.paper_url}\n"
            f"**PDF**: {p.pdf_url or '无'}\n\n"
            f"## AI 中文摘要\n\n{p.ai_summary_zh or '(无 AI 摘要，请检查 AI_API_KEY 配置)'}\n\n"
            f"## 原文摘要\n\n{p.abstract or '(无)'}"
        )


@mcp.tool(description="手动触发 Arxiv 论文抓取和 AI 摘要生成")
async def trigger_paper_fetch() -> str:
    """手动触发"""
    from app.services.arxiv_fetcher import ArxivFetcher
    result = await ArxivFetcher().run()
    return f"📄 论文抓取完成: {result['message']}"


def main():
    """启动 MCP Server"""
    import argparse

    parser = argparse.ArgumentParser(description="MyBlog MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                        help="传输模式: stdio（默认，用于 Claude Desktop/Code）或 sse（HTTP）")
    parser.add_argument("--host", default="0.0.0.0", help="SSE 模式监听地址")
    parser.add_argument("--port", type=int, default=8100, help="SSE 模式监听端口")
    args = parser.parse_args()

    print("🚀 MyBlog MCP Server 启动中...")
    print(f"   传输模式: {args.transport}")
    print("")
    print("支持的工具 (共 31 个):")
    print("  📝 文章管理:")
    print("    - list_posts      : 查看文章列表")
    print("    - get_post        : 查看文章详情")
    print("    - search_posts    : 搜索文章")
    print("    - create_post     : 发布文章（需鉴权）")
    print("    - update_post     : 编辑文章（需鉴权）")
    print("    - delete_post     : 删除文章（需鉴权）")
    print("    - list_drafts     : 查看草稿（需鉴权）")
    print("    - get_draft       : 草稿详情（需鉴权）")
    print("    - get_hot_posts   : 热门文章")
    print("    - get_random_post : 随机文章")
    print("    - get_rss         : RSS Feed")
    print("  🏷️ 标签/交互:")
    print("    - list_tags        : 标签列表")
    print("    - get_posts_by_tag : 按标签查文章")
    print("    - toggle_like      : 点赞/取消")
    print("    - get_like_status  : 点赞状态")
    print("    - list_comments    : 查看评论")
    print("  👤 用户:")
    print("    - get_user_info      : 用户信息")
    print("    - get_user_profile   : 用户资料")
    print("    - update_user_profile: 更新资料（需鉴权）")
    print("  🤖 AI 自动化:")
    print("    - generate_post_summary : AI 生成摘要")
    print("    - list_news_digests  : 资讯摘要列表")
    print("    - get_news_digest    : 资讯摘要详情")
    print("    - trigger_news_fetch : 触发新闻抓取")
    print("    - list_trending_repos: Trending 列表")
    print("    - get_trending_repo  : Trending 详情")
    print("    - trigger_trending_fetch: 触发 Trending 抓取")
    print("    - list_paper_digests : 论文速递列表")
    print("    - get_paper_digest   : 论文详情")
    print("    - trigger_paper_fetch: 触发论文抓取")
    print("  📊 其他:")
    print("    - blog_stats  : 博客统计（含自动化数据）")
    print("")

    if args.transport == "sse":
        print(f"🌐 SSE 模式，监听 {args.host}:{args.port}")
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route

        sse = SseServerTransport("/mcp/messages")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await mcp._run_session(streams[0], streams[1])

        app = Starlette(routes=[
            Route("/sse", endpoint=handle_sse),
        ])

        uvicorn.run(app, host=args.host, port=args.port)
    else:
        print("🔌 stdio 模式，等待 MCP 客户端连接...")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
