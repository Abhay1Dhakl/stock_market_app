from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.categorization.entity_matcher import WatchlistEntityMatcher
from app.categorization.gemini_matcher import GeminiWatchlistMatcher
from app.categorization.sentiment import score_sentiment
from app.core.config import settings
from app.models import Company, NewsArticle, NewsCompanyTag

REVIEW_CONFIDENCE_THRESHOLD = Decimal("0.65")
logger = logging.getLogger(__name__)


def categorize_news_articles(
    db: Session,
    *,
    article_ids: list[int] | None = None,
    only_missing: bool = False,
) -> dict[str, int]:
    companies = list(db.scalars(select(Company).where(Company.is_active.is_(True)).order_by(Company.symbol.asc())).all())
    if not companies:
        return {
            "processed": 0,
            "tagged": 0,
            "manual_skipped": 0,
            "review_candidates": 0,
            "provider": "rule_based",
            "fallback_articles": 0,
        }

    statement = select(NewsArticle).options(selectinload(NewsArticle.tags).selectinload(NewsCompanyTag.company))
    if article_ids:
        statement = statement.where(NewsArticle.id.in_(article_ids))
    articles = list(db.scalars(statement.order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())).unique().all())

    rule_matcher = WatchlistEntityMatcher(companies)
    gemini_matcher = _build_categorization_matcher(companies)
    processed = 0
    tagged = 0
    manual_skipped = 0
    review_candidates = 0
    fallback_articles = 0

    try:
        for article in articles:
            if only_missing and article.tags:
                continue

            article.sentiment_label = score_sentiment(f"{article.headline}\n{article.body_text}")
            manual_tags = [tag for tag in article.tags if tag.tag_source == "manual"]
            if manual_tags:
                manual_skipped += 1
                processed += 1
                continue

            try:
                matches = (
                    gemini_matcher.match(article.headline, article.body_text)
                    if gemini_matcher is not None
                    else rule_matcher.match(article.headline, article.body_text)
                )
            except Exception as exc:
                logger.warning("Gemini categorization failed for article %s, falling back to rules: %s", article.id, exc)
                matches = rule_matcher.match(article.headline, article.body_text)
                fallback_articles += 1

            for existing_tag in [tag for tag in article.tags if tag.tag_source == "system"]:
                db.delete(existing_tag)
            db.flush()

            for match in matches:
                confidence = Decimal(f"{match.confidence_score:.4f}")
                db.add(
                    NewsCompanyTag(
                        news_article_id=article.id,
                        company_id=match.company_id,
                        confidence_score=confidence,
                        tag_source="system",
                        match_summary=match.match_summary,
                        created_by_user_id=None,
                    )
                )
                tagged += 1

            if not matches or any(
                Decimal(f"{match.confidence_score:.4f}") < REVIEW_CONFIDENCE_THRESHOLD for match in matches
            ):
                review_candidates += 1

            processed += 1
    finally:
        if gemini_matcher is not None:
            gemini_matcher.close()

    if processed:
        db.commit()

    return {
        "processed": processed,
        "tagged": tagged,
        "manual_skipped": manual_skipped,
        "review_candidates": review_candidates,
        "provider": "gemini" if gemini_matcher is not None else "rule_based",
        "fallback_articles": fallback_articles,
    }


def list_review_queue_articles(
    db: Session,
    *,
    threshold: Decimal = REVIEW_CONFIDENCE_THRESHOLD,
    limit: int = 50,
) -> list[NewsArticle]:
    articles = list(
        db.scalars(
            select(NewsArticle)
            .options(selectinload(NewsArticle.tags).selectinload(NewsCompanyTag.company))
            .order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())
        )
        .unique()
        .all()
    )

    queued: list[NewsArticle] = []
    for article in articles:
        if not article.tags:
            queued.append(article)
            continue

        manual_tags = [tag for tag in article.tags if tag.tag_source == "manual"]
        if manual_tags:
            continue

        if any(tag.confidence_score < threshold for tag in article.tags):
            queued.append(article)

        if len(queued) >= limit:
            break

    return queued[:limit]


def _build_categorization_matcher(companies: list[Company]) -> GeminiWatchlistMatcher | None:
    provider = settings.categorization_provider.strip().lower()
    if provider != "gemini":
        return None

    if not settings.gemini_api_key:
        logger.warning("CATEGORIZATION_PROVIDER=gemini but GEMINI_API_KEY is missing. Falling back to rule-based matching.")
        return None

    return GeminiWatchlistMatcher(
        companies,
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.gemini_timeout_seconds,
    )
