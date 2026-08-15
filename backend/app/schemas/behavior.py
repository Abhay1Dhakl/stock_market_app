from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class BehaviorBreakdownItem(BaseModel):
    event_type: str
    count: int


class BehaviorCompanyInterest(BaseModel):
    company_id: int
    symbol: str
    name: str
    interactions: int


class UserBehaviorEventItem(BaseModel):
    event_type: str
    occurred_at: datetime
    page_path: Optional[str] = None
    company_id: Optional[int] = None
    company_symbol: Optional[str] = None
    company_name: Optional[str] = None
    metadata: dict[str, object] = Field(default_factory=dict)


class UserBehaviorSummaryResponse(BaseModel):
    total_events: int = 0
    watchlist_size: int = 0
    companies_explored: int = 0
    favorite_sector: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    event_breakdown: list[BehaviorBreakdownItem] = Field(default_factory=list)
    top_companies: list[BehaviorCompanyInterest] = Field(default_factory=list)
    recent_activity: list[UserBehaviorEventItem] = Field(default_factory=list)


class AdminUserBehaviorRow(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    role: str
    watchlist_size: int = 0
    total_events: int = 0
    companies_explored: int = 0
    last_activity_at: Optional[datetime] = None
    favorite_symbol: Optional[str] = None


class AdminUserBehaviorResponse(BaseModel):
    items: list[AdminUserBehaviorRow]


class TelemetryEventRequest(BaseModel):
    event_type: str = Field(min_length=2, max_length=50)
    page_path: Optional[str] = Field(default=None, max_length=255)
    company_id: Optional[int] = None
    article_id: Optional[int] = None
    metadata: dict[str, object] = Field(default_factory=dict)
    notes: Optional[str] = None


class TelemetryEventResponse(BaseModel):
    id: int
    event_type: str
