from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CompanySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    sector: str
    aliases: list[str]
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(BaseModel):
    items: list[CompanySummary]


class DailyPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trading_date: date
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

    trading_date: date
    transaction_time: Optional[datetime] = None
    buyer_broker_code: str
    seller_broker_code: str
    quantity: int
    rate: Decimal
    amount: Decimal
    source_name: Optional[str] = None


class CompanyFloorsheetResponse(BaseModel):
    company_id: int
    date: Optional[date] = None
    items: list[FloorsheetTransactionResponse]
