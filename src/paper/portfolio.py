"""포트폴리오 (현금 + 포지션). Decimal 정밀도 유지."""
from __future__ import annotations

from decimal import Decimal

from src.config.constants import INITIAL_CAPITAL_KRW, INITIAL_CAPITAL_USD
from src.storage import connect


def init_account_if_empty() -> None:
    with connect() as conn:
        row = conn.execute("SELECT id FROM account_cash WHERE id=1").fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO account_cash (id, cash_krw, cash_usd) VALUES (1, ?, ?)",
                (INITIAL_CAPITAL_KRW, INITIAL_CAPITAL_USD),
            )


def get_cash() -> tuple[Decimal, Decimal]:
    init_account_if_empty()
    with connect() as conn:
        r = conn.execute("SELECT cash_krw, cash_usd FROM account_cash WHERE id=1").fetchone()
    # DECIMAL converter 로 이미 Decimal 변환됨
    return r["cash_krw"], r["cash_usd"]


def update_cash(cash_krw: Decimal, cash_usd: Decimal) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE account_cash SET cash_krw=?, cash_usd=?, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=1",
            (cash_krw, cash_usd),
        )


def get_position(symbol: str) -> tuple[int, Decimal] | None:
    with connect() as conn:
        r = conn.execute(
            "SELECT qty, avg_price FROM positions WHERE symbol=?", (symbol,)
        ).fetchone()
    if r is None:
        return None
    return int(r["qty"]), r["avg_price"]


def list_positions() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT symbol, market, qty, avg_price FROM positions "
            "WHERE qty > 0 ORDER BY symbol"
        ).fetchall()
    out: list[dict] = []
    for r in rows:
        out.append({
            "symbol": r["symbol"],
            "market": r["market"],
            "qty": int(r["qty"]),
            "avg_price": r["avg_price"],
        })
    return out


def upsert_position(symbol: str, market: str, qty: int, avg_price: Decimal) -> None:
    with connect() as conn:
        if qty <= 0:
            conn.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
            return
        conn.execute(
            """
            INSERT INTO positions (symbol, market, qty, avg_price)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                market=excluded.market,
                qty=excluded.qty,
                avg_price=excluded.avg_price,
                updated_at=CURRENT_TIMESTAMP
            """,
            (symbol, market, qty, avg_price),
        )


def reset_portfolio() -> None:
    """테스트용. 모든 포지션/현금/거래 초기화."""
    with connect() as conn:
        conn.execute("DELETE FROM trades")
        conn.execute("DELETE FROM positions")
        conn.execute("DELETE FROM account_cash")
        conn.execute("DELETE FROM portfolio_snapshots")
    init_account_if_empty()
