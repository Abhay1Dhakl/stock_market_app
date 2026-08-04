from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.company import Company
from app.models.news import NewsArticle, NewsCompanyTag


def list_news_articles(
    db: Session,
    company_id: Optional[int] = None,
    limit: int = 50,
) -> list[NewsArticle]:
    statement = (
        select(NewsArticle)
        .options(selectinload(NewsArticle.tags).selectinload(NewsCompanyTag.company))
        .order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())
        .limit(limit)
    )
    if company_id is not None:
        statement = statement.join(NewsCompanyTag).where(NewsCompanyTag.company_id == company_id)
    return list(db.scalars(statement).unique().all())


def get_news_article_by_id(db: Session, news_id: int) -> Optional[NewsArticle]:
    statement = (
        select(NewsArticle)
        .options(selectinload(NewsArticle.tags).selectinload(NewsCompanyTag.company))
        .where(NewsArticle.id == news_id)
    )
    return db.scalar(statement)


def list_companies_by_ids(db: Session, company_ids: list[int]) -> list[Company]:
    if not company_ids:
        return []
    statement = select(Company).where(Company.id.in_(company_ids)).order_by(Company.symbol.asc())
    return list(db.scalars(statement).all())
