"""Mock collector — tests/fixtures/*.csv 기반 (lru_cache 적용)."""
from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.collectors.base import BaseCollector

_FIX_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"


@lru_cache(maxsize=4)
def _read_market(market: str, dir_str: str) -> pd.DataFrame:
    f = Path(dir_str) / f"sample_prices_{market}.csv"
    df = pd.read_csv(f, parse_dates=["date"], dtype={"symbol": str})
    df["date"] = df["date"].dt.date
    return df


class MockCollector(BaseCollector):
    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self.dir = fixtures_dir or _FIX_DIR

    def _load(self, market: str) -> pd.DataFrame:
        return _read_market(market, str(self.dir))

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        market = "kr" if symbol.isdigit() and len(symbol) == 6 else "us"
        df = self._load(market)
        df = df[df["symbol"] == symbol]
        df = df[(df["date"] >= start) & (df["date"] <= end)]
        return df.set_index("date")[["open", "high", "low", "close", "volume"]]

    def fetch_realtime(self, symbol: str) -> float:
        market = "kr" if symbol.isdigit() and len(symbol) == 6 else "us"
        df = self._load(market)
        df = df[df["symbol"] == symbol]
        if df.empty:
            raise ValueError(f"Mock: 종목 {symbol!r} 데이터가 없습니다")
        return float(df.sort_values("date").iloc[-1]["close"])


def get_mock_collector() -> MockCollector:
    return MockCollector()
