"""自动化调度器 —— APScheduler 集成"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()


def _parse_cron(expr: str) -> dict:
    """将 '0 8 * * *' 格式的 cron 表达式解析为 APScheduler 参数字典"""
    parts = expr.strip().split()
    if len(parts) != 5:
        return {"trigger": "cron", "minute": "*/30"}
    return {
        "trigger": "cron",
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "day_of_week": parts[4],
    }


async def _initial_fetch():
    """启动时延迟执行首次抓取（如果今天还没有数据）"""
    import asyncio
    from app.core.config import settings
    from app.core.database import async_session

    if not settings.AUTOMATION_ENABLED:
        return

    await asyncio.sleep(30)  # 等服务完全启动

    from app.services.news_fetcher import NewsFetcher
    from app.services.github_fetcher import GithubFetcher
    from app.services.arxiv_fetcher import ArxivFetcher

    # 检查今天是否已有数据（避免重启重复抓取）
    from datetime import date
    from sqlalchemy import select, func
    from app.models.trending import TrendingRepo

    async with async_session() as db:
        result = await db.execute(
            select(func.count()).select_from(TrendingRepo).where(
                TrendingRepo.fetched_date == date.today()
            )
        )
        if result.scalar() == 0:
            await GithubFetcher().run(db=db)
            await db.commit()

    await NewsFetcher().run()
    await ArxivFetcher().run()


def init_scheduler():
    """初始化并启动调度器。在 FastAPI lifespan startup 中调用。"""
    from app.core.config import settings

    if not settings.AUTOMATION_ENABLED:
        return

    from app.services.news_fetcher import NewsFetcher
    from app.services.github_fetcher import GithubFetcher
    from app.services.arxiv_fetcher import ArxivFetcher

    # 注册定时任务
    scheduler.add_job(
        NewsFetcher().run,
        **_parse_cron(settings.NEWS_SCHEDULE),
        id="news_digest",
        replace_existing=True,
    )
    scheduler.add_job(
        GithubFetcher().run,
        **_parse_cron(settings.GITHUB_TRENDING_SCHEDULE),
        id="github_trending",
        replace_existing=True,
    )
    scheduler.add_job(
        ArxivFetcher().run,
        **_parse_cron(settings.ARXIV_SCHEDULE),
        id="arxiv_papers",
        replace_existing=True,
    )

    scheduler.start()

    # 启动后延迟执行首次抓取（不阻塞启动）
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_initial_fetch())
    except RuntimeError:
        pass
