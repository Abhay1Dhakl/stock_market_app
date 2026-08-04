from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CrawlRun(Base, TimestampMixin):
    __tablename__ = "crawl_runs"
    __table_args__ = (
        CheckConstraint(
            "status in ('queued', 'running', 'succeeded', 'failed')",
            name="status",
        ),
        CheckConstraint(
            "run_kind in ('news', 'market_data', 'full')",
            name="run_kind",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_kind: Mapped[str] = mapped_column(String(30), default="full", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True, nullable=False)
    requested_sources: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_stats: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    triggered_by: Mapped["User | None"] = relationship(back_populates="triggered_crawl_runs")
    articles: Mapped[list["NewsArticle"]] = relationship(back_populates="crawl_run")
