from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from bs4 import BeautifulSoup

from app.crawlers.base import HTTPCrawlerSupport


def _to_decimal(value: object) -> Decimal:
    """Normalize crawler text or numeric input into a Decimal."""
    return Decimal(str(value).replace(",", "").strip())


def _to_int(value: object) -> int:
    """Normalize crawler text or numeric input into an integer."""
    return int(_to_decimal(value))

@dataclass
class DailyTradingBar:
    trading_date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    turnover: Decimal


@dataclass
class FloorsheetTrade:
    contract_no: str
    trading_date: date
    buyer_broker_code: str
    seller_broker_code: str
    quantity: int
    rate: Decimal
    amount: Decimal
    transaction_time: Optional[str] = None
    source_name: str = "sharesansar"


class MarketDataCrawler(HTTPCrawlerSupport):
    source_name = "sharesansar"
    company_url_template = "https://www.sharesansar.com/company/{symbol}"
    price_history_endpoint = "https://www.sharesansar.com/company-price-history"
    floorsheet_endpoint = "https://www.sharesansar.com/company-floor-sheet"

    def fetch_company_history(self, symbol: str, days: int = 30) -> list[DailyTradingBar]:
        """Fetch recent daily OHLCV history for one company symbol.

        Args:
            symbol: NEPSE symbol used to resolve the company context page.
            days: Maximum number of trading sessions to return.

        Returns:
            list[DailyTradingBar]: Chronological market-history rows.
        """
        context = self._fetch_company_context(symbol)
        payload = self._post_json(
            self.price_history_endpoint,
            data={"company": context["company_id"], "draw": 1, "start": 0, "length": max(days, 30)},
            headers=context["headers"],
        )
        return self.parse_price_history_payload(payload, days=days)

    def fetch_company_floorsheet(
        self,
        symbol: str,
        *,
        sample_days: int = 1,
        page_size: int = 200,
    ) -> list[FloorsheetTrade]:
        """Fetch sampled floorsheet trades for the most recent trading days.

        Args:
            symbol: NEPSE symbol used to resolve the company context page.
            sample_days: Number of distinct trading dates to collect.
            page_size: Page size used against the floorsheet endpoint.

        Returns:
            list[FloorsheetTrade]: Parsed floorsheet trades across the sampled
            trading dates.
        """
        context = self._fetch_company_context(symbol)
        collected: list[FloorsheetTrade] = []
        target_dates: list[date] = []
        start = 0

        while True:
            payload = self._post_json(
                self.floorsheet_endpoint,
                data={
                    "company": context["symbol"],
                    "buyer": "",
                    "seller": "",
                    "draw": 1,
                    "start": start,
                    "length": page_size,
                },
                headers=context["headers"],
            )
            page_rows = self.parse_floorsheet_payload(payload)
            if not page_rows:
                break

            for trade in page_rows:
                # Stop once we have captured the requested number of distinct trading sessions.
                if trade.trading_date not in target_dates:
                    if len(target_dates) >= sample_days:
                        return collected
                    target_dates.append(trade.trading_date)
                collected.append(trade)

            if len(page_rows) < page_size:
                break
            start += page_size

        return collected

    def parse_price_history_payload(self, payload: dict[str, object], *, days: int) -> list[DailyTradingBar]:
        """Parse the ShareSansar price-history payload into trading bars.

        Args:
            payload: Raw JSON payload returned by the history endpoint.
            days: Maximum number of recent rows to keep.

        Returns:
            list[DailyTradingBar]: Chronological trading bars ready to store.
        """
        rows = payload.get("data", [])
        if not isinstance(rows, list):
            return []

        bars = [
            DailyTradingBar(
                trading_date=date.fromisoformat(str(row["published_date"])),
                open_price=_to_decimal(row["open"]),
                high_price=_to_decimal(row["high"]),
                low_price=_to_decimal(row["low"]),
                close_price=_to_decimal(row["close"]),
                volume=_to_int(row["traded_quantity"]),
                turnover=_to_decimal(row["traded_amount"]),
            )
            for row in rows[:days]
            if isinstance(row, dict)
        ]
        bars.reverse()
        return bars

    def parse_floorsheet_payload(self, payload: dict[str, object]) -> list[FloorsheetTrade]:
        """Parse the ShareSansar floorsheet payload into trade objects.

        Args:
            payload: Raw JSON payload returned by the floorsheet endpoint.

        Returns:
            list[FloorsheetTrade]: Normalized floorsheet trades for ingestion.
        """
        rows = payload.get("data", [])
        if not isinstance(rows, list):
            return []

        trades: list[FloorsheetTrade] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            trades.append(
                FloorsheetTrade(
                    contract_no=str(row["contract_no"]),
                    trading_date=date.fromisoformat(str(row["date_"])),
                    buyer_broker_code=str(row["buyer"]),
                    seller_broker_code=str(row["seller"]),
                    quantity=_to_int(row["quantity"]),
                    rate=_to_decimal(row["rate"]),
                    amount=_to_decimal(row["amount"]),
                )
            )
        return trades

    def _fetch_company_context(self, symbol: str) -> dict[str, object]:
        """Resolve CSRF headers and company identifiers from the company page.

        Args:
            symbol: NEPSE symbol whose company page should be inspected.

        Returns:
            dict[str, object]: Request context for subsequent AJAX endpoint
            calls, including company ID, symbol, and CSRF-aware headers.
        """
        url = self.company_url_template.format(symbol=symbol.upper())
        soup = BeautifulSoup(self._get_text(url), "lxml")

        # ShareSansar embeds the AJAX identifiers and CSRF token in the company page HTML.
        token_node = soup.select_one('meta[name="_token"]')
        company_id_node = soup.select_one("#companyid")
        symbol_node = soup.select_one("#symbol")
        if token_node is None or company_id_node is None or symbol_node is None:
            raise ValueError(f"Missing market-data crawl context for {symbol}")

        return {
            "company_id": company_id_node.get_text(" ", strip=True),
            "symbol": symbol_node.get_text(" ", strip=True),
            "headers": {
                "X-CSRF-Token": token_node.get("content", ""),
                "X-Requested-With": "XMLHttpRequest",
                "Referer": url,
            },
        }
