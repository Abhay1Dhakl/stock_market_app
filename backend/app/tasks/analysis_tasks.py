from __future__ import annotations

from celery import shared_task

from app.core.database import SessionLocal
from app.services.analysis_service import compute_analysis_snapshots


@shared_task(name="analysis.compute_company_metrics")
def compute_company_metrics() -> dict[str, object]:
    with SessionLocal() as db:
        summary = compute_analysis_snapshots(db)
        return {"status": "completed", "summary": summary}
