from typing import Iterable


def compute_vwap(prices: Iterable[float], volumes: Iterable[int]) -> float:
    weighted_total = 0.0
    volume_total = 0
    for price, volume in zip(prices, volumes):
        weighted_total += price * volume
        volume_total += volume
    if volume_total == 0:
        return 0.0
    return round(weighted_total / volume_total, 4)

