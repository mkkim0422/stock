"""Collector 인터페이스. 실제 구현은 Phase 2."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class BaseCollector(ABC):
    """모든 데이터 소스가 따라야 할 인터페이스.

    Phase 1 에는 MockCollector 한 개만 구현된다.
    Phase 2 에서 PykrxCollector, YFinanceCollector, FDRCollector 추가.
    """

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        """OHLCV 일봉 반환. 컬럼: open/high/low/close/volume. 인덱스: date."""

    @abstractmethod
    def fetch_realtime(self, symbol: str) -> float:
        """현재가 (또는 가장 최근 종가) 반환."""
