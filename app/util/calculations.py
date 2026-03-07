from typing import Iterable


def calculate_order_item_total(amount: int, unit_price: float) -> float:
    return float(amount) * float(unit_price)


def calculate_order_total(item_totals: Iterable[float]) -> float:
    return float(sum(item_totals))
