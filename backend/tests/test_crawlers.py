from datetime import date
from decimal import Decimal

from app.crawlers.market_data import MarketDataCrawler
from app.crawlers.merolagani import MeroLaganiCrawler
from app.crawlers.sharesansar import ShareSansarCrawler


def test_sharesansar_extract_article_links_deduplicates():
    html = """
    <html>
      <body>
        <a href="/newsdetail/market-wrapup-2026-08-04">Market Wrap-up</a>
        <a href="https://www.sharesansar.com/newsdetail/market-wrapup-2026-08-04">Duplicate</a>
        <a href="/newsdetail/q4-results-2026-08-04">Quarterly Results</a>
        <a href="/newsdetail/beginners-guide-part-1">Knowledge Link</a>
      </body>
    </html>
    """

    crawler = ShareSansarCrawler()
    try:
        assert crawler.extract_article_links(html) == [
            "https://www.sharesansar.com/newsdetail/market-wrapup-2026-08-04",
            "https://www.sharesansar.com/newsdetail/q4-results-2026-08-04",
        ]
    finally:
        crawler.close()


def test_sharesansar_parse_article_extracts_body_and_timestamp():
    html = """
    <div class="detail b-shadow margin-bottom-20">
      <h1>Quarterly earnings surge</h1>
      <h5>
        Tue, Aug 4, 2026 12:07 PM on
        <a class="tags">Company Analysis</a>
      </h5>
      <strong>-ShareSansar</strong>
      <div id="newsdetail-content">
        <p>First paragraph.</p>
        <p>Second paragraph.</p>
      </div>
    </div>
    """

    crawler = ShareSansarCrawler()
    try:
        article = crawler.parse_article(html, "https://www.sharesansar.com/newsdetail/example")
    finally:
        crawler.close()

    assert article is not None
    assert article.title == "Quarterly earnings surge"
    assert article.body == "First paragraph.\n\nSecond paragraph."
    assert article.source == "ShareSansar"
    assert article.published_at is not None
    assert article.published_at.isoformat() == "2026-08-04T12:07:00+05:45"
    assert article.raw_payload["categories"] == ["Company Analysis"]


def test_merolagani_parse_article_extracts_overview_and_detail():
    html = """
    <div id="ctl00_ContentPlaceHolder1_newsTitle">Profit climbs in fiscal Q4</div>
    <div id="ctl00_ContentPlaceHolder1_newsDate">Aug 04, 2026 11:49 AM</div>
    <div id="ctl00_ContentPlaceHolder1_newsSource">MeroLagani</div>
    <div id="ctl00_ContentPlaceHolder1_newsOverview">Overview text.</div>
    <div id="ctl00_ContentPlaceHolder1_newsDetail">Detailed body text.</div>
    """

    crawler = MeroLaganiCrawler()
    try:
        article = crawler.parse_article(html, "https://merolagani.com/NewsDetail.aspx?newsID=123")
    finally:
        crawler.close()

    assert article is not None
    assert article.title == "Profit climbs in fiscal Q4"
    assert article.body == "Overview text.\n\nDetailed body text."
    assert article.source == "MeroLagani"
    assert article.published_at is not None
    assert article.published_at.isoformat() == "2026-08-04T11:49:00+05:45"
    assert article.raw_payload["news_id"] == "123"


def test_market_data_payload_parsers_convert_to_domain_objects():
    crawler = MarketDataCrawler()
    try:
        bars = crawler.parse_price_history_payload(
            {
                "data": [
                    {
                        "published_date": "2026-08-03",
                        "open": "528.20",
                        "high": "568.00",
                        "low": "528.20",
                        "close": "557.10",
                        "traded_quantity": "53226.00",
                        "traded_amount": "29781333.10",
                    },
                    {
                        "published_date": "2026-08-02",
                        "open": "520.00",
                        "high": "530.00",
                        "low": "519.00",
                        "close": "528.20",
                        "traded_quantity": "40000.00",
                        "traded_amount": "21000000.00",
                    },
                ]
            },
            days=2,
        )
        trades = crawler.parse_floorsheet_payload(
            {
                "data": [
                    {
                        "contract_no": 2026080301000001,
                        "buyer": "64",
                        "seller": "29",
                        "quantity": "10.00",
                        "rate": "528.20",
                        "amount": "5282.00",
                        "date_": "2026-08-03",
                    }
                ]
            }
        )
    finally:
        crawler.close()

    assert [bar.trading_date for bar in bars] == [date(2026, 8, 2), date(2026, 8, 3)]
    assert bars[-1].close_price == Decimal("557.10")
    assert bars[-1].volume == 53226
    assert trades[0].contract_no == "2026080301000001"
    assert trades[0].amount == Decimal("5282.00")
