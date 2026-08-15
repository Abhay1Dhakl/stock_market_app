from __future__ import annotations

from datetime import date as calendar_date
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CompanySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    sector: str
    aliases: list[str]
    description: Optional[str] = None
    is_active: bool
    source_kind: str
    coverage_status: str
    last_refresh_at: Optional[datetime] = None
    last_refresh_error: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(BaseModel):
    items: list[CompanySummary]


class CompanyCreateRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=25)
    name: str = Field(min_length=2, max_length=255)
    sector: str = Field(min_length=2, max_length=100)
    aliases: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    is_active: bool = True


class CompanyUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    sector: Optional[str] = Field(default=None, min_length=2, max_length=100)
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DailyPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trading_date: calendar_date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    turnover: Decimal
    source_name: Optional[str] = None


class CompanyPricesResponse(BaseModel):
    company_id: int
    range: str
    items: list[DailyPriceResponse]


class FloorsheetTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trading_date: calendar_date
    transaction_time: Optional[datetime] = None
    buyer_broker_code: str
    seller_broker_code: str
    quantity: int
    rate: Decimal
    amount: Decimal
    source_name: Optional[str] = None


class CompanyFloorsheetResponse(BaseModel):
    company_id: int
    date: Optional[calendar_date] = None
    items: list[FloorsheetTransactionResponse]
