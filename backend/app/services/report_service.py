from __future__ import annotations

import csv
from io import StringIO

from sqlalchemy.orm import Session

from app.repositories.company_repository import get_latest_analysis_snapshot, list_active_companies


def build_watchlist_summary_csv(db: Session) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "symbol",
            "name",
            "sector",
            "is_active",
            "trading_date",
            "close_price",
            "vwap",
            "pressure_indicator",
            "is_volume_anomaly",
            "news_count",
            "news_sentiment_score",
            "next_day_price_change_pct",
            "next_day_volume_change_pct",
        ]
    )

    for company in list_active_companies(db):
        snapshot = get_latest_analysis_snapshot(db, company.id)
        writer.writerow(
            [
                company.symbol,
                company.name,
                company.sector,
                "true" if company.is_active else "false",
                snapshot.trading_date.isoformat() if snapshot and snapshot.trading_date else "",
                str(snapshot.close_price) if snapshot and snapshot.close_price is not None else "",
                str(snapshot.vwap) if snapshot and snapshot.vwap is not None else "",
                snapshot.pressure_indicator if snapshot and snapshot.pressure_indicator else "",
                "true" if snapshot and snapshot.is_volume_anomaly else "false",
                str(snapshot.news_count) if snapshot else "0",
                str(snapshot.news_sentiment_score) if snapshot and snapshot.news_sentiment_score is not None else "",
                str(snapshot.next_day_price_change_pct)
                if snapshot and snapshot.next_day_price_change_pct is not None
                else "",
                str(snapshot.next_day_volume_change_pct)
                if snapshot and snapshot.next_day_volume_change_pct is not None
                else "",
            ]
        )

    return output.getvalue()
