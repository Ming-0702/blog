"""自动化内容相关 Pydantic schema"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel


# ===== 新闻摘要 =====

class DigestOut(BaseModel):
    id: int
    source_type: str
    title: str
    content: str
    raw_data: Optional[dict] = None
    source_url: str
    source_name: str
    published_date: Optional[datetime] = None
    is_processed: bool = False
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class DigestPage(BaseModel):
    items: List[DigestOut]
    total: int
    page: int
    page_size: int


# ===== GitHub Trending =====

class TrendingRepoOut(BaseModel):
    id: int
    repo_name: str
    repo_url: str
    description: str
    language: str
    stars_today: int
    total_stars: int
    contributors: Optional[list] = None
    ai_interpretation: str
    fetched_date: date
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class TrendingRepoPage(BaseModel):
    items: List[TrendingRepoOut]
    total: int
    page: int
    page_size: int


# ===== 论文摘要 =====

class PaperOut(BaseModel):
    id: int
    arxiv_id: str
    title: str
    authors: Optional[list] = None
    paper_url: str
    pdf_url: str
    abstract: str
    categories: Optional[list] = None
    published_date: Optional[datetime] = None
    ai_summary: str
    ai_summary_zh: str
    is_processed: bool = False
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class PaperPage(BaseModel):
    items: List[PaperOut]
    total: int
    page: int
    page_size: int


# ===== 自动化状态 =====

class AutomationStatus(BaseModel):
    automation_enabled: bool
    news_digests_total: int
    trending_repos_total: int
    paper_digests_total: int
    message: str = ""
