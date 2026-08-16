from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserBehaviorEvent(Base):
    __tablename__ = "user_behavior_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    article_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("news_articles.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    page_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_metadata: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="behavior_events")
    company: Mapped[Optional[Company]] = relationship(back_populates="behavior_events")
    article: Mapped[Optional[NewsArticle]] = relationship(back_populates="behavior_events")
