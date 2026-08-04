def derive_pressure_indicator(price_change: float, volume_change: float) -> str:
    if price_change > 0 and volume_change > 0:
        return "strong_buy_pressure"
    if price_change > 0 and volume_change <= 0:
        return "weak_buy_pressure"
    if price_change < 0 and volume_change > 0:
        return "strong_sell_pressure"
    if price_change < 0 and volume_change <= 0:
        return "weak_sell_pressure"
    return "neutral"

