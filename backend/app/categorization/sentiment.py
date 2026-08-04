POSITIVE_WORDS = {"growth", "profit", "gain", "surge", "record", "rise"}
NEGATIVE_WORDS = {"loss", "drop", "decline", "fall", "penalty", "risk"}


def score_sentiment(text: str) -> str:
    score = sentiment_score_value(text)
    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def sentiment_score_value(text: str) -> float:
    lowered = text.lower()
    positive_hits = sum(word in lowered for word in POSITIVE_WORDS)
    negative_hits = sum(word in lowered for word in NEGATIVE_WORDS)
    total = positive_hits + negative_hits
    if total == 0:
        return 0.0
    return round((positive_hits - negative_hits) / total, 4)
