from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(25), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_kind: Mapped[str] = mapped_column(String(20), default="seed", nullable=False)
    coverage_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    last_refresh_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_refresh_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    price_history: Mapped[list[DailyPrice]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    floorsheet_transactions: Mapped[list[FloorsheetTransaction]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    news_tags: Mapped[list[NewsCompanyTag]] = relationship(back_populates="company")
    analysis_snapshots: Mapped[list[CompanyAnalysisSnapshot]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    watchlist_entries: Mapped[list[UserWatchlistEntry]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    behavior_events: Mapped[list[UserBehaviorEvent]] = relationship(back_populates="company")
    created_by: Mapped[Optional[User]] = relationship(back_populates="created_companies")
