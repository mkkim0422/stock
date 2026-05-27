"""정적 종목 마스터. Phase 2에서 동적 갱신."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

_DIR = Path(__file__).resolve().parent


@dataclass(slots=True, frozen=True)
class Symbol:
    symbol: str
    market: str
    name: str
    name_kr: str | None
    sector: str | None


def _load_csv(market: str) -> list[Symbol]:
    f = _DIR / f"{market.lower()}_symbols.csv"
    df = pd.read_csv(f, dtype={"symbol": str}).drop_duplicates(subset=["symbol"], keep="first")
    out = []
    for _, r in df.iterrows():
        out.append(
            Symbol(
                symbol=str(r["symbol"]),
                market=market,
                name=str(r["name"]),
                name_kr=str(r["name_kr"]) if pd.notna(r["name_kr"]) else None,
                sector=str(r["sector"]) if pd.notna(r["sector"]) else None,
            )
        )
    return out


def list_kr_symbols() -> list[Symbol]:
    return _load_csv("KR")


def list_us_symbols() -> list[Symbol]:
    return _load_csv("US")


def load_symbols() -> list[Symbol]:
    return list_kr_symbols() + list_us_symbols()


def search_symbols(query: str, limit: int = 20) -> list[Symbol]:
    """티커/영문명/한글명에서 부분 일치 검색."""
    q = query.strip()
    if not q:
        return []
    q_lower = q.lower()
    out = []
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
