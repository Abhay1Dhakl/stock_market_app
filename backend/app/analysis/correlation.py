from typing import List


def align_news_to_price_window(news_counts: List[int], price_changes: List[float]) -> List[tuple]:
    paired = []
    for news_count, price_change in zip(news_counts, price_changes):
        paired.append((news_count, price_change))
    return paired

