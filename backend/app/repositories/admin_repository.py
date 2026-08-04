from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.crawl_run import CrawlRun


def create_crawl_run(
    db: Session,
    *,
    run_kind: str,
    requested_sources: list[str],
    triggered_by_user_id: Optional[int],
) -> CrawlRun:
    crawl_run = CrawlRun(
        run_kind=run_kind,
        status="queued",
        requested_sources=requested_sources,
        triggered_by_user_id=triggered_by_user_id,
        run_stats={},
    )
    db.add(crawl_run)
    db.commit()
    db.refresh(crawl_run)
    return crawl_run


def get_crawl_run_by_id(db: Session, crawl_run_id: int) -> Optional[CrawlRun]:
    statement = (
        select(CrawlRun)
        .options(joinedload(CrawlRun.triggered_by))
        .where(CrawlRun.id == crawl_run_id)
    )
    return db.scalar(statement)


def list_crawl_runs(db: Session, limit: int = 20) -> list[CrawlRun]:
    statement = (
        select(CrawlRun)
        .options(joinedload(CrawlRun.triggered_by))
        .order_by(CrawlRun.created_at.desc(), CrawlRun.id.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).unique().all())
