"""GitHub Trending 仓库模型"""
import datetime
from sqlalchemy import String, Text, DateTime, Integer, Boolean, Date, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TrendingRepo(Base):
    __tablename__ = "trending_repos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    repo_name: Mapped[str] = mapped_column(String(300), nullable=False)  # owner/repo
    repo_url: Mapped[str] = mapped_column(String(1000), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(50), default="")
    stars_today: Mapped[int] = mapped_column(Integer, default=0)
    total_stars: Mapped[int] = mapped_column(Integer, default=0)
    contributors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ai_interpretation: Mapped[str] = mapped_column(Text, default="")  # AI 中文解读
    fetched_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("repo_url", "fetched_date", name="uq_trending_repo_date"),
    )
