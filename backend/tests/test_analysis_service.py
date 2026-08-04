from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models import CompanyAnalysisSnapshot, FloorsheetTransaction, NewsArticle, NewsCompanyTag
from app.models.market_data import DailyPrice
from app.services.analysis_service import compute_analysis_snapshots


def test_compute_analysis_snapshots_derives_metrics_from_prices_news_and_floorsheet(
    db_session,
    seeded_company_data,
):
    company = seeded_company_data["company"]

    second_price = DailyPrice(
        company_id=company.id,
        trading_date=date(2026, 8, 4),
        open_price=Decimal("508.00"),
        high_price=Decimal("515.00"),
        low_price=Decimal("507.00"),
        close_price=Decimal("514.00"),
        volume=180000,
        turnover=Decimal("92520000.00"),
        source_name="seed",
    )
    floor_row = FloorsheetTransaction(
        company_id=company.id,
        trading_date=date(2026, 8, 4),
        transaction_time=None,
        buyer_broker_code="64",
        seller_broker_code="29",
        quantity=100,
        rate=Decimal("514.00"),
        amount=Decimal("51400.00"),
        row_hash="analysis-test-row",
        source_name="seed",
    )
    article = NewsArticle(
        source_name="sharesansar",
        source_url="https://example.com/nabil-aug-4",
        headline="Nabil profit rise continues",
        excerpt="Positive follow-up article.",
        body_text="Nabil reported another profit rise and growth in deposits.",
        sentiment_label="positive",
        published_at=None,
        raw_payload={},
    )
    db_session.add_all([second_price, floor_row, article])
    db_session.commit()
    db_session.refresh(article)

    db_session.add(
        NewsCompanyTag(
            news_article_id=article.id,
            company_id=company.id,
            confidence_score=Decimal("0.9000"),
            tag_source="system",
            match_summary="Direct symbol match",
        )
    )
    article.published_at = datetime(2026, 8, 4, 10, 0, tzinfo=timezone.utc)
    db_session.add(article)
    db_session.commit()

    summary = compute_analysis_snapshots(db_session, company_ids=[company.id])
    latest_snapshot = db_session.scalar(
        select(CompanyAnalysisSnapshot)
        .where(
            CompanyAnalysisSnapshot.company_id == company.id,
            CompanyAnalysisSnapshot.trading_date == date(2026, 8, 4),
        )
    )

    assert summary["companies_processed"] == 1
    assert summary["snapshots_written"] >= 2
    assert latest_snapshot is not None
    assert latest_snapshot.close_price == Decimal("514.00")
    assert latest_snapshot.vwap == Decimal("514.0000")
    assert latest_snapshot.pressure_indicator == "strong_buy_pressure"
    assert latest_snapshot.news_count == 1
    assert latest_snapshot.snapshot_payload["top_brokers"][0]["broker_code"] == "64"
