from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Company, CompanyAnalysisSnapshot, NewsArticle, NewsCompanyTag, User, UserWatchlistEntry
from app.repositories.company_repository import get_company_by_id, get_company_by_symbol
from app.schemas.analysis import BehaviorSummaryResponse
from app.services.analysis_service import compute_analysis_snapshots
from app.services.categorization_service import categorize_news_articles
from app.services.crawl_service import refresh_companies_market_data
from app.services.user_behavior_service import record_user_event


def add_company_to_watchlist(
    db: Session,
    *,
    user: User,
    company_id: int | None = None,
    symbol: str | None = None,
    name: str | None = None,
    sector: str | None = None,
    aliases: list[str] | None = None,
    description: str | None = None,
) -> Company:
    company: Company | None = None
    if company_id is not None:
        company = get_company_by_id(db, company_id)
    elif symbol is not None:
        normalized_symbol = symbol.strip().upper()
        company = get_company_by_symbol(db, normalized_symbol)
        if company is None:
            company = Company(
                symbol=normalized_symbol,
                name=(name or normalized_symbol).strip(),
                sector=(sector or "Unclassified").strip(),
                aliases=_normalize_aliases(aliases or []),
                description=description.strip() if description else None,
                is_active=True,
                source_kind="user",
                coverage_status="pending",
                created_by_user_id=user.id,
            )
            db.add(company)
            db.commit()
            db.refresh(company)

    if company is None:
        raise ValueError("Requested company could not be resolved.")

    if not company.is_active:
        company.is_active = True

    entry = db.scalar(
        select(UserWatchlistEntry).where(
            UserWatchlistEntry.user_id == user.id,
            UserWatchlistEntry.company_id == company.id,
        )
    )
    if entry is None:
        db.add(UserWatchlistEntry(user_id=user.id, company_id=company.id, source="manual"))

    db.commit()
    db.refresh(company)

    record_user_event(
        db,
        user_id=user.id,
        event_type="watchlist_add",
        company_id=company.id,
        page_path="/dashboard",
        metadata={"symbol": company.symbol},
        commit=False,
    )

    try:
        refresh_companies_market_data(db, company_ids=[company.id])
        categorize_news_articles(db, only_missing=False)
        compute_analysis_snapshots(db, company_ids=[company.id])
        company.coverage_status = "ready" if _get_latest_snapshot(db, company.id) is not None else company.coverage_status
        company.last_refresh_error = None
        company.last_refresh_at = datetime.now(timezone.utc)
    except Exception as exc:
        company.coverage_status = "error"
        company.last_refresh_error = str(exc)
        company.last_refresh_at = datetime.now(timezone.utc)
    finally:
        db.add(company)
        db.commit()
        db.refresh(company)

    return company


def remove_company_from_watchlist(db: Session, *, user: User, company_id: int) -> None:
    entry = db.scalar(
        select(UserWatchlistEntry).where(
            UserWatchlistEntry.user_id == user.id,
            UserWatchlistEntry.company_id == company_id,
        )
    )
    if entry is None:
        return

    db.delete(entry)
    record_user_event(
        db,
        user_id=user.id,
        event_type="watchlist_remove",
        company_id=company_id,
        page_path="/dashboard",
        commit=False,
    )
    db.commit()


def build_user_watchlist_insights(db: Session, *, user: User) -> list[dict[str, object]]:
    entries = list(
        db.scalars(
            select(UserWatchlistEntry)
            .options(joinedload(UserWatchlistEntry.company))
            .where(UserWatchlistEntry.user_id == user.id)
            .order_by(UserWatchlistEntry.created_at.asc(), UserWatchlistEntry.id.asc())
        ).all()
    )
    companies = [entry.company for entry in entries]
    mention_context = _load_company_mention_context(db, [company.id for company in companies])
    return [_build_company_insight(db, company, mention_context, is_in_watchlist=True) for company in companies]


def build_discovery_feed(db: Session, *, user: User, limit: int = 8) -> list[dict[str, object]]:
    watchlist_company_ids = set(
        db.scalars(select(UserWatchlistEntry.company_id).where(UserWatchlistEntry.user_id == user.id)).all()
    )
    active_companies = list(
        db.scalars(
            select(Company)
            .where(Company.is_active.is_(True))
            .order_by(Company.updated_at.desc(), Company.symbol.asc())
        ).all()
    )
    mention_context = _load_company_mention_context(db, [company.id for company in active_companies])

    candidates = [
        _build_company_insight(db, company, mention_context, is_in_watchlist=False)
        for company in active_companies
        if company.id not in watchlist_company_ids and mention_context[company.id]["mention_count"] > 0
    ]
    candidates.sort(
        key=lambda item: (
            -(item["mention_count"] or 0),
            -(
                item["last_mentioned_at"].timestamp()
                if item["last_mentioned_at"] is not None
                else 0
            ),
            item["company"].symbol,
        ),
    )
    return candidates[:limit]


def _build_company_insight(
    db: Session,
    company: Company,
    mention_context: dict[int, dict[str, object]],
    *,
    is_in_watchlist: bool,
) -> dict[str, object]:
    snapshot = _get_latest_snapshot(db, company.id)
    summary = (
        BehaviorSummaryResponse(
            company_id=company.id,
            trading_date=snapshot.trading_date,
            close_price=snapshot.close_price,
            vwap=snapshot.vwap,
            price_change_pct=snapshot.price_change_pct,
            volume_change_pct=snapshot.volume_change_pct,
            pressure_indicator=snapshot.pressure_indicator,
            is_volume_anomaly=snapshot.is_volume_anomaly,
            anomaly_threshold=snapshot.anomaly_threshold,
            news_count=snapshot.news_count,
            news_sentiment_score=snapshot.news_sentiment_score,
            next_day_price_change_pct=snapshot.next_day_price_change_pct,
            next_day_volume_change_pct=snapshot.next_day_volume_change_pct,
            snapshot_payload=snapshot.snapshot_payload,
        )
        if snapshot is not None
        else BehaviorSummaryResponse(company_id=company.id)
    )
    context = mention_context.get(company.id, {})
    return {
        "company": company,
        "summary": summary,
        "is_in_watchlist": is_in_watchlist,
        "mention_count": int(context.get("mention_count", 0)),
        "last_mentioned_at": context.get("last_mentioned_at"),
        "recent_headline": context.get("recent_headline"),
    }


def _load_company_mention_context(db: Session, company_ids: list[int]) -> dict[int, dict[str, object]]:
    if not company_ids:
        return defaultdict(dict)

    articles = list(
        db.scalars(
            select(NewsArticle)
            .join(NewsCompanyTag, NewsCompanyTag.news_article_id == NewsArticle.id)
            .options(joinedload(NewsArticle.tags).joinedload(NewsCompanyTag.company))
            .where(NewsCompanyTag.company_id.in_(company_ids))
            .order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())
        ).unique().all()
    )
    lookback = datetime.now(timezone.utc) - timedelta(days=14)
    context: dict[int, dict[str, object]] = defaultdict(
        lambda: {"mention_count": 0, "last_mentioned_at": None, "recent_headline": None}
    )

    for article in articles:
        published_at = article.published_at
        if published_at is not None and published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        mentioned_company_ids = {tag.company_id for tag in article.tags if tag.company_id in company_ids}
        for company_id in mentioned_company_ids:
            context_item = context[company_id]
            if published_at and published_at >= lookback:
                context_item["mention_count"] += 1
            if context_item["last_mentioned_at"] is None and published_at is not None:
                context_item["last_mentioned_at"] = published_at
                context_item["recent_headline"] = article.headline

    return context


def _get_latest_snapshot(db: Session, company_id: int) -> CompanyAnalysisSnapshot | None:
    return db.scalar(
        select(CompanyAnalysisSnapshot)
        .where(CompanyAnalysisSnapshot.company_id == company_id)
        .order_by(CompanyAnalysisSnapshot.trading_date.desc())
        .limit(1)
    )


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
