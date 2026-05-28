"""거시 / 시장 컨텍스트 수집기 — USD/KRW · KOSPI200 · S&P500 · NASDAQ.

FinanceDataReader 사용, 무료, 인증 불필요. 30분 캐시.
"""
from __future__ import annotations

import time
from datetime import date, timedelta

import pandas as pd

from src.utils.logger import get_logger

_log = get_logger("collectors.macro")
_CACHE: dict[str, pd.DataFrame] = {}
_CACHE_TS: dict[str, float] = {}
_TTL = 1800.0  # 30분

# 주요 지수 / 환율 코드 (FinanceDataReader)
TICKERS = {
    "USDKRW": "USD/KRW",
    "KOSPI200": "KS200",
    "KOSPI": "KS11",
    "KOSDAQ": "KQ11",
    "SP500": "US500",
    "NASDAQ": "IXIC",
}


def _get(code: str, days: int = 30) -> pd.DataFrame:
    """FDR 캐시 wrapper."""
    now = time.monotonic()
    if code in _CACHE and (now - _CACHE_TS.get(code, 0)) < _TTL:
        return _CACHE[code]
    try:
        import FinanceDataReader as fdr
        end = date.today()
        start = end - timedelta(days=days)
        df = fdr.DataReader(code, start.isoformat(), end.isoformat())
    except Exception as e:
        _log.warning("macro fetch 실패 (%s): %s", code, e)
        df = pd.DataFrame()
    _CACHE[code] = df
    _CACHE_TS[code] = now
    return df


def _pct_return(df: pd.DataFrame, days: int) -> float | None:
    if df.empty or len(df) < days + 1:
        return None
    col = next((c for c in ("Close", "close") if c in df.columns), None)
    if col is None:
        return None
    try:
        last = float(df[col].iloc[-1])
        prev = float(df[col].iloc[-(days + 1)])
        if prev == 0:
            return None
        return (last / prev - 1) * 100
    except Exception:
        return None


def context_snapshot() -> dict:
    """현재 거시 환경 한 줄 요약 + 5일/20일 수익률.

    반환: { name: {"value", "ret_5d", "ret_20d"} }
    """
    out: dict[str, dict] = {}
    for name, code in TICKERS.items():
        df = _get(code, days=40)
        if df.empty:
            out[name] = {"value": None, "ret_5d": None, "ret_20d": None}
            continue
        col = next((c for c in ("Close", "close") if c in df.columns), None)
        value = float(df[col].iloc[-1]) if col else None
        out[name] = {
            "value": value,
            "ret_5d": _pct_return(df, 5),
            "ret_20d": _pct_return(df, 20),
        }
    return out


# 섹터 ETF 매핑 — 한국 대표 섹터 ETF
SECTOR_ETF = {
    "반도체": "091160",          # KODEX 반도체
    "2차전지": "305720",         # KODEX 2차전지산업
    "바이오": "244580",          # KODEX 바이오
    "은행": "091170",            # KODEX 은행
    "자동차": "091180",          # KODEX 자동차
    "에너지화학": "117460",       # KODEX 에너지화학
    "건설": "117700",            # KODEX 건설
    "철강": "139260",            # TIGER 200 철강소재
    "증권": "102970",            # KODEX 증권
    "보험": "140700",            # KODEX 보험
    "운송": "140710",            # KODEX 운송
    "필수소비재": "227550",       # TIGER 200 생활소비재
    "미디어컨텐츠": "228810",     # TIGER 미디어컨텐츠
    "게임": "300610",            # KODEX 게임산업
}


def sector_etf_return(sector_or_industry: str, days: int = 5) -> float | None:
    """업종/섹터명으로 ETF 매핑 시도, 최근 N일 수익률 반환. 매핑 없으면 None."""
    key = None
    for k in SECTOR_ETF:
        if k in sector_or_industry:
            key = k
            break
    if not key:
        return None
    df = _get(SECTOR_ETF[key], days=days + 10)
    return _pct_return(df, days)


def macro_summary_text() -> str:
    """프롬프트용 거시 컨텍스트 한 줄."""
    ctx = context_snapshot()
    parts = []
    for name in ("KOSPI", "USDKRW", "SP500"):
        c = ctx.get(name, {})
        if c.get("ret_5d") is not None:
            parts.append(f"{name} 5일 {c['ret_5d']:+.1f}%")
    return " · ".join(parts) if parts else "거시 데이터 없음"
