"""한국 시세 수집기 (pykrx).

원칙:
- KRX 서버 부담을 고려해 호출 간격 0.3s 이상.
- 429/5xx 대응: tenacity 지수 백오프 (최대 5회).
- 결과는 prices 테이블에 캐시.
"""
from __future__ import annotations

import time
from datetime import date

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from src.collectors.base import BaseCollector
from src.collectors.cache import cache_ohlcv, read_cached_ohlcv
from src.utils.logger import get_logger

_log = get_logger("collectors.kr")
_LAST_CALL_TS = 0.0
_MIN_INTERVAL_SEC = 0.3


def _throttle() -> None:
    global _LAST_CALL_TS
    now = time.monotonic()
    diff = now - _LAST_CALL_TS
    if diff < _MIN_INTERVAL_SEC:
        time.sleep(_MIN_INTERVAL_SEC - diff)
    _LAST_CALL_TS = time.monotonic()


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    reraise=True,
)
def _krx_ohlcv(symbol: str, start: date, end: date) -> pd.DataFrame:
    _throttle()
    from pykrx import stock

    s = start.strftime("%Y%m%d")
    e = end.strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_date(s, e, symbol)
    # 컬럼명 한글 → 영어
    rename = {"시가": "open", "고가": "high", "저가": "low", "종가": "close", "거래량": "volume"}
    df = df.rename(columns=rename)
    return df[["open", "high", "low", "close", "volume"]]


class PykrxCollector(BaseCollector):
    name = "pykrx"

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        # 캐시 우선
        cached = read_cached_ohlcv(symbol, start, end)
        expected_days = max(1, (end - start).days // 2)  # 영업일 절반 가정
        if not cached.empty and len(cached) >= expected_days:
            _log.debug("cache hit %s", symbol)
            return cached
        try:
            df = _krx_ohlcv(symbol, start, end)
        except Exception as e:
            _log.warning("pykrx failed for %s: %s", symbol, e)
            if not cached.empty:
                return cached
            raise
        if df.empty:
            return cached if not cached.empty else df
        cache_ohlcv(symbol, df)
        return df

    def fetch_realtime(self, symbol: str) -> float:
        from datetime import timedelta
        end = date.today()
        start = end - timedelta(days=10)
        df = self.fetch_ohlcv(symbol, start, end)
        if df.empty:
            raise ValueError(f"pykrx: 데이터 없음 {symbol}")
        return float(df.iloc[-1]["close"])


def list_kr_symbols_from_krx(market: str = "ALL") -> list[dict]:
    """KRX 전종목 마스터 (KOSPI + KOSDAQ).

    반환: [{"symbol", "name"}].
    """
    from pykrx import stock

    _throttle()
    today = date.today().strftime("%Y%m%d")
    out: list[dict] = []
    markets = ["KOSPI", "KOSDAQ"] if market == "ALL" else [market]
    for m in markets:
        try:
            tickers = stock.get_market_ticker_list(today, market=m)
        except Exception as e:
            _log.warning("KRX ticker list failed (%s): %s", m, e)
            continue
        for t in tickers:
            try:
                name = stock.get_market_ticker_name(t)
            except Exception:
                name = ""
            out.append({"symbol": t, "name": name, "market": "KR"})
    return out
