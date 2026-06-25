"""Arxiv 论文摘要模型"""
import datetime
from sqlalchemy import String, Text, DateTime, Integer, Boolean, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PaperDigest(Base):
    __tablename__ = "paper_digests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    arxiv_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    authors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    paper_url: Mapped[str] = mapped_column(String(1000), default="")
    pdf_url: Mapped[str] = mapped_column(String(1000), default="")
    abstract: Mapped[str] = mapped_column(Text, default="")
    categories: Mapped[list | None] = mapped_column(JSON, nullable=True)
    published_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_summary: Mapped[str] = mapped_column(Text, default="")  # AI 英文摘要
    ai_summary_zh: Mapped[str] = mapped_column(Text, default="")  # AI 中文摘要
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
