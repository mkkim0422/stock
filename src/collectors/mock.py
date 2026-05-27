"""Mock collector — tests/fixtures/*.csv 로부터 데이터 반환.

Phase 1 에서 모든 데이터 호출은 여기로 라우팅된다.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from src.collectors.base import BaseCollector

_FIX_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"


class MockCollector(BaseCollector):
    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self.dir = fixtures_dir or _FIX_DIR

    def _load(self, market: str) -> pd.DataFrame:
        f = self.dir / f"sample_prices_{market}.csv"
        df = pd.read_csv(f, parse_dates=["date"], dtype={"symbol": str})
        df["date"] = df["date"].dt.date
        return df

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        market = "kr" if symbol.isdigit() and len(symbol) == 6 else "us"
        df = self._load(market)
        df = df[df["symbol"] == symbol]
        df = df[(df["date"] >= start) & (df["date"] <= end)]
        df = df.set_index("date")[["open", "high", "low", "close", "volume"]]
        return df

    def fetch_realtime(self, symbol: str) -> float:
        market = "kr" if symbol.isdigit() and len(symbol) == 6 else "us"
        df = self._load(market)
        df = df[df["symbol"] == symbol]
        if df.empty:
            raise ValueError(f"Mock: 종목 {symbol!r} 데이터가 없습니다")
        return float(df.sort_values("date").iloc[-1]["close"])


def get_mock_collector() -> MockCollector:
    return MockCollector()
