"""호가 단위 (tick) 반올림.

ROUND_HALF_UP 사용 — 5에서 절대값이 큰 쪽으로 반올림 (실거래 직관 부합).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from src.config.constants import KR_TICK_TABLE, US_TICK


def round_to_kr_tick(price: Decimal) -> Decimal:
    p = price
    for upper, tick in KR_TICK_TABLE:
        if p < Decimal(upper):
            t = Decimal(tick)
            return (p / t).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * t
    t = Decimal(1000)
    return (p / t).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * t


def round_to_us_tick(price: Decimal) -> Decimal:
    return (price / US_TICK).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * US_TICK
