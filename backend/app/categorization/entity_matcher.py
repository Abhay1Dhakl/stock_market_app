from dataclasses import dataclass
from typing import Iterable, List

from app.categorization.normalizer import normalize_text


@dataclass
class EntityMatch:
    company_slug: str
    matched_terms: List[str]


class WatchlistEntityMatcher:
    def __init__(self, company_terms: dict) -> None:
        self.company_terms = {
            company: [normalize_text(term) for term in terms]
            for company, terms in company_terms.items()
        }

    def match(self, text: str) -> List[EntityMatch]:
        normalized = normalize_text(text)
        matches: List[EntityMatch] = []
        for company, terms in self.company_terms.items():
            matched_terms = [term for term in terms if term in normalized]
            if matched_terms:
                matches.append(EntityMatch(company_slug=company, matched_terms=matched_terms))
        return matches


def build_company_terms(symbol: str, aliases: Iterable[str]) -> List[str]:
    return [symbol, *aliases]

