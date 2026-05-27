from decimal import Decimal

from src.paper.fees import calc_fee, calc_tax


def test_fee_kr():
    f = calc_fee("KR", Decimal("1000000"))
    assert f == Decimal("150.00000")


def test_fee_us_zero():
    f = calc_fee("US", Decimal("1000"))
    assert f == Decimal("0")


def test_tax_kr_sell():
    t = calc_tax("KR", "SELL", Decimal("1000000"))
    assert t == Decimal("2000.0000")


def test_tax_kr_buy_zero():
    t = calc_tax("KR", "BUY", Decimal("1000000"))
    assert t == Decimal("0")


def test_tax_us_zero():
    t = calc_tax("US", "SELL", Decimal("1000"))
    assert t == Decimal("0")
