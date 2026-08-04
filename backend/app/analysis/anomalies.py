from typing import List


def detect_volume_anomalies(volumes: List[int], multiplier: float = 1.8) -> List[int]:
    if not volumes:
        return []
    average_volume = sum(volumes) / len(volumes)
    return [index for index, volume in enumerate(volumes) if volume >= average_volume * multiplier]

