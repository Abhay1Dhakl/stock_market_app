from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.permissions import RoleName, require_role
from app.models.user import User
from app.schemas.behavior import UserBehaviorSummaryResponse
from app.schemas.company import CompanySummary
from app.schemas.watchlist import DiscoveryFeedResponse, UserWatchlistResponse, WatchlistMutationRequest
from app.services.user_behavior_service import build_user_behavior_summary
from app.services.watchlist_service import (
    add_company_to_watchlist,
    build_discovery_feed,
    build_user_watchlist_insights,
    remove_company_from_watchlist,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/watchlist", response_model=UserWatchlistResponse)
async def get_my_watchlist(
    db: Session = Depends(get_db_session),
    user: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> UserWatchlistResponse:
    return UserWatchlistResponse(items=build_user_watchlist_insights(db, user=user))


@router.post("/me/watchlist", response_model=CompanySummary, status_code=status.HTTP_201_CREATED)
async def add_to_my_watchlist(
    payload: WatchlistMutationRequest,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> CompanySummary:
    try:
        company = add_company_to_watchlist(
            db,
            user=user,
            company_id=payload.company_id,
            symbol=payload.symbol,
            name=payload.name,
            sector=payload.sector,
            aliases=payload.aliases,
            description=payload.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return CompanySummary.model_validate(company)


@router.delete("/me/watchlist/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_my_watchlist(
    company_id: int,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> Response:
    remove_company_from_watchlist(db, user=user, company_id=company_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/discovery-feed", response_model=DiscoveryFeedResponse)
async def get_my_discovery_feed(
    db: Session = Depends(get_db_session),
    user: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> DiscoveryFeedResponse:
    return DiscoveryFeedResponse(items=build_discovery_feed(db, user=user))


@router.get("/me/behavior-summary", response_model=UserBehaviorSummaryResponse)
async def get_my_behavior_summary(
    db: Session = Depends(get_db_session),
    user: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> UserBehaviorSummaryResponse:
    return UserBehaviorSummaryResponse(**build_user_behavior_summary(db, user))
