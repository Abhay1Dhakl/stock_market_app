from __future__ import annotations

from celery import shared_task

from app.core.database import SessionLocal
from app.services.categorization_service import categorize_news_articles


@shared_task(name="categorization.process_news")
def process_uncategorized_news() -> dict[str, object]:
    with SessionLocal() as db:
        summary = categorize_news_articles(db, only_missing=False)
        return {"status": "completed", "summary": summary}
