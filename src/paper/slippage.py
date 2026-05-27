"""슬리피지 모델 (기본 0.07%, 대용량 추가)."""
from __future__ import annotations

from decimal import Decimal

from src.config.constants import SLIPPAGE_RATE


def apply_slippage(price: Decimal, side: str, notional_krw: Decimal | None = None) -> Decimal:
    """체결가 = 호가 ± 슬리피지. BUY 면 +, SELL 이면 -.

    notional_krw 가 1억 초과면 추가 0.03% 부과 (단순 모델).
    """
    rate = SLIPPAGE_RATE
    if notional_krw is not None and notional_krw > Decimal("100_000_000"):
        rate += Decimal("0.0003")
    if side == "BUY":
        return price * (Decimal(1) + rate)
    if side == "SELL":
        return price * (Decimal(1) - rate)
    raise ValueError(f"unknown side: {side}")
