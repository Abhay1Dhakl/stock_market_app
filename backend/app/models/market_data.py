from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DailyPrice(Base, TimestampMixin):
    __tablename__ = "daily_prices"
    __table_args__ = (UniqueConstraint("company_id", "trading_date", name="uq_daily_prices_company_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    turnover: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    source_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="price_history")


class FloorsheetTransaction(Base, TimestampMixin):
    __tablename__ = "floorsheet_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    trading_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    transaction_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    buyer_broker_code: Mapped[str] = mapped_column(String(32), nullable=False)
    seller_broker_code: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    row_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    source_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="floorsheet_transactions")
