"""액션 조정 (분할, 배당) + trader 통합 헬퍼."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.paper.portfolio import get_cash, get_position, update_cash, upsert_position
from src.storage import connect


def apply_stock_split(
    qty: int, avg_price: Decimal, ratio_num: int, ratio_den: int
) -> tuple[int, Decimal]:
    """ratio_num : ratio_den 분할 (예: 5:1 → ratio_num=5, ratio_den=1)."""
    if ratio_num <= 0 or ratio_den <= 0:
        raise ValueError("ratio must be positive")
    new_qty = qty * ratio_num // ratio_den
    new_avg = avg_price * Decimal(ratio_den) / Decimal(ratio_num)
    return new_qty, new_avg


def apply_cash_dividend(qty: int, dividend_per_share: Decimal) -> Decimal:
    """현금배당 (세전)."""
    return Decimal(qty) * dividend_per_share


def apply_split_to_portfolio(
    symbol: str, ratio_num: int, ratio_den: int, ex_date: date | None = None
) -> tuple[int, Decimal] | None:
    """현재 보유 포지션에 분할 적용 + DB 기록.

    반환: (new_qty, new_avg) 또는 None (포지션 없음).
    """
    pos = get_position(symbol)
    if pos is None:
        return None
    qty, avg = pos
    new_qty, new_avg = apply_stock_split(qty, avg, ratio_num, ratio_den)
    market = "KR" if symbol.isdigit() and len(symbol) == 6 else "US"
    upsert_position(symbol, market, new_qty, new_avg)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO corporate_actions
            (symbol, ex_date, kind, ratio_num, ratio_den, applied_at)
            VALUES (?, ?, 'SPLIT', ?, ?, CURRENT_TIMESTAMP)
            """,
            (symbol, (ex_date or date.today()).isoformat(), ratio_num, ratio_den),
        )
    return new_qty, new_avg


def apply_dividend_to_portfolio(
    symbol: str, dividend_per_share: Decimal, ex_date: date | None = None
) -> Decimal:
    """현재 보유 수량에 현금배당 적용 + 현금 잔고 증가 + DB 기록.

    반환: 배당 총액 (KRW or USD, 시장 통화 기준).
    """
    pos = get_position(symbol)
    if pos is None:
        return Decimal(0)
    qty, _ = pos
    market = "KR" if symbol.isdigit() and len(symbol) == 6 else "US"
    total = apply_cash_dividend(qty, dividend_per_share)

    cash_krw, cash_usd = get_cash()
    if market == "KR":
        cash_krw += total
    else:
        cash_usd += total
    update_cash(cash_krw, cash_usd)

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO corporate_actions
            (symbol, ex_date, kind, dividend, applied_at)
            VALUES (?, ?, 'DIVIDEND', ?, CURRENT_TIMESTAMP)
            """,
            (symbol, (ex_date or date.today()).isoformat(), dividend_per_share),
        )
    return total
