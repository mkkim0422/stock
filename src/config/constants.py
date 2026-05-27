"""프로젝트 상수.

수치는 docs/PAPER_TRADING.md, CLAUDE.md 와 일치해야 한다.
변경 시 두 문서 모두 업데이트할 것.
"""
from __future__ import annotations

from decimal import Decimal

INITIAL_CAPITAL_KRW: Decimal = Decimal("10000000")
INITIAL_CAPITAL_USD: Decimal = Decimal("10000")

MOCK_FX_KRW_PER_USD: Decimal = Decimal("1350")
FX_FEE_RATE: Decimal = Decimal("0.001")

FEE_RATE_KR: Decimal = Decimal("0.00015")
FEE_RATE_US: Decimal = Decimal("0")

TAX_RATE_KR: Decimal = Decimal("0.0020")  # 2026-01-01 시행: KOSPI 0.05+0.15, KOSDAQ 0.20

SLIPPAGE_RATE: Decimal = Decimal("0.0007")

SIGNAL_BUY_THRESHOLD: int = 8
SIGNAL_SELL_THRESHOLD: int = -3

KR_TICK_TABLE: tuple[tuple[int, int], ...] = (
    (2_000, 1),
    (5_000, 5),
    (20_000, 10),
    (50_000, 50),
    (200_000, 100),
    (500_000, 500),
    (10**9, 1_000),
)

US_TICK: Decimal = Decimal("0.01")

BRIEFING_TIMES_KST: tuple[str, ...] = (
    "07:00",
    "09:30",
    "12:00",
    "14:30",
    "16:00",
    "18:00",
    "23:30",
)
