from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis_snapshot import CompanyAnalysisSnapshot
from app.models.company import Company
from app.models.market_data import DailyPrice, FloorsheetTransaction


def list_active_companies(db: Session) -> list[Company]:
    statement = select(Company).where(Company.is_active.is_(True)).order_by(Company.symbol.asc())
    return list(db.scalars(statement).all())


def get_company_by_id(db: Session, company_id: int) -> Optional[Company]:
    return db.get(Company, company_id)


def list_company_prices(db: Session, company_id: int, limit: int) -> list[DailyPrice]:
    statement = (
        select(DailyPrice)
        .where(DailyPrice.company_id == company_id)
        .order_by(DailyPrice.trading_date.desc())
        .limit(limit)
    )
    rows = list(db.scalars(statement).all())
    rows.reverse()
    return rows


def list_company_floorsheet(
    db: Session,
    company_id: int,
    trading_date: Optional[date],
) -> Tuple[Optional[date], list[FloorsheetTransaction]]:
    target_date = trading_date
    if target_date is None:
        latest_date_statement = (
            select(FloorsheetTransaction.trading_date)
            .where(FloorsheetTransaction.company_id == company_id)
            .order_by(FloorsheetTransaction.trading_date.desc())
            .limit(1)
        )
        target_date = db.scalar(latest_date_statement)

    if target_date is None:
        return None, []

    statement = (
        select(FloorsheetTransaction)
        .where(
            FloorsheetTransaction.company_id == company_id,
            FloorsheetTransaction.trading_date == target_date,
        )
        .order_by(FloorsheetTransaction.transaction_time.asc(), FloorsheetTransaction.id.asc())
    )
    return target_date, list(db.scalars(statement).all())


def get_latest_analysis_snapshot(db: Session, company_id: int) -> Optional[CompanyAnalysisSnapshot]:
    statement = (
        select(CompanyAnalysisSnapshot)
        .where(CompanyAnalysisSnapshot.company_id == company_id)
        .order_by(CompanyAnalysisSnapshot.trading_date.desc())
        .limit(1)
    )
    return db.scalar(statement)


def list_analysis_snapshots(
    db: Session,
    company_id: int,
    limit: int = 30,
) -> list[CompanyAnalysisSnapshot]:
    statement = (
        select(CompanyAnalysisSnapshot)
        .where(CompanyAnalysisSnapshot.company_id == company_id)
        .order_by(CompanyAnalysisSnapshot.trading_date.desc())
        .limit(limit)
    )
    rows = list(db.scalars(statement).all())
    rows.reverse()
    return rows
