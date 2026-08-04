from celery import shared_task


@shared_task(name="categorization.process_news")
def process_uncategorized_news() -> dict:
    return {"status": "queued-placeholder"}

