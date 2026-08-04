from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class CrawledArticle:
    title: str
    body: str
    published_at: Optional[datetime]
    source: str
    url: str


class BaseNewsCrawler(ABC):
    source_name: str = ""

    @abstractmethod
    async def fetch_latest(self) -> List[CrawledArticle]:
        """Fetch the latest articles from the target source."""

