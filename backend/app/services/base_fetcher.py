"""自动化抓取器基类 —— fetch → AI process → store 通用流程"""
import logging
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)


class BaseAutomationFetcher(ABC):
    """自动化抓取基类。子类只需实现 fetch_raw() 和 ai_process()。"""

    @abstractmethod
    async def fetch_raw(self) -> list[dict]:
        """从外部数据源抓取原始数据，返回 dict 列表"""
        ...

    @abstractmethod
    async def ai_process(self, items: list[dict]) -> list[dict]:
        """对抓取结果进行 AI 处理，返回增加了 AI 字段的 dict 列表"""
        ...

    async def run(self, db: AsyncSession | None = None) -> dict:
        """执行完整的抓取→AI处理→存储流程。
        返回 {'status': 'success'|'no_data'|'error', 'count': int, 'message': str}
        """
        own_db = db is None
        if own_db:
            from app.core.database import async_session
            db = async_session()

        try:
            # 1. 抓取
            items = await self.fetch_raw()
            if not items:
                return {"status": "no_data", "count": 0, "message": "没有新数据"}

            # 2. AI 处理
            items = await self.ai_process(items)

            # 3. 存储
            count = await self._store(db, items)

            if own_db:
                await db.commit()

            logger.info(f"{self.__class__.__name__}: stored {count} items")
            return {"status": "success", "count": count, "message": f"成功存入 {count} 条"}
        except Exception as e:
            if own_db:
                await db.rollback()
            logger.error(f"{self.__class__.__name__} error: {e}")
            return {"status": "error", "count": 0, "message": str(e)}
        finally:
            if own_db:
                await db.close()

    @abstractmethod
    async def _store(self, db: AsyncSession, items: list[dict]) -> int:
        """存储到数据库，返回成功存储的数量。使用 ON CONFLICT DO NOTHING 去重。"""
        ...
