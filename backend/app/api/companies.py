from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
async def list_companies() -> dict:
    return {
        "items": [],
        "message": "Tracked companies will be loaded from PostgreSQL in the next phase.",
    }


@router.get("/{company_id}/prices")
async def get_company_prices(
    company_id: int,
    time_range: str = Query(default="30d", alias="range"),
) -> dict:
    return {
        "company_id": company_id,
        "range": time_range,
        "items": [],
        "message": "Daily OHLCV endpoint scaffolded.",
    }


@router.get("/{company_id}/floorsheet")
async def get_company_floorsheet(company_id: int, date_filter: Optional[date] = Query(default=None, alias="date")) -> dict:
    return {
        "company_id": company_id,
        "date": date_filter,
        "items": [],
        "message": "Floorsheet endpoint scaffolded.",
    }

