def compute_confidence(alias_hits: int, symbol_hits: int, body_length: int) -> float:
    raw_score = (alias_hits * 0.2) + (symbol_hits * 0.4)
    if body_length > 600:
        raw_score += 0.1
    return max(0.0, min(round(raw_score, 2), 1.0))

