from __future__ import annotations

from collections import Counter, defaultdict
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Company, User, UserBehaviorEvent, UserWatchlistEntry


def record_user_event(
    db: Session,
    *,
    user_id: int,
    event_type: str,
    page_path: str | None = None,
    company_id: int | None = None,
    article_id: int | None = None,
    metadata: Optional[dict[str, object]] = None,
    notes: str | None = None,
    commit: bool = True,
) -> UserBehaviorEvent:
    event = UserBehaviorEvent(
        user_id=user_id,
        company_id=company_id,
        article_id=article_id,
        event_type=event_type.strip().lower(),
        page_path=page_path.strip() if page_path else None,
        event_metadata=metadata or {},
        notes=notes.strip() if notes else None,
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    return event


def build_user_behavior_summary(db: Session, user: User) -> dict[str, object]:
    events = list(
        db.scalars(
            select(UserBehaviorEvent)
            .options(joinedload(UserBehaviorEvent.company))
            .where(UserBehaviorEvent.user_id == user.id)
            .order_by(UserBehaviorEvent.occurred_at.desc(), UserBehaviorEvent.id.desc())
            .limit(250)
        ).all()
    )
    watchlist_entries = list(
        db.scalars(
            select(UserWatchlistEntry)
            .options(joinedload(UserWatchlistEntry.company))
            .where(UserWatchlistEntry.user_id == user.id)
            .order_by(UserWatchlistEntry.created_at.asc(), UserWatchlistEntry.id.asc())
        ).all()
    )

    event_breakdown = Counter(event.event_type for event in events)
    company_counter: Counter[int] = Counter(
        event.company_id for event in events if event.company_id is not None
    )
    company_lookup = {
        entry.company.id: entry.company for entry in watchlist_entries
    }
    for company in db.scalars(select(Company).where(Company.id.in_(company_counter.keys()))).all() if company_counter else []:
        company_lookup[company.id] = company

    sector_counter: Counter[str] = Counter()
    for company_id, interactions in company_counter.items():
        company = company_lookup.get(company_id)
        if company is not None:
            sector_counter[company.sector] += interactions
    for entry in watchlist_entries:
        sector_counter[entry.company.sector] += 1

    top_companies: list[dict[str, object]] = []
    for company_id, interactions in company_counter.most_common(5):
        company = company_lookup.get(company_id)
        if company is None:
            continue
        top_companies.append(
            {
                "company_id": company.id,
                "symbol": company.symbol,
                "name": company.name,
                "interactions": interactions,
            }
        )

    recent_activity = [
        {
            "event_type": event.event_type,
            "occurred_at": event.occurred_at,
            "page_path": event.page_path,
            "company_id": event.company_id,
            "company_symbol": event.company.symbol if event.company is not None else None,
            "company_name": event.company.name if event.company is not None else None,
            "metadata": event.event_metadata,
        }
        for event in events[:8]
    ]

    return {
        "total_events": len(events),
        "watchlist_size": len(watchlist_entries),
        "companies_explored": len(company_counter),
        "favorite_sector": sector_counter.most_common(1)[0][0] if sector_counter else None,
        "last_activity_at": events[0].occurred_at if events else None,
        "event_breakdown": [
            {"event_type": event_type, "count": count}
            for event_type, count in event_breakdown.most_common()
        ],
        "top_companies": top_companies,
        "recent_activity": recent_activity,
    }


def build_admin_user_behavior_overview(db: Session, *, limit: int = 25) -> list[dict[str, object]]:
    users = list(
        db.scalars(
            select(User)
            .options(joinedload(User.role))
            .order_by(User.full_name.asc())
        ).unique().all()
    )
    events = list(
        db.scalars(
            select(UserBehaviorEvent)
            .options(joinedload(UserBehaviorEvent.company))
            .order_by(UserBehaviorEvent.occurred_at.desc(), UserBehaviorEvent.id.desc())
        ).all()
    )
    watchlist_entries = list(
        db.scalars(
            select(UserWatchlistEntry)
            .options(joinedload(UserWatchlistEntry.company))
            .order_by(UserWatchlistEntry.created_at.desc(), UserWatchlistEntry.id.desc())
        ).all()
    )

    events_by_user: dict[int, list[UserBehaviorEvent]] = defaultdict(list)
    for event in events:
        events_by_user[event.user_id].append(event)

    watchlists_by_user: dict[int, list[UserWatchlistEntry]] = defaultdict(list)
    for entry in watchlist_entries:
        watchlists_by_user[entry.user_id].append(entry)

    rows: list[dict[str, object]] = []
    for user in users:
        user_events = events_by_user.get(user.id, [])
        company_counter: Counter[int] = Counter(
            event.company_id for event in user_events if event.company_id is not None
        )
        favorite_symbol = None
        if company_counter:
            favorite_company_id = company_counter.most_common(1)[0][0]
            favorite_event = next((event for event in user_events if event.company_id == favorite_company_id and event.company is not None), None)
            if favorite_event is not None and favorite_event.company is not None:
                favorite_symbol = favorite_event.company.symbol

        rows.append(
            {
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role.name,
                "watchlist_size": len(watchlists_by_user.get(user.id, [])),
                "total_events": len(user_events),
                "companies_explored": len(company_counter),
                "last_activity_at": user_events[0].occurred_at if user_events else None,
                "favorite_symbol": favorite_symbol,
            }
        )

    rows.sort(
        key=lambda item: (
            -(item["total_events"] or 0),
            item["full_name"].lower(),
        )
    )
    return rows[:limit]
