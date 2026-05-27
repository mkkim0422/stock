from datetime import date

from src.utils.calendar import (
    is_kr_trading_day,
    is_us_trading_day,
    next_kr_trading_day,
)


def test_kr_holiday_new_year():
    assert not is_kr_trading_day(date(2026, 1, 1))


def test_kr_lunar_new_year_2026():
    assert not is_kr_trading_day(date(2026, 2, 16))
    assert not is_kr_trading_day(date(2026, 2, 17))


def test_kr_year_end_2025():
    assert not is_kr_trading_day(date(2025, 12, 31))


def test_us_independence_2026():
    # 2026-07-04 = 토요일 → 7/3(금) 휴장으로 조정됨
    assert not is_us_trading_day(date(2026, 7, 3))


def test_us_thanksgiving_2026():
    assert not is_us_trading_day(date(2026, 11, 26))


def test_next_kr_trading_skips_holiday():
    # 2026-01-01(목) 휴장 → 다음 거래일 1/2(금)
    n = next_kr_trading_day(date(2025, 12, 31))
    assert n == date(2026, 1, 2)
