from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.permissions import RoleName, require_role
from app.models.user import User
from app.services.report_service import build_watchlist_summary_csv
from app.services.user_behavior_service import record_user_event

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/watchlist-summary.csv")
async def export_watchlist_summary(
    db: Session = Depends(get_db_session),
    user: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> Response:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_payload = build_watchlist_summary_csv(db)
    record_user_event(
        db,
        user_id=user.id,
        event_type="report_export",
        page_path="/dashboard",
        metadata={"report": "watchlist-summary"},
    )
    return Response(
        content=csv_payload,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="watchlist-summary-{timestamp}.csv"'},
    )
