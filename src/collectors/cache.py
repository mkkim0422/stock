"""SQLite prices/fx_cache 테이블을 활용한 OHLCV/환율 캐시."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd

from src.storage import connect


def cache_ohlcv(symbol: str, df: pd.DataFrame) -> int:
    """OHLCV DataFrame을 prices 테이블에 upsert.

    df 컬럼: open/high/low/close/volume. 인덱스: date.
    반환: 삽입/업데이트된 행 수.
    """
    if df.empty:
        return 0
    rows = []
    for d, r in df.iterrows():
        d_obj: date = d if isinstance(d, date) else d.date()
        rows.append(
            (
                symbol,
                d_obj.isoformat(),
                Decimal(str(r["open"])),
                Decimal(str(r["high"])),
                Decimal(str(r["low"])),
                Decimal(str(r["close"])),
                int(r["volume"]) if pd.notna(r["volume"]) else 0,
            )
        )
    with connect() as conn:
        conn.executemany(
            """
            INSERT INTO prices (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date) DO UPDATE SET
                open=excluded.open, high=excluded.high, low=excluded.low,
                close=excluded.close, volume=excluded.volume
            """,
            rows,
        )
    return len(rows)


def read_cached_ohlcv(symbol: str, start: date, end: date) -> pd.DataFrame:
    with connect() as conn:
        rows = conn.execute(
            "SELECT date, open, high, low, close, volume FROM prices "
            "WHERE symbol=? AND date BETWEEN ? AND ? ORDER BY date",
            (symbol, start.isoformat(), end.isoformat()),
        ).fetchall()
    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = pd.DataFrame([dict(r) for r in rows])
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.set_index("date")
    for c in ("open", "high", "low", "close"):
        df[c] = df[c].astype(float)
    df["volume"] = df["volume"].astype(int)
    return df


def cache_fx(d: date, krw_per_usd: Decimal) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO fx_cache (date, krw_per_usd) VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET krw_per_usd=excluded.krw_per_usd
            """,
            (d.isoformat(), krw_per_usd),
        )


def read_cached_fx(d: date) -> Decimal | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT krw_per_usd FROM fx_cache WHERE date=?", (d.isoformat(),)
        ).fetchone()
    return row["krw_per_usd"] if row else None


def read_latest_cached_fx(within_days: int = 7) -> Decimal | None:
    """가장 최근 캐시 환율 (within_days 이내)."""
    with connect() as conn:
        row = conn.execute(
            "SELECT krw_per_usd FROM fx_cache ORDER BY date DESC LIMIT 1"
        ).fetchone()
    return row["krw_per_usd"] if row else None
