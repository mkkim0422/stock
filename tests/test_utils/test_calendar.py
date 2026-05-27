from datetime import date

from src.utils.calendar import (
    is_kr_trading_day,
    is_us_trading_day,
    next_kr_trading_day,
    previous_kr_trading_day,
)


def test_weekend_not_trading():
    assert not is_kr_trading_day(date(2026, 5, 30))
    assert not is_kr_trading_day(date(2026, 5, 31))
    assert not is_us_trading_day(date(2026, 5, 30))


def test_weekday_trading():
    assert is_kr_trading_day(date(2026, 5, 27))


def test_next_skip_weekend():
    friday = date(2026, 5, 29)
    nxt = next_kr_trading_day(friday)
    assert nxt == date(2026, 6, 1)


def test_previous_skip_weekend():
    monday = date(2026, 6, 1)
    prev = previous_kr_trading_day(monday)
    assert prev == date(2026, 5, 29)
