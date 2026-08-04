from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.permissions import Role, require_role

router = APIRouter(prefix="/admin", tags=["admin"])


class CrawlRunRequest(BaseModel):
    sources: List[str] = Field(default_factory=lambda: ["merolagani", "sharesansar"])
    full_refresh: bool = False


@router.post("/crawl-runs")
async def trigger_crawl_run(
    payload: CrawlRunRequest,
    user: dict = Depends(require_role(Role.ADMIN)),
) -> dict:
    return {
        "id": "scaffold-crawl-run",
        "requested_by": user["email"],
        "sources": payload.sources,
        "full_refresh": payload.full_refresh,
        "status": "queued",
    }


@router.get("/crawl-runs/{crawl_run_id}")
async def get_crawl_run_status(crawl_run_id: str) -> dict:
    return {
        "id": crawl_run_id,
        "status": "not_implemented",
        "message": "Crawl run tracking will be backed by the database and Celery state.",
    }


@router.get("/users")
async def list_users(user: dict = Depends(require_role(Role.ADMIN))) -> dict:
    return {
        "requested_by": user["email"],
        "items": [],
        "message": "User and role management endpoint scaffolded.",
    }

