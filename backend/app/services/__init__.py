"""服务层统一导出"""
from app.services.ai_processor import ai_chat
from app.services.base_fetcher import BaseAutomationFetcher
from app.services.news_fetcher import NewsFetcher
from app.services.github_fetcher import GithubFetcher
from app.services.scheduler import scheduler, init_scheduler

__all__ = [
    "ai_chat",
    "BaseAutomationFetcher",
    "NewsFetcher",
    "GithubFetcher",
    "scheduler",
    "init_scheduler",
]
