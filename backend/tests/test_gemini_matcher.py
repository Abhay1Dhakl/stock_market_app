from app.categorization.gemini_matcher import GeminiWatchlistMatcher
from app.models import Company


def test_gemini_watchlist_matcher_maps_structured_output_to_entity_matches():
    company = Company(
        id=1,
        symbol="NABIL",
        name="Nabil Bank Limited",
        sector="Banking",
        aliases=["Nabil", "Nabil Bank"],
        description="Test company",
        is_active=True,
    )
    matcher = GeminiWatchlistMatcher([company], api_key="test-key")

    matcher._request_matches = lambda title, body: {  # type: ignore[method-assign]
        "steps": [
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            '{"matches": ['
                            '{"company_id": 1, "confidence_score": 0.91, "match_summary": "Direct mention of NABIL in the headline."},'
                            '{"company_id": 999, "confidence_score": 0.99, "match_summary": "Unknown company should be ignored."}'
                            "]} "
                        ),
                    }
                ],
            }
        ]
    }

    try:
        matches = matcher.match(
            "NABIL quarterly update",
            "NABIL announced stronger profit and deposit growth this quarter.",
        )
    finally:
        matcher.close()

    assert len(matches) == 1
    assert matches[0].company_id == 1
    assert matches[0].company_symbol == "NABIL"
    assert matches[0].confidence_score == 0.91
    assert "Direct mention" in matches[0].match_summary
