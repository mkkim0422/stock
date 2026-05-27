"""미국 시세 수집기 — yfinance 우선, 차단/실패 시 FinanceDataReader 폴백."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from src.collectors.base import BaseCollector
from src.collectors.cache import cache_ohlcv, read_cached_ohlcv
from src.utils.logger import get_logger

_log = get_logger("collectors.us")


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume",
            "Adj Close": "adj_close",
        }
    )
    if isinstance(df.index, pd.DatetimeIndex):
        df.index = df.index.date
    return df[[c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    reraise=True,
)
def _yf_ohlcv(symbol: str, start: date, end: date) -> pd.DataFrame:
    import yfinance as yf

    t = yf.Ticker(symbol)
    df = t.history(
        start=start.isoformat(),
        end=(end + timedelta(days=1)).isoformat(),
        auto_adjust=False,
    )
    if df.empty:
        raise RuntimeError(f"yfinance empty for {symbol}")
    return _normalize(df)


def _fdr_ohlcv(symbol: str, start: date, end: date) -> pd.DataFrame:
    import FinanceDataReader as fdr

    df = fdr.DataReader(symbol, start.isoformat(), end.isoformat())
    if df.empty:
        raise RuntimeError(f"FDR empty for {symbol}")
    return _normalize(df)


class USCollector(BaseCollector):
    """yfinance 우선, FDR 폴백, 캐시 마지막."""

    name = "us-multi"

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        cached = read_cached_ohlcv(symbol, start, end)
        if not cached.empty and len(cached) >= max(1, (end - start).days // 2):
            return cached

        for name, fn in (("yfinance", _yf_ohlcv), ("FDR", _fdr_ohlcv)):
            try:
                df = fn(symbol, start, end)
                if not df.empty:
                    cache_ohlcv(symbol, df)
                    return df
            except Exception as e:
                _log.warning("%s failed for %s: %s", name, symbol, e)
                continue

        if not cached.empty:
            _log.warning("all sources failed, using cache for %s", symbol)
            return cached
        raise RuntimeError(f"모든 US 데이터 소스 실패: {symbol}")

    def fetch_realtime(self, symbol: str) -> float:
        end = date.today()
        start = end - timedelta(days=10)
        df = self.fetch_ohlcv(symbol, start, end)
        if df.empty:
            raise ValueError(f"US realtime 실패: {symbol}")
        return float(df.iloc[-1]["close"])
