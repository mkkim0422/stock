from decimal import Decimal

import pytest

from src.paper.spread import round_to_kr_tick, round_to_us_tick


@pytest.mark.parametrize(
    "price,expected",
    [
        (Decimal("1234.6"), Decimal("1235")),       # <2000 → 1원
        (Decimal("3777"), Decimal("3775")),         # 2000~5000 → 5원
        (Decimal("12_345"), Decimal("12_350")),     # 5000~20000 → 10원
        (Decimal("38_777"), Decimal("38_800")),     # 20000~50000 → 50원
        (Decimal("99_777"), Decimal("99_800")),     # 50000~200000 → 100원
        (Decimal("399_777"), Decimal("400_000")),   # 200000~500000 → 500원 (반올림 거리 동등시 짝수)
        (Decimal("777_777"), Decimal("778_000")),   # 500000+ → 1000원
    ],
)
def test_kr_tick_rounding(price, expected):
    out = round_to_kr_tick(price)
    assert out == expected


def test_us_tick_rounding():
    assert round_to_us_tick(Decimal("123.456")) == Decimal("123.46")
    assert round_to_us_tick(Decimal("199.991")) == Decimal("199.99")
    assert round_to_us_tick(Decimal("100")) == Decimal("100.00")


def test_kr_tick_zero():
    assert round_to_kr_tick(Decimal("0")) == Decimal("0")
