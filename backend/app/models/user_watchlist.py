from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserWatchlistEntry(Base, TimestampMixin):
    __tablename__ = "user_watchlists"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_watchlists_user_company"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)

    user: Mapped[User] = relationship(back_populates="watchlist_entries")
    company: Mapped[Company] = relationship(back_populates="watchlist_entries")
