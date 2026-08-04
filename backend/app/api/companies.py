from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.permissions import RoleName, require_role
from app.models.user import User
from app.repositories.company_repository import (
    get_company_by_id,
    list_active_companies,
    list_company_floorsheet,
    list_company_prices,
)
from app.schemas.company import (
    CompanyFloorsheetResponse,
    CompanyListResponse,
    CompanyPricesResponse,
    CompanySummary,
    DailyPriceResponse,
    FloorsheetTransactionResponse,
)

router = APIRouter(prefix="/companies", tags=["companies"])


def _parse_range_limit(time_range: str) -> int:
    normalized = time_range.strip().lower()
    if not normalized.endswith("d") or not normalized[:-1].isdigit():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Range must use the form '<days>d', for example '30d'.",
        )
    return min(max(int(normalized[:-1]), 1), 365)


def _get_company_or_404(db: Session, company_id: int):
    company = get_company_by_id(db, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return company


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> CompanyListResponse:
    companies = list_active_companies(db)
    return CompanyListResponse(items=[CompanySummary.model_validate(company) for company in companies])


@router.get("/{company_id}", response_model=CompanySummary)
async def get_company(
    company_id: int,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> CompanySummary:
    company = _get_company_or_404(db, company_id)
    return CompanySummary.model_validate(company)


@router.get("/{company_id}/prices", response_model=CompanyPricesResponse)
async def get_company_prices(
    company_id: int,
    time_range: str = Query(default="30d", alias="range"),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> CompanyPricesResponse:
    _get_company_or_404(db, company_id)
    rows = list_company_prices(db, company_id, _parse_range_limit(time_range))
    return CompanyPricesResponse(
        company_id=company_id,
        range=time_range,
        items=[DailyPriceResponse.model_validate(row) for row in rows],
    )


@router.get("/{company_id}/floorsheet", response_model=CompanyFloorsheetResponse)
async def get_company_floorsheet(
    company_id: int,
    date_filter: Optional[date] = Query(default=None, alias="date"),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> CompanyFloorsheetResponse:
    _get_company_or_404(db, company_id)
    selected_date, rows = list_company_floorsheet(db, company_id, date_filter)
    return CompanyFloorsheetResponse(
        company_id=company_id,
        date=selected_date,
        items=[FloorsheetTransactionResponse.model_validate(row) for row in rows],
    )
