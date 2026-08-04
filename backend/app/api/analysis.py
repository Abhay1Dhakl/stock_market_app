from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.permissions import RoleName, require_role
from app.models.user import User
from app.repositories.company_repository import get_company_by_id, get_latest_analysis_snapshot, list_analysis_snapshots
from app.schemas.analysis import BehaviorSummaryResponse, CorrelationPoint, NewsPriceCorrelationResponse


router = APIRouter(prefix="/companies", tags=["analysis"])


def _ensure_company_exists(db: Session, company_id: int) -> None:
    if get_company_by_id(db, company_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")


@router.get("/{company_id}/behavior-summary", response_model=BehaviorSummaryResponse)
async def get_behavior_summary(
    company_id: int,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> BehaviorSummaryResponse:
    _ensure_company_exists(db, company_id)
    snapshot = get_latest_analysis_snapshot(db, company_id)
    if snapshot is None:
        return BehaviorSummaryResponse(company_id=company_id)

    return BehaviorSummaryResponse(
        company_id=company_id,
        trading_date=snapshot.trading_date,
        close_price=snapshot.close_price,
        vwap=snapshot.vwap,
        price_change_pct=snapshot.price_change_pct,
        volume_change_pct=snapshot.volume_change_pct,
        pressure_indicator=snapshot.pressure_indicator,
        is_volume_anomaly=snapshot.is_volume_anomaly,
        anomaly_threshold=snapshot.anomaly_threshold,
        news_count=snapshot.news_count,
        news_sentiment_score=snapshot.news_sentiment_score,
        next_day_price_change_pct=snapshot.next_day_price_change_pct,
        next_day_volume_change_pct=snapshot.next_day_volume_change_pct,
        snapshot_payload=snapshot.snapshot_payload,
    )


@router.get("/{company_id}/news-price-correlation", response_model=NewsPriceCorrelationResponse)
async def get_news_price_correlation(
    company_id: int,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> NewsPriceCorrelationResponse:
    _ensure_company_exists(db, company_id)
    snapshots = list_analysis_snapshots(db, company_id, limit=30)
    return NewsPriceCorrelationResponse(
        company_id=company_id,
        items=[
            CorrelationPoint(
                trading_date=snapshot.trading_date,
                news_count=snapshot.news_count,
                news_sentiment_score=snapshot.news_sentiment_score,
                next_day_price_change_pct=snapshot.next_day_price_change_pct,
                next_day_volume_change_pct=snapshot.next_day_volume_change_pct,
            )
            for snapshot in snapshots
        ],
    )
