"""환율 모듈 (Phase 1: mock 1,350 KRW/USD 고정)."""
from __future__ import annotations

from decimal import Decimal

from src.config.constants import FX_FEE_RATE, MOCK_FX_KRW_PER_USD


def get_fx_rate() -> Decimal:
    """Phase 1: mock 환율 고정값. Phase 2: 실시간."""
    return MOCK_FX_KRW_PER_USD


def convert_krw_to_usd(amount_krw: Decimal, fee: bool = True) -> Decimal:
    """KRW → USD. fee=True 면 환전 수수료 0.1% 차감."""
    rate = get_fx_rate()
    usd_gross = amount_krw / rate
    if fee:
        return usd_gross * (Decimal(1) - FX_FEE_RATE)
    return usd_gross


def convert_usd_to_krw(amount_usd: Decimal, fee: bool = True) -> Decimal:
    """USD → KRW. fee=True 면 환전 수수료 0.1% 차감."""
    rate = get_fx_rate()
    krw_gross = amount_usd * rate
    if fee:
        return krw_gross * (Decimal(1) - FX_FEE_RATE)
    return krw_gross
