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


async def _cleanup_old_data():
    """清理超过保留期限的数据"""
    from datetime import date, timedelta
    from app.core.config import settings
    from app.core.database import async_session
    from sqlalchemy import delete
    from app.models.digest import NewsDigest
    from app.models.trending import TrendingRepo
    retention = settings.AUTOMATION_RETENTION_DAYS
    cutoff = date.today() - timedelta(days=retention)

    async with async_session() as db:
        r1 = await db.execute(delete(NewsDigest).where(NewsDigest.created_at < cutoff))
        r2 = await db.execute(delete(TrendingRepo).where(TrendingRepo.fetched_date < cutoff))
        await db.commit()
        total = (r1.rowcount or 0) + (r2.rowcount or 0)
        if total:
            import logging
            logging.getLogger(__name__).info(f"Cleanup: deleted {total} records older than {retention} days")


def init_scheduler():
    """初始化并启动调度器。在 FastAPI lifespan startup 中调用。"""
    from app.core.config import settings

    if not settings.AUTOMATION_ENABLED:
        return

    from app.services.news_fetcher import NewsFetcher
    from app.services.github_fetcher import GithubFetcher

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
    # 注册数据清理任务（每天凌晨 3 点）
    scheduler.add_job(
        _cleanup_old_data,
        trigger="cron", hour=3, minute=0,
        id="cleanup_old_data",
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
