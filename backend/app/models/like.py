"""点赞模型（通用：支持文章和评论点赞）"""
import datetime
from sqlalchemy import DateTime, Integer, ForeignKey, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "post" 或 "comment"
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", back_populates="likes")
    # 注意：target_type/target_id 是多态关联，没有直接的 ORM 关系
    # 需要通过查询来获取目标对象

    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_user_like_target"),
    )
