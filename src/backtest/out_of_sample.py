"""OOS (Out-of-Sample) 검증."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.backtest.engine import BacktestResult, run_single


def split_in_out_of_sample(
    start: date, end: date, in_sample_ratio: float = 0.7
) -> tuple[date, date, date, date]:
    """기간을 in-sample / OOS 로 분리.

    반환: (is_start, is_end, oos_start, oos_end)
    """
    if not 0 < in_sample_ratio < 1:
        raise ValueError("in_sample_ratio must be in (0, 1)")
    total = (end - start).days
    split_days = int(total * in_sample_ratio)
    is_end = start + timedelta(days=split_days)
    oos_start = is_end + timedelta(days=1)
    return start, is_end, oos_start, end


def evaluate_oos(
    symbol: str,
    df: pd.DataFrame,
    market: str = "KR",
    in_sample_ratio: float = 0.7,
) -> tuple[BacktestResult, BacktestResult]:
    """In-sample / OOS 백테스트 각각 실행."""
    df = df.sort_index()
    s, is_end, oos_start, e = split_in_out_of_sample(
        df.index[0] if isinstance(df.index[0], date) else df.index[0].date(),
        df.index[-1] if isinstance(df.index[-1], date) else df.index[-1].date(),
        in_sample_ratio,
    )
    is_df = df[df.index <= is_end]
    oos_df = df[df.index >= oos_start]
    is_result = run_single(symbol, is_df, market=market)
    oos_result = run_single(
        symbol, oos_df, market=market,
        warmup_bars=min(200, len(oos_df) // 2),
    )
    return is_result, oos_result
