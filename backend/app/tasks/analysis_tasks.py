from celery import shared_task


@shared_task(name="analysis.compute_company_metrics")
def compute_company_metrics() -> dict:
    return {"status": "queued-placeholder"}

