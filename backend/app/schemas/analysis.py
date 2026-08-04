from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class BehaviorSummaryResponse(BaseModel):
    company_id: int
    trading_date: Optional[date] = None
    close_price: Optional[Decimal] = None
    vwap: Optional[Decimal] = None
    price_change_pct: Optional[Decimal] = None
    volume_change_pct: Optional[Decimal] = None
    pressure_indicator: Optional[str] = None
    is_volume_anomaly: bool = False
    anomaly_threshold: Optional[Decimal] = None
    news_count: int = 0
    news_sentiment_score: Optional[Decimal] = None
    next_day_price_change_pct: Optional[Decimal] = None
    next_day_volume_change_pct: Optional[Decimal] = None
    snapshot_payload: dict[str, object] = Field(default_factory=dict)


class CorrelationPoint(BaseModel):
    trading_date: date
    news_count: int
    news_sentiment_score: Optional[Decimal] = None
    next_day_price_change_pct: Optional[Decimal] = None
    next_day_volume_change_pct: Optional[Decimal] = None


class NewsPriceCorrelationResponse(BaseModel):
    company_id: int
    items: list[CorrelationPoint]
