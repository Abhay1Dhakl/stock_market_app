from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import or_, select
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
    """Tag articles against the active watchlist and persist confidence scores.

    Args:
        db: Active SQLAlchemy session used for article and tag writes.
        article_ids: Optional subset of article IDs to process.
        only_missing: When `True`, skip articles that already have tags.

    Returns:
        dict[str, int]: Categorization counters including processed, tagged,
        review-candidate, and fallback totals.
    """
    companies = list(
        db.scalars(
            select(Company)
            .where(or_(Company.is_active.is_(True), Company.source_kind == "directory"))
            .order_by(Company.symbol.asc())
        ).all()
    )
    if not companies:
        return {
            "processed": 0,
            "tagged": 0,
            "manual_skipped": 0,
            "review_candidates": 0,
            "provider": "rule_based",
            "fallback_articles": 0,
            "promoted_companies": 0,
            "promoted_company_ids": [],
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
    promoted_company_ids: set[int] = set()
    company_lookup = {company.id: company for company in companies}

    try:
        for article in articles:
            if only_missing and article.tags:
                continue

            article.sentiment_label = score_sentiment(f"{article.headline}\n{article.body_text}")
            # Preserve analyst corrections as the source of truth over rerun automation.
            manual_tags = [tag for tag in article.tags if tag.tag_source == "manual"]
            if manual_tags:
                manual_skipped += 1
                processed += 1
                continue

            try:
                # Prefer the configured LLM matcher, but keep deterministic fallback coverage.
                matches = (
                    gemini_matcher.match(article.headline, article.body_text)
                    if gemini_matcher is not None
                    else rule_matcher.match(article.headline, article.body_text)
                )
            except Exception as exc:
                logger.warning("Gemini categorization failed for article %s, falling back to rules: %s", article.id, exc)
                matches = rule_matcher.match(article.headline, article.body_text)
                fallback_articles += 1

            # Replace only system tags so repeated runs never erase manual review decisions.
            for existing_tag in [tag for tag in article.tags if tag.tag_source == "system"]:
                db.delete(existing_tag)
            db.flush()

            for match in matches:
                confidence = Decimal(f"{match.confidence_score:.4f}")
                company = company_lookup.get(match.company_id)
                if company is not None and company.source_kind == "directory" and not company.is_active:
                    company.is_active = True
                    company.coverage_status = "pending"
                    db.add(company)
                    promoted_company_ids.add(company.id)
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
        "promoted_companies": len(promoted_company_ids),
        "promoted_company_ids": sorted(promoted_company_ids),
    }


def list_review_queue_articles(
    db: Session,
    *,
    threshold: Decimal = REVIEW_CONFIDENCE_THRESHOLD,
    limit: int = 50,
) -> list[NewsArticle]:
    """Collect articles that still need analyst review.

    Args:
        db: Active SQLAlchemy session used for article reads.
        threshold: Minimum acceptable confidence before review is required.
        limit: Maximum number of queued articles to return.

    Returns:
        list[NewsArticle]: Ordered review-queue articles for the UI/API.
    """
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
    """Build the configured categorization provider for the active watchlist.

    Args:
        companies: Active watchlist companies exposed to the matcher.

    Returns:
        GeminiWatchlistMatcher | None: Configured Gemini matcher when enabled
        and fully configured, otherwise `None` to force rule-based matching.
    """
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
