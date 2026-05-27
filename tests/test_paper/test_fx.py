from decimal import Decimal

import pytest

from src.paper.fx import convert_krw_to_usd, convert_usd_to_krw, get_fx_rate


def test_rate_is_mock():
    assert get_fx_rate() == Decimal("1350")


def test_krw_to_usd_with_fee():
    usd = convert_krw_to_usd(Decimal("1_350_000"))
    assert usd == pytest.approx(Decimal("999"), rel=Decimal("0.0001"))


def test_usd_to_krw_with_fee():
    krw = convert_usd_to_krw(Decimal("1000"))
    assert krw == pytest.approx(Decimal("1348650"), rel=Decimal("0.0001"))


def test_no_fee_roundtrip():
    krw = convert_usd_to_krw(Decimal("100"), fee=False)
    back = convert_krw_to_usd(krw, fee=False)
    assert back == Decimal("100")
