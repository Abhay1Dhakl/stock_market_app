from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CompanyAnalysisSnapshot(Base, TimestampMixin):
    __tablename__ = "company_analysis_snapshots"
    __table_args__ = (
        UniqueConstraint("company_id", "trading_date", name="uq_company_analysis_snapshots_company_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    close_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    vwap: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    price_change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    volume_change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    pressure_indicator: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    is_volume_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    news_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    news_sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    next_day_price_change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    next_day_volume_change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    snapshot_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    company: Mapped[Company] = relationship(back_populates="analysis_snapshots")
