from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.broker_analysis import aggregate_net_positions
from app.analysis.pressure import derive_pressure_indicator
from app.analysis.price_metrics import compute_vwap
from app.categorization.sentiment import sentiment_score_value
from app.models import Company, CompanyAnalysisSnapshot, DailyPrice, FloorsheetTransaction, NewsArticle, NewsCompanyTag

ANOMALY_MULTIPLIER = Decimal("1.8")


def compute_analysis_snapshots(db: Session, *, company_ids: list[int] | None = None) -> dict[str, int]:
    company_statement = select(Company).where(Company.is_active.is_(True)).order_by(Company.symbol.asc())
    if company_ids:
        company_statement = company_statement.where(Company.id.in_(company_ids))
    companies = list(db.scalars(company_statement).all())

    snapshots_written = 0
    companies_processed = 0

    for company in companies:
        price_rows = list(
            db.scalars(
                select(DailyPrice)
                .where(DailyPrice.company_id == company.id)
                .order_by(DailyPrice.trading_date.asc())
            ).all()
        )
        if not price_rows:
            continue

        floorsheet_rows = list(
            db.scalars(
                select(FloorsheetTransaction)
                .where(FloorsheetTransaction.company_id == company.id)
                .order_by(FloorsheetTransaction.trading_date.asc(), FloorsheetTransaction.id.asc())
            ).all()
        )
        article_rows = list(
            db.scalars(
                select(NewsArticle)
                .join(NewsCompanyTag, NewsCompanyTag.news_article_id == NewsArticle.id)
                .where(NewsCompanyTag.company_id == company.id)
                .order_by(NewsArticle.published_at.asc(), NewsArticle.id.asc())
            )
            .unique()
            .all()
        )

        floorsheet_by_date = defaultdict(list)
        for row in floorsheet_rows:
            floorsheet_by_date[row.trading_date].append(row)

        news_by_date = defaultdict(list)
        for article in article_rows:
            if article.published_at is not None:
                news_by_date[article.published_at.date()].append(article)

        existing_snapshots = {
            row.trading_date: row
            for row in db.scalars(
                select(CompanyAnalysisSnapshot).where(CompanyAnalysisSnapshot.company_id == company.id)
            ).all()
        }

        closing_prices = [float(row.close_price) for row in price_rows]
        volumes = [row.volume for row in price_rows]
        anomaly_thresholds = _build_anomaly_thresholds(volumes)

        for index, row in enumerate(price_rows):
            previous_row = price_rows[index - 1] if index > 0 else None
            next_row = price_rows[index + 1] if index + 1 < len(price_rows) else None

            price_change_pct = _pct_change(row.close_price, previous_row.close_price if previous_row else None)
            volume_change_pct = _pct_change(Decimal(row.volume), Decimal(previous_row.volume) if previous_row else None)
            threshold = anomaly_thresholds[index]
            is_anomaly = Decimal(row.volume) >= threshold if threshold > 0 else False

            daily_floorsheet = floorsheet_by_date.get(row.trading_date, [])
            vwap = _compute_snapshot_vwap(row, daily_floorsheet)
            broker_positions = aggregate_net_positions(
                [
                    {
                        "buyer_broker": trade.buyer_broker_code,
                        "seller_broker": trade.seller_broker_code,
                        "quantity": trade.quantity,
                    }
                    for trade in daily_floorsheet
                ]
            )
            top_brokers = [
                {"broker_code": broker_code, "net_quantity": quantity}
                for broker_code, quantity in sorted(
                    broker_positions.items(),
                    key=lambda item: (-item[1], item[0]),
                )[:5]
            ]

            related_articles = news_by_date.get(row.trading_date, [])
            sentiment_values = [
                sentiment_score_value(f"{article.headline}\n{article.body_text}")
                for article in related_articles
            ]
            avg_sentiment = (
                _decimalize(sum(sentiment_values) / len(sentiment_values), places="0.0001")
                if sentiment_values
                else None
            )

            snapshot = existing_snapshots.get(row.trading_date)
            if snapshot is None:
                snapshot = CompanyAnalysisSnapshot(company_id=company.id, trading_date=row.trading_date)
                db.add(snapshot)
                existing_snapshots[row.trading_date] = snapshot

            snapshot.close_price = row.close_price
            snapshot.vwap = vwap
            snapshot.price_change_pct = price_change_pct
            snapshot.volume_change_pct = volume_change_pct
            snapshot.pressure_indicator = derive_pressure_indicator(
                float(price_change_pct or 0),
                float(volume_change_pct or 0),
            )
            snapshot.is_volume_anomaly = is_anomaly
            snapshot.anomaly_threshold = threshold
            snapshot.news_count = len(related_articles)
            snapshot.news_sentiment_score = avg_sentiment
            snapshot.next_day_price_change_pct = (
                _pct_change(next_row.close_price, row.close_price) if next_row is not None else None
            )
            snapshot.next_day_volume_change_pct = (
                _pct_change(Decimal(next_row.volume), Decimal(row.volume)) if next_row is not None else None
            )
            snapshot.snapshot_payload = {
                "top_brokers": top_brokers,
                "news_headlines": [article.headline for article in related_articles[:5]],
                "window_close_prices": closing_prices[max(0, index - 4) : index + 1],
                "window_volumes": volumes[max(0, index - 4) : index + 1],
                "floorsheet_trade_count": len(daily_floorsheet),
            }
            snapshots_written += 1

        companies_processed += 1

    if snapshots_written:
        db.commit()

    return {
        "companies_processed": companies_processed,
        "snapshots_written": snapshots_written,
    }


def _pct_change(current: Decimal, previous: Decimal | None) -> Decimal | None:
    if previous in (None, Decimal("0")):
        return None
    value = ((current - previous) / previous) * Decimal("100")
    return _decimalize(value, places="0.0001")


def _compute_snapshot_vwap(price_row: DailyPrice, floorsheet_rows: list[FloorsheetTransaction]) -> Decimal:
    if floorsheet_rows:
        prices = [float(row.rate) for row in floorsheet_rows]
        volumes = [row.quantity for row in floorsheet_rows]
        return _decimalize(Decimal(str(compute_vwap(prices, volumes))), places="0.0001")
    return _decimalize(price_row.close_price, places="0.0001")


def _build_anomaly_thresholds(volumes: list[int]) -> list[Decimal]:
    thresholds: list[Decimal] = []
    running_total = Decimal("0")
    for index, volume in enumerate(volumes, start=1):
        running_total += Decimal(volume)
        average = running_total / Decimal(index)
        thresholds.append(_decimalize(average * ANOMALY_MULTIPLIER, places="0.01"))
    return thresholds


def _decimalize(value: Decimal | float, *, places: str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP)
