from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.permissions import RoleName, require_role
from app.models.user import User
from app.repositories.admin_repository import create_crawl_run, get_crawl_run_by_id, list_crawl_runs
from app.repositories.user_repository import list_users
from app.schemas.admin import CrawlRunListResponse, CrawlRunRequest, CrawlRunResponse, UserListResponse, UserSummaryResponse
from app.services.crawl_service import execute_crawl_run
from app.tasks.crawl_tasks import run_crawl_pipeline

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/crawl-runs", response_model=CrawlRunResponse)
async def trigger_crawl_run(
    payload: CrawlRunRequest,
    execute_now: bool = Query(default=False),
    db: Session = Depends(get_db_session),
    user: User = Depends(require_role(RoleName.ADMIN)),
) -> CrawlRunResponse:
    crawl_run = create_crawl_run(
        db,
        run_kind=payload.run_kind,
        requested_sources=payload.sources,
        triggered_by_user_id=user.id,
    )
    if execute_now:
        crawl_run = execute_crawl_run(db, crawl_run.id)
    else:
        try:
            run_crawl_pipeline.delay(crawl_run.id)
        except Exception as exc:
            crawl_run.status = "failed"
            crawl_run.error_message = f"Unable to enqueue crawl run: {exc}"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to enqueue crawl run. Ensure Redis and the Celery worker are running.",
            ) from exc

    return CrawlRunResponse(
        id=crawl_run.id,
        run_kind=crawl_run.run_kind,
        status=crawl_run.status,
        requested_sources=crawl_run.requested_sources,
        error_message=crawl_run.error_message,
        run_stats=crawl_run.run_stats,
        started_at=crawl_run.started_at,
        finished_at=crawl_run.finished_at,
        triggered_by_user_id=crawl_run.triggered_by_user_id,
        requested_by=user.email,
    )


@router.get("/crawl-runs", response_model=CrawlRunListResponse)
async def list_crawl_runs_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN)),
) -> CrawlRunListResponse:
    crawl_runs = list_crawl_runs(db, limit=limit)
    return CrawlRunListResponse(
        items=[
            CrawlRunResponse(
                id=crawl_run.id,
                run_kind=crawl_run.run_kind,
                status=crawl_run.status,
                requested_sources=crawl_run.requested_sources,
                error_message=crawl_run.error_message,
                run_stats=crawl_run.run_stats,
                started_at=crawl_run.started_at,
                finished_at=crawl_run.finished_at,
                triggered_by_user_id=crawl_run.triggered_by_user_id,
                requested_by=crawl_run.triggered_by.email if crawl_run.triggered_by else None,
            )
            for crawl_run in crawl_runs
        ]
    )


@router.get("/crawl-runs/{crawl_run_id}", response_model=CrawlRunResponse)
async def get_crawl_run_status(
    crawl_run_id: int,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN)),
) -> CrawlRunResponse:
    crawl_run = get_crawl_run_by_id(db, crawl_run_id)
    if crawl_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crawl run not found.")
    return CrawlRunResponse(
        id=crawl_run.id,
        run_kind=crawl_run.run_kind,
        status=crawl_run.status,
        requested_sources=crawl_run.requested_sources,
        error_message=crawl_run.error_message,
        run_stats=crawl_run.run_stats,
        started_at=crawl_run.started_at,
        finished_at=crawl_run.finished_at,
        triggered_by_user_id=crawl_run.triggered_by_user_id,
        requested_by=crawl_run.triggered_by.email if crawl_run.triggered_by else None,
    )


@router.get("/users", response_model=UserListResponse)
async def list_users_endpoint(
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN)),
) -> UserListResponse:
    users = list_users(db)
    return UserListResponse(
        items=[
            UserSummaryResponse(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                is_active=user.is_active,
                role=user.role.name,
                last_login_at=user.last_login_at,
            )
            for user in users
        ]
    )
