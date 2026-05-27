"""수수료/거래세."""
from __future__ import annotations

from decimal import Decimal

from src.config.constants import FEE_RATE_KR, FEE_RATE_US, TAX_RATE_KR


def calc_fee(market: str, notional: Decimal) -> Decimal:
    """거래대금 기준 수수료."""
    rate = FEE_RATE_KR if market == "KR" else FEE_RATE_US
    return notional * rate


def calc_tax(market: str, side: str, notional: Decimal) -> Decimal:
    """매도 시 거래세. KR 만 부과."""
    if market != "KR" or side != "SELL":
        return Decimal(0)
    return notional * TAX_RATE_KR
