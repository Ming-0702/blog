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
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import hash_password
from app.models import User, Post, Comment, Like

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


@mcp.tool(description="获取博客的统计概览信息：文章数、用户数、评论数")
async def blog_stats() -> str:
    """博客统计概览"""
    async with async_session() as db:
        posts_count = (await db.execute(select(func.count()).select_from(Post))).scalar()
        users_count = (await db.execute(select(func.count()).select_from(User))).scalar()
        comments_count = (await db.execute(select(func.count()).select_from(Comment))).scalar()

        # 最近文章
        result = await db.execute(
            select(Post).where(Post.status == "published").order_by(Post.created_at.desc()).limit(5)
        )
        recent = result.scalars().all()

        lines = [
            "📊 MyBlog 统计概览",
            "",
            f"👥 用户数: {users_count}",
            f"📝 文章数: {posts_count}",
            f"💬 评论数: {comments_count}",
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
    print("支持的工具:")
    print("  - list_posts    : 查看文章列表")
    print("  - get_post      : 查看文章详情")
    print("  - search_posts  : 搜索文章")
    print("  - create_post   : 发布文章（需鉴权）")
    print("  - update_post   : 编辑文章（需鉴权）")
    print("  - delete_post   : 删除文章（需鉴权）")
    print("  - list_comments : 查看评论")
    print("  - blog_stats    : 博客统计")
    print("  - get_user_info : 用户信息")
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
