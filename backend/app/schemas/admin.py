from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.behavior import AdminUserBehaviorResponse


class CrawlRunRequest(BaseModel):
    sources: list[str] = Field(default_factory=lambda: ["merolagani", "sharesansar"])
    run_kind: Literal["news", "market_data", "full"] = "full"


class CrawlRunResponse(BaseModel):
    id: int
    run_kind: str
    status: str
    requested_sources: list[str]
    error_message: Optional[str] = None
    run_stats: dict[str, object]
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    triggered_by_user_id: Optional[int] = None
    requested_by: Optional[str] = None


class CrawlRunListResponse(BaseModel):
    items: list[CrawlRunResponse]


class UserCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["admin", "analyst", "viewer"]
    is_active: bool = True


class UserSummaryResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    role: str
    last_login_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    items: list[UserSummaryResponse]
