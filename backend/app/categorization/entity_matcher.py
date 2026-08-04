from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.categorization.confidence import compute_confidence
from app.categorization.normalizer import normalize_text
from app.models.company import Company


@dataclass
class EntityMatch:
    company_id: int
    company_symbol: str
    company_name: str
    matched_terms: list[str]
    alias_hits: int
    symbol_hits: int
    title_hits: int
    confidence_score: float
    match_summary: str


class WatchlistEntityMatcher:
    def __init__(self, companies: list[Company]) -> None:
        self._companies = []
        for company in companies:
            symbol = normalize_text(company.symbol)
            aliases = [
                normalize_text(term)
                for term in build_company_terms(company.symbol, [company.name, *company.aliases])
                if normalize_text(term)
            ]
            unique_terms = list(dict.fromkeys(aliases))
            self._companies.append(
                {
                    "company_id": company.id,
                    "company_symbol": company.symbol,
                    "company_name": company.name,
                    "symbol_term": symbol,
                    "terms": unique_terms,
                }
            )

    def match(self, title: str, body: str) -> list[EntityMatch]:
        normalized_title = normalize_text(title)
        normalized_body = normalize_text(body)
        matches: list[EntityMatch] = []

        for company in self._companies:
            matched_terms: list[str] = []
            alias_hits = 0
            symbol_hits = 0
            title_hits = 0

            for term in company["terms"]:
                term_matches_title = _count_term_occurrences(normalized_title, term)
                term_matches_body = _count_term_occurrences(normalized_body, term)
                total_hits = term_matches_title + term_matches_body
                if total_hits == 0:
                    continue

                matched_terms.append(term)
                title_hits += term_matches_title
                if term == company["symbol_term"]:
                    symbol_hits += total_hits
                else:
                    alias_hits += total_hits

            if not matched_terms:
                continue

            confidence_score = compute_confidence(
                alias_hits=alias_hits,
                symbol_hits=symbol_hits,
                title_hits=title_hits,
                distinct_terms=len(matched_terms),
                body_length=len(body),
            )
            matches.append(
                EntityMatch(
                    company_id=company["company_id"],
                    company_symbol=company["company_symbol"],
                    company_name=company["company_name"],
                    matched_terms=matched_terms,
                    alias_hits=alias_hits,
                    symbol_hits=symbol_hits,
                    title_hits=title_hits,
                    confidence_score=confidence_score,
                    match_summary=(
                        f"Matched {', '.join(matched_terms[:4])}; "
                        f"title_hits={title_hits}, symbol_hits={symbol_hits}, alias_hits={alias_hits}"
                    ),
                )
            )

        matches.sort(key=lambda item: (-item.confidence_score, item.company_symbol))
        return matches


def build_company_terms(symbol: str, aliases: Iterable[str]) -> list[str]:
    return [symbol, *aliases]


def _count_term_occurrences(text: str, term: str) -> int:
    pattern = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)")
    return len(pattern.findall(text))
