from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

DEFAULT_CRAWLER_USER_AGENT = "stock-market-app-bot/0.1 (+assignment crawler)"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_CRAWL_DELAY_SECONDS = 0.5

@dataclass
class CrawledArticle:
    title: str
    body: str
    published_at: Optional[datetime]
    source: str
    url: str
    excerpt: Optional[str] = None
    raw_payload: dict[str, object] = field(default_factory=dict)


class HTTPCrawlerSupport:
    def __init__(
        self,
        *,
        client: Optional[httpx.Client] = None,
        user_agent: str = DEFAULT_CRAWLER_USER_AGENT,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        crawl_delay_seconds: float = DEFAULT_CRAWL_DELAY_SECONDS,
    ) -> None:
        self._client = client or httpx.Client(
            headers={"User-Agent": user_agent},
            follow_redirects=True,
            timeout=timeout_seconds,
        )
        self._owns_client = client is None
        self._crawl_delay_seconds = crawl_delay_seconds
        self._last_request_at = 0.0
        self._robots_cache: dict[str, RobotFileParser] = {}

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _respect_crawl_delay(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._crawl_delay_seconds:
            time.sleep(self._crawl_delay_seconds - elapsed)

    def _normalize_url(self, base_url: str, candidate: str) -> str:
        return urljoin(base_url, candidate.strip())

    def _get_robots_parser(self, target_url: str) -> RobotFileParser:
        parsed = urlparse(target_url)
        root_url = f"{parsed.scheme}://{parsed.netloc}"
        cached = self._robots_cache.get(root_url)
        if cached is not None:
            return cached

        robots_url = f"{root_url}/robots.txt"
        parser = RobotFileParser()

        try:
            response = self._client.get(robots_url)
            if response.is_success:
                parser.parse(response.text.splitlines())
        except httpx.HTTPError:
            parser.parse([])

        self._robots_cache[root_url] = parser
        return parser

    def _can_fetch(self, target_url: str) -> bool:
        parser = self._get_robots_parser(target_url)
        return parser.can_fetch(self._client.headers.get("User-Agent", "*"), target_url)

    def _request(
        self,
        method: str,
        url: str,
        *,
        data: Optional[dict[str, object]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        if not self._can_fetch(url):
            raise PermissionError(f"Crawling is disallowed by robots.txt for {url}")

        self._respect_crawl_delay()
        response = self._client.request(method, url, data=data, headers=headers)
        self._last_request_at = time.monotonic()
        response.raise_for_status()
        return response

    def _get_text(self, url: str) -> str:
        return self._request("GET", url).text

    def _get_soup(self, url: str) -> BeautifulSoup:
        return BeautifulSoup(self._get_text(url), "lxml")

    def _post_json(
        self,
        url: str,
        *,
        data: dict[str, object],
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, object]:
        response = self._request("POST", url, data=data, headers=headers)
        return response.json()


class BaseNewsCrawler(HTTPCrawlerSupport, ABC):
    source_name: str = ""

    def __del__(self) -> None:
        self.close()

    @abstractmethod
    def fetch_latest(self, limit: int = 10) -> list[CrawledArticle]:
        """Fetch the latest articles from the target source."""
