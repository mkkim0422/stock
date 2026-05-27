"""성과 평가 (평가액, 일간 손익, 누적 수익률) — Decimal 정밀도."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.collectors import fetch_realtime
from src.collectors.base import BaseCollector
from src.config.constants import INITIAL_CAPITAL_KRW, INITIAL_CAPITAL_USD
from src.paper.fx import get_fx_rate
from src.paper.portfolio import get_cash, list_positions
from src.storage import connect


def _initial_total_krw() -> Decimal:
    return INITIAL_CAPITAL_KRW + INITIAL_CAPITAL_USD * get_fx_rate()


def evaluate(collector: BaseCollector | None = None, on_date: date | None = None) -> dict:
    """현재 평가액과 손익.

    on_date 가 주어지면 portfolio_snapshots 에서 해당 날짜 스냅샷을 우선 반환.
    스냅샷이 없으면 현 시점 평가로 계산하되 as_of 만 on_date 로 표기.
    """
    if on_date is not None:
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM portfolio_snapshots WHERE date=?",
                (on_date.isoformat(),),
            ).fetchone()
        if row is not None:
            return {
                "cash_krw": row["cash_krw"],
                "cash_usd": row["cash_usd"],
                "fx_rate": row["fx_rate"],
                "positions": [],
                "positions_value_krw": row["positions_value_krw"],
                "total_value_krw": row["total_value_krw"],
                "initial_value_krw": _initial_total_krw(),
                "cum_return_pct": (row["total_value_krw"] / _initial_total_krw() - Decimal(1))
                                  * Decimal(100),
                "as_of": on_date.isoformat(),
                "from_snapshot": True,
            }

    cash_krw, cash_usd = get_cash()
    fx = get_fx_rate()

    positions_value_krw = Decimal(0)
    rows: list[dict] = []
    for p in list_positions():
        sym = p["symbol"]
        qty = p["qty"]
        avg = p["avg_price"]
        market = p["market"]
        try:
            if collector is not None:
                cur_price = collector.fetch_realtime(sym)
            else:
                cur_price = fetch_realtime(sym)
            cur = Decimal(str(cur_price))
        except Exception:
            cur = avg
        local_value = cur * Decimal(qty)
        value_krw = local_value if market == "KR" else local_value * fx
        pnl_local = (cur - avg) * Decimal(qty)
        pnl_pct = (cur / avg - Decimal(1)) * Decimal(100) if avg > 0 else Decimal(0)
        rows.append({
            "symbol": sym,
            "market": market,
            "qty": qty,
            "avg_price": avg,
            "current_price": cur,
            "value_krw": value_krw,
            "pnl": pnl_local,
            "pnl_pct": pnl_pct,
        })
        positions_value_krw += value_krw

    total_krw = cash_krw + cash_usd * fx + positions_value_krw
    init_krw = _initial_total_krw()
    cum_return_pct = (total_krw / init_krw - Decimal(1)) * Decimal(100)

    return {
        "cash_krw": cash_krw,
        "cash_usd": cash_usd,
        "fx_rate": fx,
        "positions": rows,
        "positions_value_krw": positions_value_krw,
        "total_value_krw": total_krw,
        "initial_value_krw": init_krw,
        "cum_return_pct": cum_return_pct,
        "as_of": (on_date or date.today()).isoformat(),
        "from_snapshot": False,
    }


def _previous_total_krw(on_date: date) -> Decimal | None:
    """on_date 직전 날짜의 portfolio_snapshots.total_value_krw 반환."""
    with connect() as conn:
        row = conn.execute(
            "SELECT total_value_krw FROM portfolio_snapshots "
            "WHERE date < ? ORDER BY date DESC LIMIT 1",
            (on_date.isoformat(),),
        ).fetchone()
    return row["total_value_krw"] if row else None


def snapshot_today() -> None:
    """오늘 평가액을 portfolio_snapshots 에 저장.

    daily_pnl_krw = 오늘 total - 직전 스냅샷 total (없으면 0).
    """
    e = evaluate()
    today = date.fromisoformat(e["as_of"])
    prev = _previous_total_krw(today)
    daily_pnl = (e["total_value_krw"] - prev) if prev is not None else Decimal(0)
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO portfolio_snapshots
            (date, cash_krw, cash_usd, fx_rate, positions_value_krw,
             total_value_krw, daily_pnl_krw)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                e["as_of"],
                e["cash_krw"],
                e["cash_usd"],
                e["fx_rate"],
                e["positions_value_krw"],
                e["total_value_krw"],
                daily_pnl,
            ),
        )
