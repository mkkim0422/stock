"""성과 평가 (평가액, 일간 손익, 누적 수익률)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.collectors.mock import MockCollector
from src.config.constants import INITIAL_CAPITAL_KRW, INITIAL_CAPITAL_USD
from src.paper.fx import get_fx_rate
from src.paper.portfolio import get_cash, list_positions
from src.storage import connect


def _initial_total_krw() -> Decimal:
    return INITIAL_CAPITAL_KRW + INITIAL_CAPITAL_USD * get_fx_rate()


def evaluate(collector: MockCollector | None = None, on_date: date | None = None) -> dict:
    """현재 평가액과 손익을 계산하여 반환."""
    collector = collector or MockCollector()
    cash_krw, cash_usd = get_cash()
    fx = get_fx_rate()

    positions = list_positions()
    positions_value_krw = Decimal(0)
    rows = []
    for p in positions:
        sym = p["symbol"]
        qty = int(p["qty"])
        avg = Decimal(str(p["avg_price"]))
        market = p["market"]
        try:
            cur = Decimal(str(collector.fetch_realtime(sym)))
        except Exception:
            cur = avg  # 가격 없으면 평단 사용
        local_value = cur * Decimal(qty)
        value_krw = local_value if market == "KR" else local_value * fx
        pnl_local = (cur - avg) * Decimal(qty)
        pnl_pct = (cur / avg - Decimal(1)) * Decimal(100) if avg > 0 else Decimal(0)
        rows.append(
            {
                "symbol": sym,
                "market": market,
                "qty": qty,
                "avg_price": float(avg),
                "current_price": float(cur),
                "value_krw": float(value_krw),
                "pnl": float(pnl_local),
                "pnl_pct": float(pnl_pct),
            }
        )
        positions_value_krw += value_krw

    total_krw = cash_krw + cash_usd * fx + positions_value_krw
    init_krw = _initial_total_krw()
    cum_return_pct = (total_krw / init_krw - Decimal(1)) * Decimal(100)

    return {
        "cash_krw": float(cash_krw),
        "cash_usd": float(cash_usd),
        "fx_rate": float(fx),
        "positions": rows,
        "positions_value_krw": float(positions_value_krw),
        "total_value_krw": float(total_krw),
        "initial_value_krw": float(init_krw),
        "cum_return_pct": float(cum_return_pct),
        "as_of": (on_date or date.today()).isoformat(),
    }


def snapshot_today() -> None:
    """오늘 평가액을 portfolio_snapshots 에 저장."""
    e = evaluate()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO portfolio_snapshots
            (date, cash_krw, cash_usd, fx_rate, positions_value_krw, total_value_krw, daily_pnl_krw)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                e["as_of"],
                e["cash_krw"],
                e["cash_usd"],
                e["fx_rate"],
                e["positions_value_krw"],
                e["total_value_krw"],
                0.0,  # daily_pnl 은 별도 계산
            ),
        )
