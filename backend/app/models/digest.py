"""新闻/大会摘要模型"""
import datetime
from sqlalchemy import String, Text, DateTime, Boolean, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NewsDigest(Base):
    __tablename__ = "news_digests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(20), default="news")  # news | conference
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")  # AI 摘要内容
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 原始数据
    source_url: Mapped[str] = mapped_column(String(1000), default="")
    source_name: Mapped[str] = mapped_column(String(200), default="")
    published_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)  # AI 是否已处理
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source_url", "published_date", name="uq_news_source_date"),
    )
