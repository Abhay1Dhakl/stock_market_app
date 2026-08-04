from celery import shared_task


@shared_task(name="crawl.fetch_news")
def fetch_news_for_watchlist() -> dict:
    return {"status": "queued-placeholder"}

