"""Arxiv 论文抓取器 —— Arxiv API → AI 中文摘要 → 存储"""
import logging
from datetime import datetime, timezone
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.models.paper import PaperDigest
from app.services.base_fetcher import BaseAutomationFetcher
from app.services.ai_processor import ai_chat

import lxml.etree as ET

logger = logging.getLogger(__name__)


class ArxivFetcher(BaseAutomationFetcher):

    async def fetch_raw(self) -> list[dict]:
        """从 Arxiv API 抓取最新论文"""
        categories = settings.ARXIV_CATEGORIES
        max_results = settings.ARXIV_MAX_RESULTS
        url = (
            f"https://export.arxiv.org/api/query?"
            f"search_query=cat:{categories}&sortBy=submittedDate&"
            f"sortOrder=descending&max_results={max_results}"
        )
        items = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Arxiv API returned {resp.status_code}")
                    return items
                xml_text = resp.text
        except Exception as e:
            logger.warning(f"ArxivFetcher: failed to fetch: {e}")
            return items

        # 解析 Atom XML
        try:
            root = ET.fromstring(xml_text.encode("utf-8"))
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }
            for entry in root.findall("atom:entry", ns):
                arxiv_id = entry.findtext("atom:id", "", ns).strip()
                # 提取纯 ID（去掉 http://arxiv.org/abs/ 前缀）
                arxiv_id = arxiv_id.split("/abs/")[-1] if "/abs/" in arxiv_id else arxiv_id
                title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
                abstract = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")

                authors = []
                for author_elem in entry.findall("atom:author", ns):
                    name = author_elem.findtext("atom:name", "", ns)
                    if name:
                        authors.append(name)

                categories_list = []
                for cat_elem in entry.findall("atom:category", ns):
                    cat = cat_elem.get("term", "")
                    if cat:
                        categories_list.append(cat)

                published_str = entry.findtext("atom:published", "", ns)
                published = None
                if published_str:
                    try:
                        published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass

                pdf_url = ""
                for link in entry.findall("atom:link", ns):
                    if link.get("title") == "pdf":
                        pdf_url = link.get("href", "")
                        break

                items.append({
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "paper_url": f"https://arxiv.org/abs/{arxiv_id}",
                    "pdf_url": pdf_url,
                    "abstract": abstract,
                    "categories": categories_list,
                    "published_date": published,
                })
        except ET.XMLSyntaxError as e:
            logger.warning(f"ArxivFetcher: XML parse error: {e}")

        return items

    async def ai_process(self, items: list[dict]) -> list[dict]:
        for item in items:
            abstract = item.get("abstract", "")
            if not abstract:
                continue
            prompt = f"Title: {item.get('title', '')}\nAbstract: {abstract}"
            ai_result = await ai_chat(
                system_prompt=(
                    "你是一个AI研究员。用2-3句简单易懂的中文解释这篇论文的核心思想，"
                    "让非专业的读者也能理解它在做什么。控制在250字以内。"
                ),
                user_content=prompt[:3000],
                max_tokens=400,
            )
            item["ai_summary_zh"] = ai_result or ""
            item["is_processed"] = ai_result is not None
        return items

    async def _store(self, db: AsyncSession, items: list[dict]) -> int:
        if not items:
            return 0
        count = 0
        for item in items:
            stmt = insert(PaperDigest).values(item).on_conflict_do_nothing(
                constraint="paper_digests_arxiv_id_key"
            )
            result = await db.execute(stmt)
            count += result.rowcount or 0
        return count
