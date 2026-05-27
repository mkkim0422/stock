"""관심 종목 (워치리스트). 시그널 모니터링 대상."""
from __future__ import annotations

from src.storage import connect


def add(symbol: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)", (symbol,)
        )


def remove(symbol: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM watchlist WHERE symbol=?", (symbol,))


def list_all() -> list[str]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT symbol FROM watchlist ORDER BY added_at DESC"
        ).fetchall()
    return [r["symbol"] for r in rows]


def is_watched(symbol: str) -> bool:
    with connect() as conn:
        r = conn.execute(
            "SELECT 1 FROM watchlist WHERE symbol=?", (symbol,)
        ).fetchone()
    return r is not None
