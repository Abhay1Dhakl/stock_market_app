from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.crawlers.base import BaseNewsCrawler, CrawledArticle

KATHMANDU_TZ = ZoneInfo("Asia/Kathmandu")


class ShareSansarCrawler(BaseNewsCrawler):
    source_name = "sharesansar"
    listing_url = "https://www.sharesansar.com/news-page"

    def extract_article_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()
        article_links: list[str] = []

        for anchor in soup.select('a[href*="/newsdetail/"]'):
            href = anchor.get("href")
            if not href:
                continue

            url = self._normalize_url(self.listing_url, href)
            if "/newsdetail/" not in url or url in seen:
                continue
            if not self._looks_like_news_link(anchor, url):
                continue

            seen.add(url)
            article_links.append(url)

        return article_links

    def parse_article(self, html: str, url: str) -> Optional[CrawledArticle]:
        soup = BeautifulSoup(html, "lxml")
        title_node = soup.select_one("div.detail h1")
        body_node = soup.select_one("#newsdetail-content")
        meta_node = soup.select_one("div.detail h5")
        source_node = soup.select_one("div.detail strong")

        title = title_node.get_text(" ", strip=True) if title_node else ""
        if not title or body_node is None:
            return None

        paragraphs = [paragraph.get_text(" ", strip=True) for paragraph in body_node.select("p")]
        body = "\n\n".join(filter(None, paragraphs))
        if not body:
            body = body_node.get_text(" ", strip=True)

        excerpt = next((paragraph[:280] for paragraph in paragraphs if paragraph), body[:280])
        published_at = self._parse_published_at(meta_node.get_text(" ", strip=True) if meta_node else "")
        categories = [node.get_text(" ", strip=True) for node in soup.select("a.tags")]
        source = (source_node.get_text(" ", strip=True).lstrip("-") if source_node else "").strip() or self.source_name

        return CrawledArticle(
            title=title,
            body=body,
            published_at=published_at,
            source=source,
            url=url,
            excerpt=excerpt,
            raw_payload={"categories": categories},
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
        match = re.search(
            r"[A-Z][a-z]{2},\s+[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s+[AP]M",
            raw_text,
        )
        if match is None:
            return None

        return datetime.strptime(match.group(0), "%a, %b %d, %Y %I:%M %p").replace(tzinfo=KATHMANDU_TZ)

    def _looks_like_news_link(self, anchor, url: str) -> bool:
        if re.search(r"\d{4}-\d{2}-\d{2}$", url):
            return True

        if anchor.get("title"):
            return True

        parent_classes = " ".join(anchor.parent.get("class", [])) if anchor.parent else ""
        return "s-quote" in parent_classes
