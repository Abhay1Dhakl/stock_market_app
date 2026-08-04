from __future__ import annotations

from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(25), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    price_history: Mapped[list["DailyPrice"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    floorsheet_transactions: Mapped[list["FloorsheetTransaction"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    news_tags: Mapped[list["NewsCompanyTag"]] = relationship(back_populates="company")
    analysis_snapshots: Mapped[list["CompanyAnalysisSnapshot"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )

