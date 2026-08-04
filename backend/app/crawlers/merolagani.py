from typing import List

from app.crawlers.base import BaseNewsCrawler, CrawledArticle


class MeroLaganiCrawler(BaseNewsCrawler):
    source_name = "merolagani"

    async def fetch_latest(self) -> List[CrawledArticle]:
        return []

