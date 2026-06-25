"""新闻/大会 摘要抓取器 —— RSS feed → AI 中文摘要 → 存储"""
import json
import logging
from datetime import datetime, timezone, timedelta
import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.models.digest import NewsDigest
from app.services.base_fetcher import BaseAutomationFetcher
from app.services.ai_processor import ai_chat

logger = logging.getLogger(__name__)


class NewsFetcher(BaseAutomationFetcher):

    async def fetch_raw(self) -> list[dict]:
        sources = json.loads(settings.NEWS_SOURCES)
        items = []
        for url in sources:
            try:
                feed = feedparser.parse(url)
                source_name = feed.feed.get("title", url)
                for entry in feed.entries[:20]:  # 每次最多 20 条
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    items.append({
                        "source_type": "news",
                        "title": entry.get("title", ""),
                        "source_url": entry.get("link", ""),
                        "source_name": source_name,
                        "published_date": published,
                        "raw_data": {
                            "summary": entry.get("summary", ""),
                            "author": entry.get("author", ""),
                        },
                    })
            except Exception as e:
                logger.warning(f"NewsFetcher: failed to parse {url}: {e}")
        return items

    async def ai_process(self, items: list[dict]) -> list[dict]:
        for item in items:
            raw = item.get("raw_data", {})
            prompt = f"Title: {item.get('title', '')}\nSummary: {raw.get('summary', '')}"
            ai_result = await ai_chat(
                system_prompt=(
                    "你是一个科技新闻编辑。用简洁中文总结以下新闻，包括核心内容和为什么值得关注。"
                    "控制在300字以内，用2-3句话表达清楚。"
                ),
                user_content=prompt[:3000],
                max_tokens=400,
            )
            item["content"] = ai_result or ""
            item["is_processed"] = ai_result is not None
        return items

    async def _store(self, db: AsyncSession, items: list[dict]) -> int:
        if not items:
            return 0
        stmt = insert(NewsDigest).values(items).on_conflict_do_nothing(
            constraint="uq_news_source_date"
        )
        result = await db.execute(stmt)
        return result.rowcount or 0
