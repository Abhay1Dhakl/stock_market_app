from __future__ import annotations

from datetime import datetime
from typing import Optional
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.crawlers.base import BaseNewsCrawler, CrawledArticle

KATHMANDU_TZ = ZoneInfo("Asia/Kathmandu")


class MeroLaganiCrawler(BaseNewsCrawler):
    source_name = "merolagani"
    listing_url = "https://merolagani.com/NewsList.aspx"

    def extract_article_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()
        article_links: list[str] = []

        for anchor in soup.select('a[href*="NewsDetail.aspx?newsID="]'):
            href = anchor.get("href")
            if not href:
                continue

            url = self._normalize_url(self.listing_url, href)
            if "NewsDetail.aspx?newsID=" not in url or url in seen:
                continue

            seen.add(url)
            article_links.append(url)

        return article_links

    def parse_article(self, html: str, url: str) -> Optional[CrawledArticle]:
        soup = BeautifulSoup(html, "lxml")
        title_node = soup.select_one("#ctl00_ContentPlaceHolder1_newsTitle")
        overview_node = soup.select_one("#ctl00_ContentPlaceHolder1_newsOverview")
        detail_node = soup.select_one("#ctl00_ContentPlaceHolder1_newsDetail")
        if title_node is None or detail_node is None:
            return None

        overview = overview_node.get_text(" ", strip=True) if overview_node else ""
        detail_text = detail_node.get_text("\n", strip=True)
        body_parts = [part for part in [overview, detail_text] if part]
        body = "\n\n".join(body_parts)
        excerpt = overview[:280] if overview else detail_text[:280]

        source_node = soup.select_one("#ctl00_ContentPlaceHolder1_newsSource")
        news_id = parse_qs(urlparse(url).query).get("newsID", [None])[0]

        return CrawledArticle(
            title=title_node.get_text(" ", strip=True),
            body=body,
            published_at=self._parse_published_at(
                soup.select_one("#ctl00_ContentPlaceHolder1_newsDate").get_text(" ", strip=True)
                if soup.select_one("#ctl00_ContentPlaceHolder1_newsDate") is not None
                else ""
            ),
            source=source_node.get_text(" ", strip=True) if source_node else self.source_name,
            url=url,
            excerpt=excerpt,
            raw_payload={"news_id": news_id},
        )

    def fetch_latest(self, limit: int = 10) -> list[CrawledArticle]:
        articles: list[CrawledArticle] = []
        listing_html = self._get_text(self.listing_url)

        for article_url in self.extract_article_links(listing_html)[:limit]:
            article = self.parse_article(self._get_text(article_url), article_url)
            if article is not None:
                articles.append(article)

        return articles

    def _parse_published_at(self, raw_text: str) -> Optional[datetime]:
        if not raw_text:
            return None
        return datetime.strptime(raw_text, "%b %d, %Y %I:%M %p").replace(tzinfo=KATHMANDU_TZ)
