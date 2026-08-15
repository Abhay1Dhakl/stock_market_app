from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.permissions import RoleName, require_role
from app.models.news import NewsCompanyTag, NewsTagCorrection
from app.models.user import User
from app.repositories.news_repository import get_news_article_by_id, list_companies_by_ids, list_news_articles
from app.services.categorization_service import REVIEW_CONFIDENCE_THRESHOLD, list_review_queue_articles
from app.services.user_behavior_service import record_user_event
from app.schemas.news import (
    NewsArticleSummary,
    NewsListResponse,
    NewsRecategorizeResponse,
    RecategorizeRequest,
    TaggedCompanySummary,
)

router = APIRouter(prefix="/news", tags=["news"])


def _serialize_tag(tag: NewsCompanyTag) -> TaggedCompanySummary:
    return TaggedCompanySummary(
        company_id=tag.company_id,
        symbol=tag.company.symbol,
        name=tag.company.name,
        confidence_score=tag.confidence_score,
        tag_source=tag.tag_source,
        match_summary=tag.match_summary,
    )


def _serialize_article(article) -> NewsArticleSummary:
    tags = sorted(article.tags, key=lambda item: item.company.symbol)
    return NewsArticleSummary(
        id=article.id,
        source_name=article.source_name,
        source_url=article.source_url,
        headline=article.headline,
        excerpt=article.excerpt,
        published_at=article.published_at,
        crawled_at=article.crawled_at,
        sentiment_label=article.sentiment_label,
        tags=[_serialize_tag(tag) for tag in tags],
    )


@router.get("", response_model=NewsListResponse)
async def list_news(
    company_id: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST, RoleName.VIEWER)),
) -> NewsListResponse:
    articles = list_news_articles(db, company_id=company_id, limit=limit)
    return NewsListResponse(company_id=company_id, items=[_serialize_article(article) for article in articles])


@router.get("/review-queue", response_model=NewsListResponse)
async def get_review_queue(
    limit: int = Query(default=50, ge=1, le=200),
    confidence_threshold: Decimal = Query(default=REVIEW_CONFIDENCE_THRESHOLD, ge=0, le=1),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST)),
) -> NewsListResponse:
    articles = list_review_queue_articles(db, threshold=confidence_threshold, limit=limit)
    return NewsListResponse(items=[_serialize_article(article) for article in articles])


@router.post("/{news_id}/recategorize", response_model=NewsRecategorizeResponse)
async def recategorize_news(
    news_id: int,
    payload: RecategorizeRequest,
    db: Session = Depends(get_db_session),
    reviewer: User = Depends(require_role(RoleName.ADMIN, RoleName.ANALYST)),
) -> NewsRecategorizeResponse:
    article = get_news_article_by_id(db, news_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News article not found.")

    unique_company_ids = list(dict.fromkeys(payload.company_ids))
    companies = list_companies_by_ids(db, unique_company_ids)
    if len(companies) != len(unique_company_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more companies were not found.")

    previous_tags = [_serialize_tag(tag).model_dump(mode="json") for tag in article.tags]

    for existing_tag in list(article.tags):
        db.delete(existing_tag)
    db.flush()

    for company in companies:
        db.add(
            NewsCompanyTag(
                news_article_id=article.id,
                company_id=company.id,
                confidence_score=Decimal("1.0"),
                tag_source="manual",
                match_summary="Manual analyst correction",
                created_by_user_id=reviewer.id,
            )
        )

    updated_tags = [
        {
            "company_id": company.id,
            "symbol": company.symbol,
            "name": company.name,
            "confidence_score": "1.0",
            "tag_source": "manual",
        }
        for company in companies
    ]
    correction = NewsTagCorrection(
        news_article_id=article.id,
        reviewer_user_id=reviewer.id,
        previous_tags=previous_tags,
        updated_tags=updated_tags,
        notes=payload.notes,
    )
    db.add(correction)
    record_user_event(
        db,
        user_id=reviewer.id,
        event_type="review_saved",
        page_path="/review",
        article_id=article.id,
        metadata={"company_ids": unique_company_ids},
        notes=payload.notes,
        commit=False,
    )
    db.commit()
    db.refresh(correction)

    return NewsRecategorizeResponse(
        news_id=article.id,
        company_ids=unique_company_ids,
        correction_id=correction.id,
        reviewed_by=reviewer.email,
        notes=payload.notes,
    )
