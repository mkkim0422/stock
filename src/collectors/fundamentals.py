"""펀더멘털 데이터 — FinanceDataReader StockListing 스냅샷.

KRX 전종목 PER/PBR/EPS/BPS/시총/배당/섹터 정보. 일중에는 거의 변화 없으므로 1시간 캐시.
무료, 인증 불필요.
"""
from __future__ import annotations

import time
from typing import TypedDict

import pandas as pd

from src.utils.logger import get_logger

_log = get_logger("collectors.fundamentals")

_CACHE: dict[str, dict] = {}
_CACHE_TS = 0.0
_TTL = 3600.0  # 1시간


class Fundamental(TypedDict, total=False):
    symbol: str
    name: str
    market: str          # KOSPI / KOSDAQ
    sector: str
    industry: str
    market_cap: float    # 시가총액 (원 단위)
    shares: float        # 발행주식수
    per: float | None
    pbr: float | None
    eps: float | None
    bps: float | None
    dividend_yield: float | None


def _load_all() -> dict[str, dict]:
    """KRX 전종목 펀더멘털을 한 번에 받아 dict[code]=info."""
    global _CACHE, _CACHE_TS
    now = time.monotonic()
    if _CACHE and (now - _CACHE_TS) < _TTL:
        return _CACHE
    try:
        import FinanceDataReader as fdr
    except Exception as e:
        _log.warning("FDR import 실패: %s", e)
        return {}

    out: dict[str, dict] = {}
    for m in ("KOSPI", "KOSDAQ"):
        try:
            df = fdr.StockListing(m)
        except Exception as e:
            _log.warning("FDR StockListing(%s) 실패: %s", m, e)
            continue

        # 컬럼명이 FDR 버전마다 다름 — 가능한 후보들을 매핑.
        col = {c: c for c in df.columns}
        getc = lambda r, *names: next((r.get(n) for n in names if n in r and pd.notna(r.get(n))), None)

        for _, r in df.iterrows():
            code = str(r.get("Code") or r.get("Symbol") or "").zfill(6)
            if len(code) != 6 or not code.isdigit():
                continue
            try:
                cap = float(getc(r, "Marcap", "MarketCap", "marcap") or 0)
            except (TypeError, ValueError):
                cap = 0
            try:
                shares = float(getc(r, "Stocks", "Shares", "stocks") or 0)
            except (TypeError, ValueError):
                shares = 0
            per = _maybe_float(getc(r, "PER", "Per"))
            pbr = _maybe_float(getc(r, "PBR", "Pbr"))
            eps = _maybe_float(getc(r, "EPS", "Eps"))
            bps = _maybe_float(getc(r, "BPS", "Bps"))
            dy  = _maybe_float(getc(r, "DividendYield", "DPS", "Dividend"))
            sector = str(getc(r, "Sector", "Industry") or "")
            industry = str(getc(r, "Industry", "Sector") or "")
            out[code] = {
                "symbol": code,
                "name": str(r.get("Name") or ""),
                "market": m,
                "sector": sector,
                "industry": industry,
                "market_cap": cap,
                "shares": shares,
                "per": per,
                "pbr": pbr,
                "eps": eps,
                "bps": bps,
                "dividend_yield": dy,
            }

    _CACHE = out
    _CACHE_TS = now
    return out


def _maybe_float(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if pd.isna(f) or f == 0:
        return None if f == 0 else None  # 0/NaN → None
    return f


def get(symbol: str) -> Fundamental | None:
    all_ = _load_all()
    if not all_:
        return None
    r = all_.get(symbol)
    if r is None:
        return None
    return r  # type: ignore[return-value]


def industry_median_per(industry: str) -> float | None:
    """동일 업종 PER 중앙값 — 상대 밸류에이션 기준."""
    all_ = _load_all()
    pers = [
        r["per"] for r in all_.values()
        if r.get("industry") == industry and r.get("per") and r["per"] > 0
    ]
    if len(pers) < 3:
        return None
    pers.sort()
    return pers[len(pers) // 2]
