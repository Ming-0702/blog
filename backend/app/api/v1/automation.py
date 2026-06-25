"""自动化内容 API 路由"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, cast, Date, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.utils.response import success, fail
from app.core.config import settings
from app.api.deps import get_author_user
from app.models.user import User
from app.models.digest import NewsDigest
from app.models.trending import TrendingRepo
from app.models.paper import PaperDigest
from app.schemas.automation import DigestOut, TrendingRepoOut, PaperOut

router = APIRouter(prefix="/automation", tags=["自动化"])


def _serialize(item):
    """将 ORM 对象转为可 JSON 序列化的 dict"""
    if isinstance(item, NewsDigest):
        return DigestOut.model_validate(item).model_dump(mode="json")
    if isinstance(item, TrendingRepo):
        return TrendingRepoOut.model_validate(item).model_dump(mode="json")
    if isinstance(item, PaperDigest):
        return PaperOut.model_validate(item).model_dump(mode="json")
    return item


# ==================== 新闻摘要 ====================

@router.get("/digests")
async def list_digests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: str = Query("", description="news | conference"),
    date: str = Query("", description="按日期筛选, 格式 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """获取新闻/大会摘要列表"""
    q = select(NewsDigest)
    if source_type:
        q = q.where(NewsDigest.source_type == source_type)
    if date:
        q = q.where(cast(NewsDigest.published_date, Date) == date)
    q = q.order_by(desc(NewsDigest.published_date), desc(NewsDigest.id))

    total_q = select(func.count()).select_from(NewsDigest)
    if source_type:
        total_q = total_q.where(NewsDigest.source_type == source_type)
    if date:
        total_q = total_q.where(cast(NewsDigest.published_date, Date) == date)
    total = (await db.execute(total_q)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(q.offset(offset).limit(page_size))
    items = [_serialize(r) for r in result.scalars().all()]

    dates_result = await db.execute(
        select(cast(NewsDigest.published_date, Date).label("d"), func.count())
        .where(NewsDigest.published_date.isnot(None))
        .group_by(cast(NewsDigest.published_date, Date))
        .order_by(desc(cast(NewsDigest.published_date, Date))).limit(30)
    )
    available_dates = [{"date": str(r[0]), "count": r[1]} for r in dates_result.all()]

    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "available_dates": available_dates,
    })


@router.get("/digests/{digest_id}")
async def get_digest(digest_id: int, db: AsyncSession = Depends(get_db)):
    """获取单条摘要详情"""
    result = await db.execute(select(NewsDigest).where(NewsDigest.id == digest_id))
    item = result.scalar_one_or_none()
    if not item:
        return fail("摘要不存在", status_code=404)
    return success(_serialize(item))


@router.post("/digests/trigger")
async def trigger_digests(
    current_user: User = Depends(get_author_user),
):
    """手动触发新闻摘要抓取（作者专用）"""
    from app.services.news_fetcher import NewsFetcher
    r = await NewsFetcher().run()
    if r["status"] == "error":
        return fail(f"抓取失败: {r['message']}", status_code=500)
    return success(r, msg=f"抓取完成: {r['message']}")


# ==================== GitHub Trending ====================

@router.get("/trending")
async def list_trending(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date: str = Query("", description="按日期筛选, 格式 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """获取 GitHub Trending 仓库列表"""
    q = select(TrendingRepo).order_by(desc(TrendingRepo.fetched_date), desc(TrendingRepo.id))
    total_q = select(func.count()).select_from(TrendingRepo)
    if date:
        q = q.where(TrendingRepo.fetched_date == date)
        total_q = total_q.where(TrendingRepo.fetched_date == date)

    total = (await db.execute(total_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(q.offset(offset).limit(page_size))
    items = [_serialize(r) for r in result.scalars().all()]

    dates_result = await db.execute(
        select(TrendingRepo.fetched_date, func.count())
        .group_by(TrendingRepo.fetched_date)
        .order_by(desc(TrendingRepo.fetched_date)).limit(30)
    )
    available_dates = [{"date": str(r[0]), "count": r[1]} for r in dates_result.all()]

    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "available_dates": available_dates,
    })


@router.get("/trending/{repo_id}")
async def get_trending(repo_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个仓库详情"""
    result = await db.execute(select(TrendingRepo).where(TrendingRepo.id == repo_id))
    item = result.scalar_one_or_none()
    if not item:
        return fail("仓库不存在", status_code=404)
    return success(_serialize(item))


@router.post("/trending/trigger")
async def trigger_trending(
    current_user: User = Depends(get_author_user),
):
    """手动触发 GitHub Trending 抓取（作者专用）"""
    from app.services.github_fetcher import GithubFetcher
    r = await GithubFetcher().run()
    if r["status"] == "error":
        return fail(f"抓取失败: {r['message']}", status_code=500)
    return success(r, msg=f"抓取完成: {r['message']}")


# ==================== 论文摘要 ====================

@router.get("/papers")
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str = Query("", description="如 cs.AI, cs.CL"),
    date: str = Query("", description="按日期筛选, 格式 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """获取论文摘要列表"""
    q = select(PaperDigest).order_by(desc(PaperDigest.published_date), desc(PaperDigest.id))
    total_q = select(func.count()).select_from(PaperDigest)

    if category:
        q = q.where(PaperDigest.categories.cast(String).like(f'%"{category}"%'))
        total_q = total_q.where(PaperDigest.categories.cast(String).like(f'%"{category}"%'))
    if date:
        q = q.where(cast(PaperDigest.published_date, Date) == date)
        total_q = total_q.where(cast(PaperDigest.published_date, Date) == date)

    total = (await db.execute(total_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(q.offset(offset).limit(page_size))
    items = [_serialize(r) for r in result.scalars().all()]

    dates_result = await db.execute(
        select(cast(PaperDigest.published_date, Date).label("d"), func.count())
        .where(PaperDigest.published_date.isnot(None))
        .group_by(cast(PaperDigest.published_date, Date))
        .order_by(desc(cast(PaperDigest.published_date, Date))).limit(30)
    )
    available_dates = [{"date": str(r[0]), "count": r[1]} for r in dates_result.all()]

    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "available_dates": available_dates,
    })


@router.get("/papers/{paper_id}")
async def get_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    """获取单篇论文详情"""
    result = await db.execute(select(PaperDigest).where(PaperDigest.id == paper_id))
    item = result.scalar_one_or_none()
    if not item:
        return fail("论文不存在", status_code=404)
    return success(_serialize(item))


@router.post("/papers/trigger")
async def trigger_papers(
    current_user: User = Depends(get_author_user),
):
    """手动触发论文抓取（作者专用）"""
    from app.services.arxiv_fetcher import ArxivFetcher
    r = await ArxivFetcher().run()
    if r["status"] == "error":
        return fail(f"抓取失败: {r['message']}", status_code=500)
    return success(r, msg=f"抓取完成: {r['message']}")


# ==================== 状态 ====================

@router.get("/status")
async def automation_status(db: AsyncSession = Depends(get_db)):
    """获取自动化状态概览"""
    news_total = (await db.execute(select(func.count()).select_from(NewsDigest))).scalar() or 0
    trending_total = (await db.execute(select(func.count()).select_from(TrendingRepo))).scalar() or 0
    paper_total = (await db.execute(select(func.count()).select_from(PaperDigest))).scalar() or 0

    return success({
        "automation_enabled": settings.AUTOMATION_ENABLED,
        "news_digests_total": news_total,
        "trending_repos_total": trending_total,
        "paper_digests_total": paper_total,
        "retention_days": settings.AUTOMATION_RETENTION_DAYS,
        "message": "自动化已启用" if settings.AUTOMATION_ENABLED else "自动化未启用（设置 AUTOMATION_ENABLED=true）",
    })
