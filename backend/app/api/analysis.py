from fastapi import APIRouter

router = APIRouter(prefix="/companies", tags=["analysis"])


@router.get("/{company_id}/behavior-summary")
async def get_behavior_summary(company_id: int) -> dict:
    return {
        "company_id": company_id,
        "summary": {},
        "message": "Behavior summary endpoint scaffolded.",
    }


@router.get("/{company_id}/news-price-correlation")
async def get_news_price_correlation(company_id: int) -> dict:
    return {
        "company_id": company_id,
        "correlation": {},
        "message": "News-price correlation endpoint scaffolded.",
    }

