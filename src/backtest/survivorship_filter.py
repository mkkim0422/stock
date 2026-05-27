"""survivorship bias 필터.

Phase 4 에서 상폐 종목 포함 데이터셋 사용 시 자동 필터.
Phase 1 인터페이스만.
"""
from __future__ import annotations

from datetime import date

import pandas as pd


def filter_active_only(symbols: pd.DataFrame, as_of: date) -> pd.DataFrame:
    """as_of 시점에 상장 중인 종목만.

    symbols DataFrame 컬럼: symbol, delisted_at(nullable)
    """
    if symbols.empty:
        return symbols
    if "delisted_at" not in symbols.columns:
        return symbols
    mask = symbols["delisted_at"].isna() | (pd.to_datetime(symbols["delisted_at"]).dt.date > as_of)
    return symbols[mask].copy()
