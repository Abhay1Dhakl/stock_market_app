from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.analysis import BehaviorSummaryResponse
from app.schemas.company import CompanySummary


class WatchlistMutationRequest(BaseModel):
    company_id: Optional[int] = None
    symbol: Optional[str] = Field(default=None, min_length=1, max_length=25)
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    sector: Optional[str] = Field(default=None, min_length=2, max_length=100)
    aliases: list[str] = Field(default_factory=list)
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_payload(self) -> "WatchlistMutationRequest":
        if self.company_id is not None:
            return self
        if self.symbol:
            return self
        raise ValueError("Provide company_id or at least a symbol.")


class CompanyInsightResponse(BaseModel):
    company: CompanySummary
    summary: BehaviorSummaryResponse
    is_in_watchlist: bool = False
    mention_count: int = 0
    last_mentioned_at: Optional[datetime] = None
    recent_headline: Optional[str] = None


class UserWatchlistResponse(BaseModel):
    items: list[CompanyInsightResponse]


class DiscoveryFeedResponse(BaseModel):
    items: list[CompanyInsightResponse]
