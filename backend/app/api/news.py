from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.permissions import Role, require_role

router = APIRouter(prefix="/news", tags=["news"])


class RecategorizeRequest(BaseModel):
    company_ids: List[int]
    notes: Optional[str] = None


@router.get("")
async def list_news(company_id: Optional[int] = None) -> dict:
    return {
        "company_id": company_id,
        "items": [],
        "message": "Categorized news feed endpoint scaffolded.",
    }


@router.post("/{news_id}/recategorize")
async def recategorize_news(
    news_id: int,
    payload: RecategorizeRequest,
    reviewer: dict = Depends(require_role(Role.ADMIN, Role.ANALYST)),
) -> dict:
    return {
        "news_id": news_id,
        "company_ids": payload.company_ids,
        "notes": payload.notes,
        "reviewed_by": reviewer["email"],
        "message": "Manual recategorization flow scaffolded.",
    }

