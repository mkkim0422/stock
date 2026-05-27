"""종목 마스터 (정적 CSV + DB 동기화).

Phase 2:
- 정적 CSV 는 첫 부팅용 시드.
- DB `symbols` 테이블이 진실 소스.
- `refresh_kr_from_krx()` 로 KRX 전종목 동적 갱신.
- US 는 정적 유지 (Phase 2.5 에서 yfinance 인덱스 컴포넌트 추가 검토).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.storage import connect

_DIR = Path(__file__).resolve().parent


@dataclass(slots=True, frozen=True)
class Symbol:
    symbol: str
    market: str
    name: str
    name_kr: str | None
    sector: str | None


def _seed_from_csv() -> list[Symbol]:
    rows: list[Symbol] = []
    for market_code, fname in (("KR", "kr_symbols.csv"), ("US", "us_symbols.csv")):
        f = _DIR / fname
        df = pd.read_csv(f, dtype={"symbol": str}).drop_duplicates(
            subset=["symbol"], keep="first"
        )
        for _, r in df.iterrows():
            rows.append(
                Symbol(
                    symbol=str(r["symbol"]),
                    market=market_code,
                    name=str(r["name"]),
                    name_kr=str(r["name_kr"]) if pd.notna(r["name_kr"]) else None,
                    sector=str(r["sector"]) if pd.notna(r["sector"]) else None,
                )
            )
    return rows


def _ensure_seeded() -> None:
    """DB가 비어 있으면 CSV 시드를 INSERT."""
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM symbols").fetchone()
        if row["n"] > 0:
            return
        for s in _seed_from_csv():
            conn.execute(
                """
                INSERT OR IGNORE INTO symbols
                (symbol, market, name, name_kr, sector)
                VALUES (?, ?, ?, ?, ?)
                """,
                (s.symbol, s.market, s.name, s.name_kr, s.sector),
            )


def load_symbols() -> list[Symbol]:
    _ensure_seeded()
    with connect() as conn:
        rows = conn.execute(
            "SELECT symbol, market, name, name_kr, sector FROM symbols "
            "WHERE delisted=0 ORDER BY market, symbol"
        ).fetchall()
    return [
        Symbol(
            symbol=r["symbol"],
            market=r["market"],
            name=r["name"],
            name_kr=r["name_kr"],
            sector=r["sector"],
        )
        for r in rows
    ]


def list_kr_symbols() -> list[Symbol]:
    return [s for s in load_symbols() if s.market == "KR"]


def list_us_symbols() -> list[Symbol]:
    return [s for s in load_symbols() if s.market == "US"]


def search_symbols(query: str, limit: int = 20) -> list[Symbol]:
    q = query.strip()
    if not q:
        return []
    q_lower = q.lower()
    out: list[Symbol] = []
    for s in load_symbols():
        if (
            q_lower in s.symbol.lower()
            or q_lower in s.name.lower()
            or (s.name_kr and q in s.name_kr)
        ):
            out.append(s)
            if len(out) >= limit:
                break
    return out


def refresh_kr_from_krx() -> int:
    """KRX 전종목을 DB symbols 테이블에 upsert. 반환: 영향 행 수."""
    from src.collectors.kr import list_kr_symbols_from_krx

    rows = list_kr_symbols_from_krx("ALL")
    if not rows:
        return 0
    with connect() as conn:
        for r in rows:
            conn.execute(
                """
                INSERT INTO symbols (symbol, market, name, name_kr)
                VALUES (?, 'KR', ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    name=excluded.name,
                    name_kr=COALESCE(excluded.name_kr, symbols.name_kr),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (r["symbol"], r["name"], r["name"]),
            )
    return len(rows)
