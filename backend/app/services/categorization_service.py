from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.categorization.entity_matcher import WatchlistEntityMatcher
from app.categorization.sentiment import score_sentiment
from app.models import Company, NewsArticle, NewsCompanyTag

REVIEW_CONFIDENCE_THRESHOLD = Decimal("0.65")


def categorize_news_articles(
    db: Session,
    *,
    article_ids: list[int] | None = None,
    only_missing: bool = False,
) -> dict[str, int]:
    companies = list(db.scalars(select(Company).where(Company.is_active.is_(True)).order_by(Company.symbol.asc())).all())
    if not companies:
        return {"processed": 0, "tagged": 0, "manual_skipped": 0, "review_candidates": 0}

    statement = select(NewsArticle).options(selectinload(NewsArticle.tags).selectinload(NewsCompanyTag.company))
    if article_ids:
        statement = statement.where(NewsArticle.id.in_(article_ids))
    articles = list(db.scalars(statement.order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())).unique().all())

    matcher = WatchlistEntityMatcher(companies)
    processed = 0
    tagged = 0
    manual_skipped = 0
    review_candidates = 0

    for article in articles:
        if only_missing and article.tags:
            continue

        article.sentiment_label = score_sentiment(f"{article.headline}\n{article.body_text}")
        manual_tags = [tag for tag in article.tags if tag.tag_source == "manual"]
        if manual_tags:
            manual_skipped += 1
            processed += 1
            continue

        matches = matcher.match(article.headline, article.body_text)

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

        if not matches or any(Decimal(f"{match.confidence_score:.4f}") < REVIEW_CONFIDENCE_THRESHOLD for match in matches):
            review_candidates += 1

        processed += 1

    if processed:
        db.commit()

    return {
        "processed": processed,
        "tagged": tagged,
        "manual_skipped": manual_skipped,
        "review_candidates": review_candidates,
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
