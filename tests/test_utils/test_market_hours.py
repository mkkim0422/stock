"""시장 개장/마감 판단."""
from datetime import datetime

from src.utils.market_hours import (
    is_kr_open,
    is_us_open,
    kr_status,
    next_kr_open,
    next_us_open,
    us_status,
)
from src.utils.timezone import KST, NY


def test_kr_open_at_10am_weekday():
    dt = datetime(2026, 5, 28, 10, 0, tzinfo=KST)  # 목, 평일
    assert kr_status(dt) == "OPEN"
    assert is_kr_open(dt)


def test_kr_pre_open():
    dt = datetime(2026, 5, 28, 8, 30, tzinfo=KST)
    assert kr_status(dt) == "PRE_OPEN"


def test_kr_after_close():
    dt = datetime(2026, 5, 28, 16, 0, tzinfo=KST)
    assert kr_status(dt) == "AFTER_CLOSE"


def test_kr_weekend():
    sat = datetime(2026, 5, 30, 12, 0, tzinfo=KST)
    assert kr_status(sat) == "WEEKEND"


def test_kr_holiday_new_year():
    dt = datetime(2026, 1, 1, 10, 0, tzinfo=KST)
    assert kr_status(dt) == "HOLIDAY"


def test_us_open_at_10am_et():
    # 2026-05-28 10:00 ET = 2026-05-28 23:00 KST (DST EDT = UTC-4)
    dt = datetime(2026, 5, 28, 10, 0, tzinfo=NY)
    assert us_status(dt) == "OPEN"
    assert is_us_open(dt)


def test_us_after_close():
    dt = datetime(2026, 5, 28, 16, 30, tzinfo=NY)
    assert us_status(dt) == "AFTER_CLOSE"


def test_us_holiday_july4_observed():
    # 2026-07-04 is Saturday → observed Friday 7/3
    dt = datetime(2026, 7, 3, 10, 0, tzinfo=NY)
    assert us_status(dt) == "HOLIDAY"


def test_next_kr_open_from_afterclose():
    # 금요일 장 마감 후 → 다음 월요일 09:00
    fri_close = datetime(2026, 5, 29, 16, 0, tzinfo=KST)
    nxt = next_kr_open(fri_close)
    assert nxt.weekday() == 0  # 월
    assert nxt.hour == 9 and nxt.minute == 0


def test_next_kr_open_from_pre_open():
    # 평일 새벽 → 당일 09:00
    pre = datetime(2026, 5, 28, 6, 0, tzinfo=KST)
    nxt = next_kr_open(pre)
    assert nxt.date() == pre.date()
    assert nxt.hour == 9


def test_next_us_open_returns_kst_tz():
    dt = datetime(2026, 5, 28, 17, 0, tzinfo=NY)  # 마감 후
    nxt = next_us_open(dt)
    assert nxt.tzinfo == KST
