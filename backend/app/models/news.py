from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class NewsArticle(Base, TimestampMixin):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    crawl_run_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("crawl_runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    crawl_run: Mapped[Optional[CrawlRun]] = relationship(back_populates="articles")
    tags: Mapped[list[NewsCompanyTag]] = relationship(
        back_populates="news_article",
        cascade="all, delete-orphan",
    )
    tag_corrections: Mapped[list[NewsTagCorrection]] = relationship(
        back_populates="news_article",
        cascade="all, delete-orphan",
    )
    behavior_events: Mapped[list[UserBehaviorEvent]] = relationship(back_populates="article")


class NewsCompanyTag(Base, TimestampMixin):
    __tablename__ = "news_company_tags"
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="confidence_range",
        ),
        CheckConstraint(
            "tag_source in ('system', 'manual')",
            name="tag_source",
        ),
        UniqueConstraint("news_article_id", "company_id", name="uq_news_company_tags_article_company"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    news_article_id: Mapped[int] = mapped_column(
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    tag_source: Mapped[str] = mapped_column(String(20), default="system", nullable=False)
    match_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    news_article: Mapped[NewsArticle] = relationship(back_populates="tags")
    company: Mapped[Company] = relationship(back_populates="news_tags")
    created_by: Mapped[Optional[User]] = relationship(back_populates="created_news_tags")


class NewsTagCorrection(Base):
    __tablename__ = "news_tag_corrections"

    id: Mapped[int] = mapped_column(primary_key=True)
    news_article_id: Mapped[int] = mapped_column(
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    reviewer_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_tags: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    updated_tags: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    news_article: Mapped[NewsArticle] = relationship(back_populates="tag_corrections")
    reviewer: Mapped[User] = relationship(back_populates="news_tag_corrections")
