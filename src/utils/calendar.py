"""거래 캘린더 (단순화: 주말 휴장만 반영. 공휴일은 Phase 2 보강).

Phase 1 한계:
- 한국/미국 공휴일 미반영 → 거래일/영업일 정확도 한계
- Phase 2: exchange_calendars 또는 pandas_market_calendars 도입 검토
"""
from __future__ import annotations

from datetime import date, timedelta


def is_kr_trading_day(d: date) -> bool:
    return d.weekday() < 5


def is_us_trading_day(d: date) -> bool:
    return d.weekday() < 5


def next_kr_trading_day(d: date) -> date:
    n = d + timedelta(days=1)
    while not is_kr_trading_day(n):
        n += timedelta(days=1)
    return n


def previous_kr_trading_day(d: date) -> date:
    p = d - timedelta(days=1)
    while not is_kr_trading_day(p):
        p -= timedelta(days=1)
    return p
