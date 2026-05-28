"""포지션 사이징 — 시그널 강도에 따라 매수/매도 수량 추천.

원칙:
- 신규 매수: 가용 현금의 일정 %를 점수 강도에 따라 배분 (최대 10%).
- 보유 종목 매도: 보유 수량의 일정 %를 점수 강도에 따라 배분 (최대 100%).
- 단일 종목 위험을 제한하기 위해 1회 신규 매수 한도 10% 고정.

이 함수는 "권장값"만 반환하며 실제 주문 실행은 별개. 참고용.
"""
from __future__ import annotations

import math
from typing import TypedDict


class BuySizing(TypedDict):
    action: str            # "BUY"
    qty: int               # 추천 수량
    notional_krw: float    # 추천 매수 금액 (KRW 환산)
    pct_of_cash: float     # 가용 현금 대비 %
    rationale: str


class SellSizing(TypedDict):
    action: str            # "SELL"
    qty: int
    pct_of_holding: float  # 보유 수량 대비 %
    rationale: str


def _buy_pct_from_score(score: int) -> float:
    """점수 → 가용 현금 사용 비율(%).

    +8 ~ +9   → 4%   (매수 후보 진입 기준)
    +10 ~ +11 → 6%
    +12 ~ +13 → 8%
    +14 이상  → 10%  (강한 시그널, 단일 종목 한도)
    """
    if score >= 14:
        return 0.10
    if score >= 12:
        return 0.08
    if score >= 10:
        return 0.06
    if score >= 8:
        return 0.04
    return 0.0


def _sell_pct_from_score(score: int) -> float:
    """점수 → 보유 수량 매도 비율(%).

    -3 ~ -4  → 30%
    -5 ~ -6  → 50%
    -7 ~ -9  → 80%
    -10 이하 → 100% (전량 청산)
    """
    if score <= -10:
        return 1.00
    if score <= -7:
        return 0.80
    if score <= -5:
        return 0.50
    if score <= -3:
        return 0.30
    return 0.0


def suggest_buy(
    score: int,
    price: float,
    cash_available_krw: float,
    fx_rate_krw_per_usd: float = 1350.0,
    market: str = "KR",
) -> BuySizing | None:
    """매수 추천 사이징. 점수 +8 미만이면 None."""
    pct = _buy_pct_from_score(score)
    if pct <= 0 or cash_available_krw <= 0 or price <= 0:
        return None
    budget_krw = cash_available_krw * pct
    unit_price_krw = price if market == "KR" else price * fx_rate_krw_per_usd
    qty = int(math.floor(budget_krw / unit_price_krw))
    if qty <= 0:
        return None
    notional_krw = qty * unit_price_krw
    return {
        "action": "BUY",
        "qty": qty,
        "notional_krw": notional_krw,
        "pct_of_cash": pct * 100,
        "rationale": (
            f"점수 {score:+d} → 가용 현금의 {pct*100:.0f}% ({budget_krw:,.0f}원) 배정. "
            f"종목당 한도 10% 적용."
        ),
    }


def suggest_sell(
    score: int,
    holding_qty: int,
) -> SellSizing | None:
    """매도 추천 사이징. 점수 -3 초과이거나 보유 0이면 None."""
    pct = _sell_pct_from_score(score)
    if pct <= 0 or holding_qty <= 0:
        return None
    qty = max(1, int(math.floor(holding_qty * pct)))
    qty = min(qty, holding_qty)
    return {
        "action": "SELL",
        "qty": qty,
        "pct_of_holding": pct * 100,
        "rationale": (
            f"점수 {score:+d} → 보유 {holding_qty:,}주 중 {pct*100:.0f}% ({qty:,}주) 매도 권장."
        ),
    }
