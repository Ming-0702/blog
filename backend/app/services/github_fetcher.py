"""GitHub Trending 抓取器 —— 抓取 trending page → AI 中文解读 → 存储"""
import logging
from datetime import date, timezone
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.models.trending import TrendingRepo
from app.services.base_fetcher import BaseAutomationFetcher
from app.services.ai_processor import ai_chat

logger = logging.getLogger(__name__)


class GithubFetcher(BaseAutomationFetcher):

    async def fetch_raw(self) -> list[dict]:
        """从 GitHub Trending 页面抓取当日趋势仓库"""
        today = date.today()
        items = []
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(
                    "https://github.com/trending",
                    headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"},
                )
                if resp.status_code != 200:
                    logger.warning(f"GitHub Trending returned {resp.status_code}")
                    return items
                html = resp.text
        except Exception as e:
            logger.warning(f"GithubFetcher: failed to fetch trending page: {e}")
            return items

        # 简单的 HTML 解析：提取 repo 信息
        from html.parser import HTMLParser

        class TrendingParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.repos = []
                self._current = {}
                self._in_h2 = False
                self._in_p = False
                self._in_lang = False
                self._text = ""

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                cls = attrs.get("class", "")
                if tag == "article":
                    self._current = {}
                elif tag == "h2" and "h3" in cls:
                    self._in_h2 = True
                elif tag == "p" and "col-9" in cls:
                    self._in_p = True
                elif tag == "span" and "d-inline-block" in cls:
                    self._in_lang = True

            def handle_endtag(self, tag):
                if tag == "h2" and self._in_h2:
                    self._in_h2 = False
                    name = self._text.strip().replace("\n", "").replace(" ", "")
                    name = " ".join(name.split())
                    self._current["repo_name"] = name
                    self._text = ""
                elif tag == "p" and self._in_p:
                    self._in_p = False
                    self._current["description"] = self._text.strip()
                    self._text = ""
                elif tag == "span" and self._in_lang:
                    self._in_lang = False
                    self._current["language"] = self._text.strip()
                    self._text = ""
                elif tag == "article":
                    if self._current.get("repo_name"):
                        self.repos.append(self._current)
                    self._current = {}

            def handle_data(self, data):
                if self._in_h2 or self._in_p or self._in_lang:
                    self._text += data

        parser = TrendingParser()
        try:
            parser.feed(html)
        except Exception:
            pass

        for r in parser.repos[:15]:  # Top 15
            name = r.get("repo_name", "")
            items.append({
                "repo_name": name,
                "repo_url": f"https://github.com/{name}" if name else "",
                "description": r.get("description", ""),
                "language": r.get("language", ""),
                "stars_today": 0,
                "total_stars": 0,
                "fetched_date": today,
            })
        return items

    async def ai_process(self, items: list[dict]) -> list[dict]:
        for item in items:
            if not item.get("repo_name"):
                continue
            prompt = f"Project: {item.get('repo_name', '')}\nDescription: {item.get('description', '')}\nLanguage: {item.get('language', '')}"
            ai_result = await ai_chat(
                system_prompt=(
                    "你是一个技术分析师。用中文简洁解读这个 GitHub 项目：它解决什么问题、"
                    "技术方案是什么、为什么最近获得关注。控制在200字以内。"
                ),
                user_content=prompt[:2000],
                max_tokens=350,
            )
            item["ai_interpretation"] = ai_result or ""
        return items

    async def _store(self, db: AsyncSession, items: list[dict]) -> int:
        if not items:
            return 0
        stmt = insert(TrendingRepo).values(items).on_conflict_do_nothing(
            constraint="uq_trending_repo_date"
        )
        result = await db.execute(stmt)
        return result.rowcount or 0
