from collections import defaultdict
from typing import Dict, Iterable


def aggregate_net_positions(rows: Iterable[dict]) -> Dict[str, int]:
    positions: Dict[str, int] = defaultdict(int)
    for row in rows:
        buyer = row.get("buyer_broker")
        seller = row.get("seller_broker")
        quantity = int(row.get("quantity", 0))
        if buyer:
            positions[buyer] += quantity
        if seller:
            positions[seller] -= quantity
    return dict(positions)

