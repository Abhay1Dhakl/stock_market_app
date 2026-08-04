POSITIVE_WORDS = {"growth", "profit", "gain", "surge", "record", "rise"}
NEGATIVE_WORDS = {"loss", "drop", "decline", "fall", "penalty", "risk"}


def score_sentiment(text: str) -> str:
    lowered = text.lower()
    positive_hits = sum(word in lowered for word in POSITIVE_WORDS)
    negative_hits = sum(word in lowered for word in NEGATIVE_WORDS)
    if positive_hits > negative_hits:
        return "positive"
    if negative_hits > positive_hits:
        return "negative"
    return "neutral"

