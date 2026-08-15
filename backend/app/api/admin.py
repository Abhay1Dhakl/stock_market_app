from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.permissions import RoleName, require_role
from app.core.security import get_password_hash
from app.models import Company
from app.repositories.company_repository import get_company_by_id, get_company_by_symbol, list_companies
from app.models.user import User
from app.repositories.admin_repository import create_crawl_run, get_crawl_run_by_id, list_crawl_runs
from app.repositories.user_repository import get_role_by_name, get_user_by_email, list_users
from app.schemas.behavior import AdminUserBehaviorResponse
from app.schemas.admin import (
    CrawlRunListResponse,
    CrawlRunRequest,
    CrawlRunResponse,
    UserCreateRequest,
    UserListResponse,
    UserSummaryResponse,
)
from app.schemas.company import CompanyCreateRequest, CompanyListResponse, CompanySummary, CompanyUpdateRequest
from app.services.crawl_service import execute_crawl_run
from app.services.user_behavior_service import build_admin_user_behavior_overview, record_user_event
from app.tasks.crawl_tasks import run_crawl_pipeline

router = APIRouter(prefix="/admin", tags=["admin"])


def _serialize_user(user: User) -> UserSummaryResponse:
    return UserSummaryResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        role=user.role.name,
        last_login_at=user.last_login_at,
    )


def _serialize_company(company) -> CompanySummary:
    return CompanySummary.model_validate(company)


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

    record_user_event(
        db,
        user_id=user.id,
        event_type="crawl_triggered",
        page_path="/admin",
        metadata={"run_kind": payload.run_kind, "sources": payload.sources, "execute_now": execute_now},
    )

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
    return UserListResponse(items=[_serialize_user(user) for user in users])


@router.get("/user-behavior", response_model=AdminUserBehaviorResponse)
async def list_user_behavior_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN)),
) -> AdminUserBehaviorResponse:
    return AdminUserBehaviorResponse(items=build_admin_user_behavior_overview(db, limit=limit))


@router.get("/companies", response_model=CompanyListResponse)
async def list_companies_endpoint(
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN)),
) -> CompanyListResponse:
    companies = list_companies(db)
    return CompanyListResponse(items=[_serialize_company(company) for company in companies])


@router.post("/companies", response_model=CompanySummary, status_code=status.HTTP_201_CREATED)
async def create_company_endpoint(
    payload: CompanyCreateRequest,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN)),
) -> CompanySummary:
    normalized_symbol = payload.symbol.strip().upper()
    existing_company = get_company_by_symbol(db, normalized_symbol)
    if existing_company is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A company with this symbol already exists.")

    created_company = Company(
        symbol=normalized_symbol,
        name=payload.name.strip(),
        sector=payload.sector.strip(),
        aliases=_normalize_aliases(payload.aliases),
        description=payload.description.strip() if payload.description else None,
        is_active=payload.is_active,
        source_kind="admin",
        coverage_status="pending",
    )
    db.add(created_company)
    db.commit()
    db.refresh(created_company)
    return _serialize_company(created_company)


@router.patch("/companies/{company_id}", response_model=CompanySummary)
async def update_company_endpoint(
    company_id: int,
    payload: CompanyUpdateRequest,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN)),
) -> CompanySummary:
    company = get_company_by_id(db, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")

    if "name" in payload.model_fields_set:
        company.name = payload.name.strip() if payload.name is not None else company.name
    if "sector" in payload.model_fields_set:
        company.sector = payload.sector.strip() if payload.sector is not None else company.sector
    if "aliases" in payload.model_fields_set:
        company.aliases = _normalize_aliases(payload.aliases or [])
    if "description" in payload.model_fields_set:
        company.description = payload.description.strip() if payload.description else None
    if "is_active" in payload.model_fields_set and payload.is_active is not None:
        company.is_active = payload.is_active

    db.commit()
    db.refresh(company)
    return _serialize_company(company)


@router.post("/users", response_model=UserSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    payload: UserCreateRequest,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN)),
) -> UserSummaryResponse:
    existing_user = get_user_by_email(db, payload.email)
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")

    role = get_role_by_name(db, payload.role)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested role was not found.")

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.strip().lower(),
        password_hash=get_password_hash(payload.password),
        role_id=role.id,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    created_user = get_user_by_email(db, user.email)
    if created_user is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User creation failed.")
    return _serialize_user(created_user)


def _normalize_aliases(values: list[str]) -> list[str]:
    aliases: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        aliases.append(normalized)
    return aliases
