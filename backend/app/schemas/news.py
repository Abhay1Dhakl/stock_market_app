from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class TaggedCompanySummary(BaseModel):
    company_id: int
    symbol: str
    name: str
    confidence_score: Decimal
    tag_source: str
    match_summary: Optional[str] = None


class NewsArticleSummary(BaseModel):
    id: int
    source_name: str
    source_url: str
    headline: str
    excerpt: Optional[str] = None
    published_at: Optional[datetime] = None
    crawled_at: datetime
    sentiment_label: Optional[str] = None
    tags: list[TaggedCompanySummary]


class NewsListResponse(BaseModel):
    company_id: Optional[int] = None
    items: list[NewsArticleSummary]


class RecategorizeRequest(BaseModel):
    company_ids: list[int]
    notes: Optional[str] = None


class NewsRecategorizeResponse(BaseModel):
    news_id: int
    company_ids: list[int]
    correction_id: int
    reviewed_by: str
    notes: Optional[str] = None
