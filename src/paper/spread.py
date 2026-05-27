"""호가 단위 (tick) 반올림."""
from __future__ import annotations

from decimal import Decimal

from src.config.constants import KR_TICK_TABLE, US_TICK


def round_to_kr_tick(price: Decimal) -> Decimal:
    p = price
    for upper, tick in KR_TICK_TABLE:
        if p < Decimal(upper):
            t = Decimal(tick)
            return (p / t).quantize(Decimal("1")) * t
    t = Decimal(1000)
    return (p / t).quantize(Decimal("1")) * t


def round_to_us_tick(price: Decimal) -> Decimal:
    return (price / US_TICK).quantize(Decimal("1")) * US_TICK
