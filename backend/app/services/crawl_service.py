from __future__ import annotations

import json
import logging
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crawlers.base import CrawledArticle
from app.crawlers.market_data import DailyTradingBar, FloorsheetTrade, MarketDataCrawler
from app.crawlers.merolagani import MeroLaganiCrawler
from app.crawlers.sharesansar import ShareSansarCrawler
from app.models import Company, CrawlRun, DailyPrice, FloorsheetTransaction, NewsArticle
from app.repositories.company_repository import list_active_companies

logger = logging.getLogger(__name__)

KATHMANDU_TZ = ZoneInfo("Asia/Kathmandu")
SEED_COMPANY_FILE = Path(__file__).resolve().parents[3] / "data" / "seed" / "companies.json"
NEWS_LIMIT_PER_SOURCE = 10
MARKET_HISTORY_DAYS = 30
FLOORSHEET_SAMPLE_DAYS = 2

NEWS_CRAWLER_REGISTRY = {
    "merolagani": MeroLaganiCrawler,
    "sharesansar": ShareSansarCrawler,
}


def execute_crawl_run(db: Session, crawl_run_id: int) -> CrawlRun:
    crawl_run = db.get(CrawlRun, crawl_run_id)
    if crawl_run is None:
        raise ValueError(f"Crawl run {crawl_run_id} does not exist.")

    crawl_run.status = "running"
    crawl_run.started_at = datetime.now(tz=KATHMANDU_TZ)
    crawl_run.finished_at = None
    crawl_run.error_message = None
    db.commit()

    stats: dict[str, object] = {}

    try:
        if crawl_run.run_kind in {"news", "full"}:
            stats["news"] = crawl_news_sources(db, crawl_run)

        if crawl_run.run_kind in {"market_data", "full"}:
            stats["market_data"] = crawl_market_dataset(db, crawl_run)

        crawl_run = db.get(CrawlRun, crawl_run_id)
        if crawl_run is None:
            raise ValueError(f"Crawl run {crawl_run_id} disappeared during execution.")

        crawl_run.status = "succeeded"
        crawl_run.finished_at = datetime.now(tz=KATHMANDU_TZ)
        crawl_run.run_stats = stats
        db.commit()
        db.refresh(crawl_run)
        return crawl_run
    except Exception as exc:
        logger.exception("Crawl run %s failed", crawl_run_id)
        db.rollback()

        failed_run = db.get(CrawlRun, crawl_run_id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.finished_at = datetime.now(tz=KATHMANDU_TZ)
            failed_run.error_message = str(exc)
            failed_run.run_stats = stats
            db.commit()

        raise


def crawl_news_sources(db: Session, crawl_run: CrawlRun) -> dict[str, object]:
    requested_sources = [source.strip().lower() for source in crawl_run.requested_sources if source.strip()]
    sources = [source for source in requested_sources if source in NEWS_CRAWLER_REGISTRY] or sorted(NEWS_CRAWLER_REGISTRY)

    summary: dict[str, object] = {
        "sources_requested": sources,
        "fetched": 0,
        "created": 0,
        "duplicates": 0,
        "sources": {},
    }

    for source_name in sources:
        crawler = NEWS_CRAWLER_REGISTRY[source_name]()
        try:
            articles = crawler.fetch_latest(limit=NEWS_LIMIT_PER_SOURCE)
            created_count, duplicate_count = ingest_news_articles(db, crawl_run.id, articles)
            summary["fetched"] += len(articles)
            summary["created"] += created_count
            summary["duplicates"] += duplicate_count
            summary["sources"][source_name] = {
                "status": "succeeded",
                "fetched": len(articles),
                "created": created_count,
                "duplicates": duplicate_count,
            }
        except Exception as exc:
            logger.warning("News crawl failed for source %s: %s", source_name, exc)
            summary["sources"][source_name] = {"status": "failed", "error": str(exc)}
        finally:
            crawler.close()

    return summary


def crawl_market_dataset(db: Session, crawl_run: CrawlRun) -> dict[str, object]:
    requested_sources = [source.strip().lower() for source in crawl_run.requested_sources if source.strip()]
    if requested_sources and "sharesansar" not in requested_sources:
        return {
            "status": "skipped",
            "reason": "Market data is currently sourced from ShareSansar only.",
        }

    seeded_companies = ensure_seed_companies(db)
    companies = list_active_companies(db)
    crawler = MarketDataCrawler()

    summary: dict[str, object] = {
        "status": "succeeded",
        "seeded_companies": seeded_companies,
        "companies_total": len(companies),
        "price_rows_created": 0,
        "price_rows_updated": 0,
        "floorsheet_rows_created": 0,
        "companies": {},
    }

    try:
        for company in companies:
            try:
                bars = crawler.fetch_company_history(company.symbol, days=MARKET_HISTORY_DAYS)
                price_created, price_updated = upsert_daily_prices(db, company, bars)
                floorsheet_rows = crawler.fetch_company_floorsheet(
                    company.symbol,
                    sample_days=FLOORSHEET_SAMPLE_DAYS,
                )
                floorsheet_created = insert_floorsheet_rows(db, company, floorsheet_rows)

                summary["price_rows_created"] += price_created
                summary["price_rows_updated"] += price_updated
                summary["floorsheet_rows_created"] += floorsheet_created
                summary["companies"][company.symbol] = {
                    "status": "succeeded",
                    "prices_fetched": len(bars),
                    "prices_created": price_created,
                    "prices_updated": price_updated,
                    "floorsheet_rows_fetched": len(floorsheet_rows),
                    "floorsheet_rows_created": floorsheet_created,
                }
            except Exception as exc:
                logger.warning("Market-data crawl failed for %s: %s", company.symbol, exc)
                summary["companies"][company.symbol] = {"status": "failed", "error": str(exc)}
    finally:
        crawler.close()

    return summary


def ensure_seed_companies(db: Session) -> int:
    if not SEED_COMPANY_FILE.exists():
        return 0

    company_payload = json.loads(SEED_COMPANY_FILE.read_text(encoding="utf-8"))
    existing_symbols = set(db.scalars(select(Company.symbol)).all())
    created_count = 0

    for item in company_payload:
        symbol = str(item["symbol"]).upper()
        if symbol in existing_symbols:
            continue

        db.add(
            Company(
                symbol=symbol,
                name=str(item["name"]),
                sector=str(item["sector"]),
                aliases=list(item.get("aliases", [])),
                description=item.get("description"),
                is_active=bool(item.get("is_active", True)),
            )
        )
        existing_symbols.add(symbol)
        created_count += 1

    if created_count:
        db.commit()

    return created_count


def ingest_news_articles(db: Session, crawl_run_id: int, articles: list[CrawledArticle]) -> tuple[int, int]:
    article_urls = [article.url for article in articles]
    existing_urls = set()
    if article_urls:
        existing_urls = set(
            db.scalars(select(NewsArticle.source_url).where(NewsArticle.source_url.in_(article_urls))).all()
        )

    created_count = 0
    duplicate_count = 0

    for article in articles:
        if article.url in existing_urls:
            duplicate_count += 1
            continue

        db.add(
            NewsArticle(
                source_name=article.source.strip().lower(),
                source_url=article.url,
                headline=article.title,
                excerpt=article.excerpt,
                body_text=article.body,
                published_at=article.published_at,
                raw_payload=article.raw_payload,
                crawl_run_id=crawl_run_id,
            )
        )
        existing_urls.add(article.url)
        created_count += 1

    if created_count:
        db.commit()

    return created_count, duplicate_count


def upsert_daily_prices(db: Session, company: Company, bars: list[DailyTradingBar]) -> tuple[int, int]:
    if not bars:
        return 0, 0

    trading_dates = [bar.trading_date for bar in bars]
    existing_rows = {
        row.trading_date: row
        for row in db.scalars(
            select(DailyPrice).where(
                DailyPrice.company_id == company.id,
                DailyPrice.trading_date.in_(trading_dates),
            )
        ).all()
    }

    created_count = 0
    updated_count = 0

    for bar in bars:
        row = existing_rows.get(bar.trading_date)
        if row is None:
            db.add(
                DailyPrice(
                    company_id=company.id,
                    trading_date=bar.trading_date,
                    open_price=bar.open_price,
                    high_price=bar.high_price,
                    low_price=bar.low_price,
                    close_price=bar.close_price,
                    volume=bar.volume,
                    turnover=bar.turnover,
                    source_name="sharesansar",
                )
            )
            created_count += 1
            continue

        row.open_price = bar.open_price
        row.high_price = bar.high_price
        row.low_price = bar.low_price
        row.close_price = bar.close_price
        row.volume = bar.volume
        row.turnover = bar.turnover
        row.source_name = "sharesansar"
        updated_count += 1

    if created_count or updated_count:
        db.commit()

    return created_count, updated_count


def insert_floorsheet_rows(db: Session, company: Company, trades: list[FloorsheetTrade]) -> int:
    if not trades:
        return 0

    row_hashes = [build_floorsheet_row_hash(company.symbol, trade) for trade in trades]
    existing_hashes = set(
        db.scalars(select(FloorsheetTransaction.row_hash).where(FloorsheetTransaction.row_hash.in_(row_hashes))).all()
    )

    created_count = 0

    for trade, row_hash in zip(trades, row_hashes):
        if row_hash in existing_hashes:
            continue

        db.add(
            FloorsheetTransaction(
                company_id=company.id,
                trading_date=trade.trading_date,
                transaction_time=None,
                buyer_broker_code=trade.buyer_broker_code,
                seller_broker_code=trade.seller_broker_code,
                quantity=trade.quantity,
                rate=trade.rate,
                amount=trade.amount,
                row_hash=row_hash,
                source_name=trade.source_name,
            )
        )
        existing_hashes.add(row_hash)
        created_count += 1

    if created_count:
        db.commit()

    return created_count


def build_floorsheet_row_hash(symbol: str, trade: FloorsheetTrade) -> str:
    digest_source = "|".join(
        [
            symbol.upper(),
            trade.contract_no,
            trade.trading_date.isoformat(),
            trade.buyer_broker_code,
            trade.seller_broker_code,
            str(trade.quantity),
            str(trade.rate),
            str(trade.amount),
        ]
    )
    return sha256(digest_source.encode("utf-8")).hexdigest()
