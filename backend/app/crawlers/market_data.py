from dataclasses import dataclass
from datetime import date
from typing import List


@dataclass
class DailyTradingBar:
    trading_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    turnover: float


class MarketDataCrawler:
    async def fetch_company_history(self, symbol: str, days: int = 30) -> List[DailyTradingBar]:
        return []

