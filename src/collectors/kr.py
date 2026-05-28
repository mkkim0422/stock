"""한국 시세 수집기.

순서:
1) FinanceDataReader (pkg_resources 의존 없음 — 우선)
2) pykrx (백업; pkg_resources/setuptools 환경에 따라 실패 가능)

원칙:
- KRX 서버 부담 고려: 호출 간격 0.3s 이상.
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
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=15),
    reraise=True,
)
def _fdr_ohlcv(symbol: str, start: date, end: date) -> pd.DataFrame:
    """FinanceDataReader 로 OHLCV 조회 (pkg_resources 불필요)."""
    _throttle()
    import FinanceDataReader as fdr

    df = fdr.DataReader(symbol, start.isoformat(), end.isoformat())
    if df.empty:
        return df
    rename = {"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    df = df.rename(columns=rename)
    cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    return df[cols]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=15),
    reraise=True,
)
def _pykrx_ohlcv(symbol: str, start: date, end: date) -> pd.DataFrame:
    """pykrx 백업 경로 (pkg_resources 의존 — 실패 가능)."""
    _throttle()
    from pykrx import stock

    s = start.strftime("%Y%m%d")
    e = end.strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_date(s, e, symbol)
    rename = {"시가": "open", "고가": "high", "저가": "low", "종가": "close", "거래량": "volume"}
    df = df.rename(columns=rename)
    return df[["open", "high", "low", "close", "volume"]]


class PykrxCollector(BaseCollector):
    """이름은 호환을 위해 유지. 실제로는 FinanceDataReader 우선."""
    name = "kr"

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        cached = read_cached_ohlcv(symbol, start, end)
        expected_days = max(1, (end - start).days // 2)
        if not cached.empty and len(cached) >= expected_days:
            _log.debug("cache hit %s", symbol)
            return cached

        df: pd.DataFrame = pd.DataFrame()
        # 1) FinanceDataReader 시도
        try:
            df = _fdr_ohlcv(symbol, start, end)
        except Exception as e:
            _log.warning("FDR failed for %s: %s", symbol, e)

        # 2) pykrx 백업
        if df.empty:
            try:
                df = _pykrx_ohlcv(symbol, start, end)
            except Exception as e:
                _log.warning("pykrx failed for %s: %s", symbol, e)

        if df.empty:
            if not cached.empty:
                return cached
            return df

        cache_ohlcv(symbol, df)
        return df

    def fetch_realtime(self, symbol: str) -> float:
        from datetime import timedelta
        end = date.today()
        start = end - timedelta(days=10)
        df = self.fetch_ohlcv(symbol, start, end)
        if df.empty:
            raise ValueError(f"KR 데이터 없음: {symbol}")
        return float(df.iloc[-1]["close"])


def list_kr_symbols_from_krx(market: str = "ALL") -> list[dict]:
    """KRX 전종목 마스터 (KOSPI + KOSDAQ). FinanceDataReader 우선, pykrx 백업.

    반환: [{"symbol", "name", "market": "KR"}].
    """
    # FDR 시도
    try:
        import FinanceDataReader as fdr
        out: list[dict] = []
        markets = ["KOSPI", "KOSDAQ"] if market == "ALL" else [market]
        for m in markets:
            try:
                listing = fdr.StockListing(m)
            except Exception as e:
                _log.warning("FDR StockListing(%s) 실패: %s", m, e)
                continue
            for _, r in listing.iterrows():
                code = str(r.get("Code") or r.get("Symbol") or "").zfill(6)
                if not code or len(code) != 6:
                    continue
                name = str(r.get("Name") or "")
                out.append({"symbol": code, "name": name, "market": "KR"})
        if out:
            return out
    except Exception as e:
        _log.warning("FDR import 실패: %s", e)

    # pykrx 백업
    try:
        from pykrx import stock
        _throttle()
        today = date.today().strftime("%Y%m%d")
        out2: list[dict] = []
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
                out2.append({"symbol": t, "name": name, "market": "KR"})
        return out2
    except Exception as e:
        _log.warning("pykrx fallback 실패: %s", e)
        return []


def top_market_cap_kr(n: int = 100) -> list[dict]:
    """시가총액 상위 N개 한국 종목.

    반환: [{"symbol", "name", "market_cap" (억원 단위 또는 원), "market"}].
    """
    try:
        import FinanceDataReader as fdr
    except Exception as e:
        _log.warning("FDR import 실패: %s", e)
        return []

    rows: list[dict] = []
    for m in ("KOSPI", "KOSDAQ"):
        try:
            listing = fdr.StockListing(m)
        except Exception as e:
            _log.warning("FDR StockListing(%s) 실패: %s", m, e)
            continue
        # 컬럼: Code, Name, Marcap (대문자 M) 또는 MarketCap 등 — 버전마다 다름
        cap_col = next(
            (c for c in ("Marcap", "MarketCap", "marcap", "market_cap") if c in listing.columns),
            None,
        )
        if cap_col is None:
            continue
        listing = listing[listing[cap_col].notna()].copy()
        for _, r in listing.iterrows():
            code = str(r.get("Code") or r.get("Symbol") or "").zfill(6)
            if len(code) != 6 or not code.isdigit():
                continue
            name = str(r.get("Name") or "")
            try:
                cap = float(r[cap_col])
            except (TypeError, ValueError):
                continue
            rows.append({
                "symbol": code, "name": name, "market_cap": cap, "market": "KR",
                "kospi_or_kosdaq": m,
            })

    rows.sort(key=lambda x: x["market_cap"], reverse=True)
    return rows[:n]
