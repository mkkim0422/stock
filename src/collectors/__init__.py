"""Collector 라우터 — symbol 시장에 따라 적절한 collector 선택.

Phase 1 호환을 위해 MockCollector도 노출. 환경변수 USE_MOCK=1 일 때 mock 사용.
"""
from __future__ import annotations

import os
from datetime import date

import pandas as pd

from src.collectors.base import BaseCollector
from src.collectors.mock import MockCollector, get_mock_collector


def _is_kr(symbol: str) -> bool:
    return symbol.isdigit() and len(symbol) == 6


def _use_mock() -> bool:
    return os.environ.get("USE_MOCK", "0") == "1"


_kr_singleton: BaseCollector | None = None
_us_singleton: BaseCollector | None = None
_mock_singleton: MockCollector | None = None


def _get_kr() -> BaseCollector:
    global _kr_singleton
    if _kr_singleton is None:
        from src.collectors.kr import PykrxCollector
        _kr_singleton = PykrxCollector()
    return _kr_singleton


def _get_us() -> BaseCollector:
    global _us_singleton
    if _us_singleton is None:
        from src.collectors.us import USCollector
        _us_singleton = USCollector()
    return _us_singleton


def _get_mock() -> MockCollector:
    global _mock_singleton
    if _mock_singleton is None:
        _mock_singleton = MockCollector()
    return _mock_singleton


def get_collector(symbol: str) -> BaseCollector:
    if _use_mock():
        return _get_mock()
    return _get_kr() if _is_kr(symbol) else _get_us()


def fetch_realtime(symbol: str) -> float:
    return get_collector(symbol).fetch_realtime(symbol)


def fetch_ohlcv(symbol: str, start: date, end: date) -> pd.DataFrame:
    return get_collector(symbol).fetch_ohlcv(symbol, start, end)


__all__ = [
    "BaseCollector",
    "MockCollector",
    "get_mock_collector",
    "get_collector",
    "fetch_realtime",
    "fetch_ohlcv",
]
