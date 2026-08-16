from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.crawlers.base import CrawledArticle
from app.crawlers.market_data import DailyTradingBar, FloorsheetTrade, ListedCompanyRecord, MarketDataCrawler
from app.models import Company, FloorsheetTransaction, NewsArticle
from app.models.crawl_run import CrawlRun
from app.services.crawl_service import (
    build_floorsheet_row_hash,
    ensure_seed_companies,
    refresh_companies_market_data,
    ingest_news_articles,
    insert_floorsheet_rows,
    sync_company_directory,
    upsert_daily_prices,
)


def test_ensure_seed_companies_loads_default_universe(db_session):
    created_count = ensure_seed_companies(db_session)
    companies = list(db_session.scalars(select(Company).order_by(Company.symbol.asc())).all())

    assert created_count == 6
    assert [company.symbol for company in companies] == ["CHCL", "NABIL", "NTC", "SHIVM", "SICL", "UPPER"]


def test_ingest_news_articles_deduplicates_by_source_url(db_session):
    crawl_run = CrawlRun(run_kind="news", status="queued", requested_sources=["sharesansar"], run_stats={})
    db_session.add(crawl_run)
    db_session.commit()
    db_session.refresh(crawl_run)

    articles = [
        CrawledArticle(
            title="Nabil posts stronger quarter",
            body="Quarterly body text",
            published_at=None,
            source="sharesansar",
            url="https://example.com/nabil-q4",
            excerpt="Quarterly body text",
            raw_payload={"source": "sharesansar"},
        ),
        CrawledArticle(
            title="Duplicate URL should be skipped",
            body="Duplicate body",
            published_at=None,
            source="sharesansar",
            url="https://example.com/nabil-q4",
            excerpt="Duplicate body",
            raw_payload={},
        ),
    ]

    created_count, duplicate_count = ingest_news_articles(db_session, crawl_run.id, articles)
    stored_articles = list(db_session.scalars(select(NewsArticle)).all())

    assert created_count == 1
    assert duplicate_count == 1
    assert len(stored_articles) == 1
    assert stored_articles[0].headline == "Nabil posts stronger quarter"


def test_market_data_helpers_upsert_prices_and_skip_duplicate_floorsheet_rows(db_session, seeded_company_data):
    company = seeded_company_data["company"]

    price_created, price_updated = upsert_daily_prices(
        db_session,
        company,
        [
            DailyTradingBar(
                trading_date=date(2026, 8, 3),
                open_price=Decimal("501.00"),
                high_price=Decimal("511.00"),
                low_price=Decimal("497.00"),
                close_price=Decimal("509.00"),
                volume=130000,
                turnover=Decimal("62000000.00"),
            ),
            DailyTradingBar(
                trading_date=date(2026, 8, 4),
                open_price=Decimal("509.00"),
                high_price=Decimal("512.00"),
                low_price=Decimal("505.00"),
                close_price=Decimal("510.50"),
                volume=100000,
                turnover=Decimal("51050000.00"),
            ),
        ],
    )

    trades = [
        FloorsheetTrade(
            contract_no="2026080301000001",
            trading_date=date(2026, 8, 3),
            buyer_broker_code="64",
            seller_broker_code="29",
            quantity=10,
            rate=Decimal("528.20"),
            amount=Decimal("5282.00"),
        )
    ]
    first_insert_count = insert_floorsheet_rows(db_session, company, trades)
    second_insert_count = insert_floorsheet_rows(db_session, company, trades)

    stored_floorsheet_rows = list(db_session.scalars(select(FloorsheetTransaction)).all())

    assert price_created == 1
    assert price_updated == 1
    assert first_insert_count == 1
    assert second_insert_count == 0
    assert len(stored_floorsheet_rows) == 1
    assert stored_floorsheet_rows[0].row_hash == build_floorsheet_row_hash(company.symbol, trades[0])


def test_sync_company_directory_creates_imported_companies(db_session, seeded_company_data, monkeypatch):
    monkeypatch.setattr(
        MarketDataCrawler,
        "fetch_company_directory",
        lambda self: [
            ListedCompanyRecord(symbol="HDL", name="Himalayan Distillery Limited"),
            ListedCompanyRecord(symbol="NABIL", name="Nabil Bank Limited"),
        ],
    )

    summary = sync_company_directory(db_session)
    imported_company = db_session.scalar(select(Company).where(Company.symbol == "HDL"))
    existing_company = db_session.scalar(select(Company).where(Company.symbol == "NABIL"))

    assert summary["created"] == 1
    assert summary["directory_total"] == 2
    assert imported_company is not None
    assert imported_company.is_active is False
    assert imported_company.source_kind == "directory"
    assert imported_company.sector == "Manufacturing And Processing"
    assert "Himalayan Distillery" in imported_company.aliases
    assert existing_company is not None
    assert existing_company.name == "Nabil Bank Limited"
    assert summary["deactivated"] == 0


def test_sync_company_directory_deactivates_stale_directory_companies(db_session, monkeypatch):
    stale_company = Company(
        symbol="MINFNC",
        name="Ministry Of Finance Limited",
        sector="Unclassified",
        aliases=["Ministry Of Finance"],
        description="Stale imported company",
        is_active=True,
        source_kind="directory",
    )
    db_session.add(stale_company)
    db_session.commit()

    monkeypatch.setattr(
        MarketDataCrawler,
        "fetch_company_directory",
        lambda self: [ListedCompanyRecord(symbol="HDL", name="Himalayan Distillery Limited")],
    )

    summary = sync_company_directory(db_session)
    refreshed_stale_company = db_session.scalar(select(Company).where(Company.symbol == "MINFNC"))

    assert summary["deactivated"] == 1
    assert refreshed_stale_company is not None
    assert refreshed_stale_company.is_active is False


def test_refresh_market_data_skips_directory_only_companies_on_bulk_runs(db_session, monkeypatch):
    seeded_company = Company(
        symbol="NABIL",
        name="Nabil Bank Limited",
        sector="Commercial Banks",
        aliases=["Nabil Bank"],
        description="Seed-like company",
        is_active=True,
        source_kind="seed",
    )
    directory_company = Company(
        symbol="HDL",
        name="Himalayan Distillery Limited",
        sector="Manufacturing And Processing",
        aliases=["Himalayan Distillery"],
        description="Imported directory company",
        is_active=False,
        source_kind="directory",
    )
    db_session.add_all([seeded_company, directory_company])
    db_session.commit()

    monkeypatch.setattr(MarketDataCrawler, "fetch_company_history", lambda self, symbol, days=30: [])
    monkeypatch.setattr(MarketDataCrawler, "fetch_company_floorsheet", lambda self, symbol, sample_days=1, page_size=200: [])

    summary = refresh_companies_market_data(db_session)

    assert summary["companies_total"] == 1
    assert "NABIL" in summary["companies"]
    assert "HDL" not in summary["companies"]
