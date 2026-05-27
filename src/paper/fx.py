"""환율 모듈.

Phase 2:
- 기본은 실시간 환율 (exchangerate.host → 폴백 → 캐시 → mock).
- 환경변수 USE_MOCK=1 (또는 FX_FORCE_MOCK=1) 일 때 강제 mock.
"""
from __future__ import annotations

import os
from decimal import Decimal

from src.config.constants import FX_FEE_RATE, MOCK_FX_KRW_PER_USD


def _force_mock() -> bool:
    return (
        os.environ.get("USE_MOCK", "0") == "1"
        or os.environ.get("FX_FORCE_MOCK", "0") == "1"
    )


def get_fx_rate() -> Decimal:
    if _force_mock():
        return MOCK_FX_KRW_PER_USD
    try:
        from src.collectors.fx import fetch_fx_today
        return fetch_fx_today()
    except Exception:
        return MOCK_FX_KRW_PER_USD


def convert_krw_to_usd(amount_krw: Decimal, fee: bool = True) -> Decimal:
    rate = get_fx_rate()
    usd_gross = amount_krw / rate
    return usd_gross * (Decimal(1) - FX_FEE_RATE) if fee else usd_gross


def convert_usd_to_krw(amount_usd: Decimal, fee: bool = True) -> Decimal:
    rate = get_fx_rate()
    krw_gross = amount_usd * rate
    return krw_gross * (Decimal(1) - FX_FEE_RATE) if fee else krw_gross
