"""액션 조정 (분할, 배당). Phase 1 은 분할만 작동."""
from __future__ import annotations

from decimal import Decimal


def apply_stock_split(qty: int, avg_price: Decimal, ratio_num: int, ratio_den: int) -> tuple[int, Decimal]:
    """ratio_num : ratio_den 분할 (예: 5:1 → ratio_num=5, ratio_den=1).

    qty 는 num/den 배가 되고, avg_price 는 den/num 배가 된다.
    """
    if ratio_num <= 0 or ratio_den <= 0:
        raise ValueError("ratio must be positive")
    new_qty = qty * ratio_num // ratio_den
    new_avg = avg_price * Decimal(ratio_den) / Decimal(ratio_num)
    return new_qty, new_avg


def apply_cash_dividend(qty: int, dividend_per_share: Decimal) -> Decimal:
    """현금배당 (세전). 실효세는 사용자 책임."""
    return Decimal(qty) * dividend_per_share
