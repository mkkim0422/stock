"""환율 수집기 — exchangerate.host (무키), open.er-api.com 폴백, 캐시 마지막."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.collectors.cache import cache_fx, read_cached_fx, read_latest_cached_fx
from src.utils.logger import get_logger

_log = get_logger("collectors.fx")
_TIMEOUT = 5.0


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
def _fetch_exchangerate_host() -> Decimal:
    r = httpx.get(
        "https://api.exchangerate.host/latest",
        params={"base": "USD", "symbols": "KRW"},
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    js = r.json()
    rate = js.get("rates", {}).get("KRW")
    if rate is None:
        raise RuntimeError("exchangerate.host: KRW not in response")
    return Decimal(str(rate))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
def _fetch_er_api() -> Decimal:
    r = httpx.get("https://open.er-api.com/v6/latest/USD", timeout=_TIMEOUT)
    r.raise_for_status()
    js = r.json()
    rate = js.get("rates", {}).get("KRW")
    if rate is None:
        raise RuntimeError("open.er-api.com: KRW not in response")
    return Decimal(str(rate))


def fetch_fx_today() -> Decimal:
    """오늘 환율 (캐시 → 실시간 → 폴백 → mock).

    오늘 캐시가 있으면 즉시 반환. 없으면 외부 API 시도.
    모두 실패하면 가장 최근 캐시. 그것도 없으면 mock 1350.
    """
    today = date.today()
    cached = read_cached_fx(today)
    if cached is not None:
        return cached

    for name, fn in (("exchangerate.host", _fetch_exchangerate_host),
                     ("open.er-api.com", _fetch_er_api)):
        try:
            rate = fn()
            cache_fx(today, rate)
            return rate
        except Exception as e:
            _log.warning("%s 실패: %s", name, e)

    latest = read_latest_cached_fx()
    if latest is not None:
        _log.warning("실시간 환율 실패 → 최근 캐시 사용")
        return latest

    from src.config.constants import MOCK_FX_KRW_PER_USD
    _log.warning("환율 소스 전체 실패 → mock %s", MOCK_FX_KRW_PER_USD)
    return MOCK_FX_KRW_PER_USD
