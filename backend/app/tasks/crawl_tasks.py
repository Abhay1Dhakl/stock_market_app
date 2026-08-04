from __future__ import annotations

from celery import shared_task

from app.core.database import SessionLocal
from app.repositories.admin_repository import create_crawl_run
from app.services.crawl_service import execute_crawl_run

DEFAULT_CRAWL_SOURCES = ["merolagani", "sharesansar"]


@shared_task(name="crawl.run_pipeline")
def run_crawl_pipeline(crawl_run_id: int) -> dict[str, object]:
    with SessionLocal() as db:
        crawl_run = execute_crawl_run(db, crawl_run_id)
        return {
            "crawl_run_id": crawl_run.id,
            "status": crawl_run.status,
            "run_stats": crawl_run.run_stats,
        }


@shared_task(name="crawl.schedule_full")
def schedule_full_crawl() -> dict[str, object]:
    with SessionLocal() as db:
        crawl_run = create_crawl_run(
            db,
            run_kind="full",
            requested_sources=DEFAULT_CRAWL_SOURCES,
            triggered_by_user_id=None,
        )
        crawl_run = execute_crawl_run(db, crawl_run.id)
        return {
            "crawl_run_id": crawl_run.id,
            "status": crawl_run.status,
            "run_stats": crawl_run.run_stats,
        }
