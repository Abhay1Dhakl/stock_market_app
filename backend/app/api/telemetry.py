from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.permissions import RoleName, require_role
from app.models import Company, NewsArticle
from app.models.user import User
from app.schemas.behavior import TelemetryEventRequest, TelemetryEventResponse
from app.services.user_behavior_service import record_user_event

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/events", response_model=TelemetryEventResponse, status_code=status.HTTP_201_CREATED)
async def record_event(
    payload: TelemetryEventRequest,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> TelemetryEventResponse:
    if payload.company_id is not None and db.get(Company, payload.company_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    if payload.article_id is not None and db.get(NewsArticle, payload.article_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News article not found.")

    event = record_user_event(
        db,
        user_id=user.id,
        event_type=payload.event_type,
        page_path=payload.page_path,
        company_id=payload.company_id,
        article_id=payload.article_id,
        metadata=payload.metadata,
        notes=payload.notes,
    )
    return TelemetryEventResponse(id=event.id, event_type=event.event_type)
