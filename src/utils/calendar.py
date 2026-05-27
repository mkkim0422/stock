"""거래 캘린더.

한국/미국 공휴일 정적 리스트 2024-2027 반영.
이후 연도는 Phase 2 에서 exchange_calendars 라이브러리 도입 검토.
"""
from __future__ import annotations

from datetime import date, timedelta

# 한국 공휴일 (KRX 휴장일). 임시휴장/대체공휴일 포함, 출처: KRX 연도별 공시.
KR_HOLIDAYS: frozenset[date] = frozenset(
    {
        # 2024
        date(2024, 1, 1), date(2024, 2, 9), date(2024, 2, 12),
        date(2024, 3, 1), date(2024, 4, 10), date(2024, 5, 1),
        date(2024, 5, 6), date(2024, 5, 15), date(2024, 6, 6),
        date(2024, 8, 15), date(2024, 9, 16), date(2024, 9, 17),
        date(2024, 9, 18), date(2024, 10, 1), date(2024, 10, 3),
        date(2024, 10, 9), date(2024, 12, 25), date(2024, 12, 31),
        # 2025
        date(2025, 1, 1), date(2025, 1, 28), date(2025, 1, 29),
        date(2025, 1, 30), date(2025, 3, 3), date(2025, 5, 1),
        date(2025, 5, 5), date(2025, 5, 6), date(2025, 6, 3),
        date(2025, 6, 6), date(2025, 8, 15), date(2025, 10, 3),
        date(2025, 10, 6), date(2025, 10, 7), date(2025, 10, 8),
        date(2025, 10, 9), date(2025, 12, 25), date(2025, 12, 31),
        # 2026
        date(2026, 1, 1), date(2026, 2, 16), date(2026, 2, 17),
        date(2026, 2, 18), date(2026, 3, 2), date(2026, 5, 1),
        date(2026, 5, 5), date(2026, 5, 25), date(2026, 6, 3),
        date(2026, 6, 6), date(2026, 8, 17), date(2026, 9, 24),
        date(2026, 9, 25), date(2026, 10, 5), date(2026, 10, 9),
        date(2026, 12, 25), date(2026, 12, 31),
        # 2027 (확정 + 추정)
        date(2027, 1, 1), date(2027, 2, 8), date(2027, 2, 9),
        date(2027, 2, 10), date(2027, 3, 1), date(2027, 5, 5),
        date(2027, 5, 13), date(2027, 6, 7), date(2027, 8, 16),
        date(2027, 9, 14), date(2027, 9, 15), date(2027, 9, 16),
        date(2027, 10, 4), date(2027, 10, 11), date(2027, 12, 31),
    }
)


# 미국 (NYSE) 공휴일 2024-2027.
US_HOLIDAYS: frozenset[date] = frozenset(
    {
        # 2024
        date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 19),
        date(2024, 3, 29), date(2024, 5, 27), date(2024, 6, 19),
        date(2024, 7, 4), date(2024, 9, 2), date(2024, 11, 28),
        date(2024, 12, 25),
        # 2025
        date(2025, 1, 1), date(2025, 1, 9), date(2025, 1, 20),
        date(2025, 2, 17), date(2025, 4, 18), date(2025, 5, 26),
        date(2025, 6, 19), date(2025, 7, 4), date(2025, 9, 1),
        date(2025, 11, 27), date(2025, 12, 25),
        # 2026
        date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16),
        date(2026, 4, 3), date(2026, 5, 25), date(2026, 6, 19),
        date(2026, 7, 3), date(2026, 9, 7), date(2026, 11, 26),
        date(2026, 12, 25),
        # 2027
        date(2027, 1, 1), date(2027, 1, 18), date(2027, 2, 15),
        date(2027, 3, 26), date(2027, 5, 31), date(2027, 6, 18),
        date(2027, 7, 5), date(2027, 9, 6), date(2027, 11, 25),
        date(2027, 12, 24),
    }
)


def is_kr_trading_day(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    return d not in KR_HOLIDAYS


def is_us_trading_day(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    return d not in US_HOLIDAYS


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


def next_us_trading_day(d: date) -> date:
    n = d + timedelta(days=1)
    while not is_us_trading_day(n):
        n += timedelta(days=1)
    return n
