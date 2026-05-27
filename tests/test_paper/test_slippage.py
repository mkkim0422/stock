from decimal import Decimal

import pytest

from src.paper.slippage import apply_slippage


def test_buy_higher():
    p = apply_slippage(Decimal("100"), "BUY")
    assert p == Decimal("100") * Decimal("1.0007")


def test_sell_lower():
    p = apply_slippage(Decimal("100"), "SELL")
    assert p == Decimal("100") * Decimal("0.9993")


def test_large_buy_extra():
    p = apply_slippage(Decimal("100"), "BUY", notional_krw=Decimal("200_000_000"))
    assert p == Decimal("100") * Decimal("1.0010")


def test_unknown_side():
    with pytest.raises(ValueError):
        apply_slippage(Decimal("100"), "HOLD")
