from decimal import Decimal

from src.paper.corporate_actions import apply_cash_dividend, apply_stock_split


def test_split_5_to_1():
    new_q, new_p = apply_stock_split(50, Decimal("100000"), 5, 1)
    assert new_q == 250
    assert new_p == Decimal("20000")


def test_split_2_to_1():
    new_q, new_p = apply_stock_split(100, Decimal("50"), 2, 1)
    assert new_q == 200
    assert new_p == Decimal("25")


def test_dividend():
    d = apply_cash_dividend(100, Decimal("500"))
    assert d == Decimal("50000")
