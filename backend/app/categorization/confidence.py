def compute_confidence(
    *,
    alias_hits: int,
    symbol_hits: int,
    title_hits: int,
    distinct_terms: int,
    body_length: int,
) -> float:
    raw_score = 0.0
    raw_score += min(alias_hits, 3) * 0.14
    raw_score += min(symbol_hits, 3) * 0.2
    raw_score += min(title_hits, 2) * 0.22
    raw_score += min(distinct_terms, 4) * 0.08
    if body_length > 600:
        raw_score += 0.06
    return max(0.0, min(round(raw_score, 2), 1.0))
