"""시장 개장/마감 시간 유틸 (KRX, NYSE).

- KRX 정규장: KST 09:00 ~ 15:30, 점심시간 없음.
- NYSE 정규장: ET 09:30 ~ 16:00 (서머타임 자동 반영, zoneinfo 사용).
- 공휴일은 src/utils/calendar.py 의 frozenset 참고.

API:
- kr_status(dt) -> "OPEN" | "PRE_OPEN" | "AFTER_CLOSE" | "HOLIDAY" | "WEEKEND"
- us_status(dt) -> 동일
- next_kr_open(dt) -> datetime (KST aware)
- next_us_open(dt) -> datetime (KST aware, 미국 정규장 시작을 KST 로 환산)
- next_market_open(market, dt) -> 위 두 함수 dispatch
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Literal

from src.utils.calendar import KR_HOLIDAYS, US_HOLIDAYS
from src.utils.timezone import KST, NY

Status = Literal["OPEN", "PRE_OPEN", "AFTER_CLOSE", "HOLIDAY", "WEEKEND"]

_KR_OPEN = time(9, 0)
_KR_CLOSE = time(15, 30)
_US_OPEN = time(9, 30)
_US_CLOSE = time(16, 0)


def _kst(dt: datetime) -> datetime:
    return dt.astimezone(KST) if dt.tzinfo else dt.replace(tzinfo=KST)


def _ny(dt: datetime) -> datetime:
    return dt.astimezone(NY) if dt.tzinfo else dt.replace(tzinfo=KST).astimezone(NY)


def kr_status(dt: datetime) -> Status:
    k = _kst(dt)
    d = k.date()
    if k.weekday() >= 5:
        return "WEEKEND"
    if d in KR_HOLIDAYS:
        return "HOLIDAY"
    t = k.time()
    if t < _KR_OPEN:
        return "PRE_OPEN"
    if t >= _KR_CLOSE:
        return "AFTER_CLOSE"
    return "OPEN"


def us_status(dt: datetime) -> Status:
    n = _ny(dt)
    d = n.date()
    if n.weekday() >= 5:
        return "WEEKEND"
    if d in US_HOLIDAYS:
        return "HOLIDAY"
    t = n.time()
    if t < _US_OPEN:
        return "PRE_OPEN"
    if t >= _US_CLOSE:
        return "AFTER_CLOSE"
    return "OPEN"


def is_kr_open(dt: datetime) -> bool:
    return kr_status(dt) == "OPEN"


def is_us_open(dt: datetime) -> bool:
    return us_status(dt) == "OPEN"


def next_kr_open(dt: datetime) -> datetime:
    """다음 정규장 시가 (KST aware). dt 가 장중이면 다음 거래일 09:00 반환."""
    k = _kst(dt)
    candidate = k.replace(hour=9, minute=0, second=0, microsecond=0)
    if candidate <= k:
        candidate = candidate + timedelta(days=1)
    while candidate.weekday() >= 5 or candidate.date() in KR_HOLIDAYS:
        candidate = candidate + timedelta(days=1)
    return candidate


def next_us_open(dt: datetime) -> datetime:
    """다음 NYSE 정규장 시가를 KST aware 로 반환."""
    n = _ny(dt)
    candidate = n.replace(hour=9, minute=30, second=0, microsecond=0)
    if candidate <= n:
        candidate = candidate + timedelta(days=1)
        candidate = candidate.replace(hour=9, minute=30)
    while candidate.weekday() >= 5 or candidate.date() in US_HOLIDAYS:
        candidate = candidate + timedelta(days=1)
        candidate = candidate.replace(hour=9, minute=30)
    return candidate.astimezone(KST)


def next_market_open(market: str, dt: datetime) -> datetime:
    return next_kr_open(dt) if market == "KR" else next_us_open(dt)


def market_status(market: str, dt: datetime) -> Status:
    return kr_status(dt) if market == "KR" else us_status(dt)


_STATUS_LABEL_KR: dict[Status, str] = {
    "OPEN": "🟢 장중",
    "PRE_OPEN": "🟡 개장 전",
    "AFTER_CLOSE": "🔴 장 마감",
    "HOLIDAY": "🔴 휴장 (공휴일)",
    "WEEKEND": "🔴 휴장 (주말)",
}


def status_label(status: Status) -> str:
    return _STATUS_LABEL_KR[status]
