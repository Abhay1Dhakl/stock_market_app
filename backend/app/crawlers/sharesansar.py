from typing import List

from app.crawlers.base import BaseNewsCrawler, CrawledArticle


class ShareSansarCrawler(BaseNewsCrawler):
    source_name = "sharesansar"

    async def fetch_latest(self) -> List[CrawledArticle]:
        return []

