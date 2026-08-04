from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.categorization.entity_matcher import EntityMatch
from app.models.company import Company

GEMINI_INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1/interactions"


@dataclass
class GeminiMatchCandidate:
    company_id: int
    confidence_score: float
    match_summary: str


class GeminiWatchlistMatcher:
    def __init__(
        self,
        companies: Iterable[Company],
        *,
        api_key: str,
        model: str = "gemini-2.5-flash",
        timeout_seconds: float = 20.0,
    ) -> None:
        self._api_key = api_key.strip()
        self._model = model.strip() or "gemini-2.5-flash"
        self._client = httpx.Client(timeout=timeout_seconds)
        self._companies_by_id = {company.id: company for company in companies}

    def close(self) -> None:
        self._client.close()

    def match(self, title: str, body: str) -> list[EntityMatch]:
        response_payload = self._request_matches(title, body)
        candidates = self._parse_response(response_payload)

        matches_by_company_id: dict[int, EntityMatch] = {}
        for candidate in candidates:
            company = self._companies_by_id.get(candidate.company_id)
            if company is None:
                continue

            match = EntityMatch(
                company_id=company.id,
                company_symbol=company.symbol,
                company_name=company.name,
                matched_terms=[company.symbol],
                alias_hits=0,
                symbol_hits=0,
                title_hits=0,
                confidence_score=candidate.confidence_score,
                match_summary=candidate.match_summary,
            )
            existing = matches_by_company_id.get(company.id)
            if existing is None or match.confidence_score > existing.confidence_score:
                matches_by_company_id[company.id] = match

        return sorted(matches_by_company_id.values(), key=lambda item: (-item.confidence_score, item.company_symbol))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException, httpx.TransportError)),
        reraise=True,
    )
    def _request_matches(self, title: str, body: str) -> dict[str, object]:
        response = self._client.post(
            GEMINI_INTERACTIONS_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            json={
                "model": self._model,
                "store": False,
                "system_instruction": (
                    "You classify NEPSE stock-market news against a fixed watchlist. "
                    "Return only tracked companies from the provided watchlist. "
                    "Support multi-label tagging, prefer precision over recall, and use conservative confidence scores."
                ),
                "input": self._build_prompt(title, body),
                "response_format": {
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "matches": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "company_id": {"type": "integer"},
                                        "confidence_score": {"type": "number"},
                                        "match_summary": {"type": "string"},
                                    },
                                    "required": ["company_id", "confidence_score", "match_summary"],
                                },
                            }
                        },
                        "required": ["matches"],
                    },
                },
                "generation_config": {
                    "thinking_level": "low",
                    "max_output_tokens": 512,
                    "seed": 42,
                },
            },
        )
        response.raise_for_status()
        return response.json()

    def _build_prompt(self, title: str, body: str) -> str:
        watchlist = [
            {
                "company_id": company.id,
                "symbol": company.symbol,
                "name": company.name,
                "aliases": company.aliases,
            }
            for company in self._companies_by_id.values()
        ]
        return (
            "Classify the following news article against the tracked company watchlist.\n"
            "Instructions:\n"
            "- Return zero or more companies from the watchlist.\n"
            "- Use company_id exactly as provided.\n"
            "- Do not invent companies or ids.\n"
            "- Include a short match_summary for each selected company.\n"
            "- Confidence scores must be between 0.0 and 1.0.\n"
            "- If the article is broad market commentary without a clear tracked company, return an empty matches array.\n\n"
            f"Watchlist:\n{json.dumps(watchlist, ensure_ascii=True)}\n\n"
            f"Headline:\n{title.strip()}\n\n"
            f"Body:\n{body.strip()}\n"
        )

    def _parse_response(self, response_payload: dict[str, object]) -> list[GeminiMatchCandidate]:
        output_text = self._extract_output_text(response_payload)
        parsed = json.loads(output_text)
        raw_matches = parsed.get("matches", [])
        if not isinstance(raw_matches, list):
            raise ValueError("Gemini response did not contain a valid matches array.")

        matches: list[GeminiMatchCandidate] = []
        for item in raw_matches:
            if not isinstance(item, dict):
                continue

            company_id = item.get("company_id")
            confidence_score = item.get("confidence_score")
            match_summary = item.get("match_summary")

            if not isinstance(company_id, int):
                continue
            if not isinstance(match_summary, str) or not match_summary.strip():
                continue

            matches.append(
                GeminiMatchCandidate(
                    company_id=company_id,
                    confidence_score=_clamp_confidence(confidence_score),
                    match_summary=match_summary.strip(),
                )
            )

        return matches

    @staticmethod
    def _extract_output_text(response_payload: dict[str, object]) -> str:
        steps = response_payload.get("steps")
        if not isinstance(steps, list):
            raise ValueError("Gemini response did not include interaction steps.")

        for step in reversed(steps):
            if not isinstance(step, dict) or step.get("type") != "model_output":
                continue

            content = step.get("content")
            if not isinstance(content, list):
                continue

            text_parts = [
                item["text"]
                for item in content
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str)
            ]
            if text_parts:
                return "".join(text_parts)

        raise ValueError("Gemini response did not contain model output text.")


def _clamp_confidence(value: object) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(round(numeric_value, 4), 1.0))
