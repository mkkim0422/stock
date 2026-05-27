"""워크포워드 검증 — 슬라이딩 윈도우로 백테스트 반복."""
from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta

import pandas as pd

from src.backtest.engine import BacktestResult, run_single


def walk_forward_windows(
    df: pd.DataFrame,
    train_months: int = 6,
    test_months: int = 1,
) -> Iterator[tuple[pd.DataFrame, pd.DataFrame]]:
    """슬라이딩 윈도우 generator. (train_df, test_df) 쌍 반환."""
    if df.empty:
        return
    df = df.sort_index()
    start = df.index[0]
    end = df.index[-1]
    cur_train_start = start
    while True:
        cur_train_end = cur_train_start + timedelta(days=train_months * 30)
        cur_test_end = cur_train_end + timedelta(days=test_months * 30)
        if cur_test_end > end:
            return
        train = df[(df.index >= cur_train_start) & (df.index < cur_train_end)]
        test = df[(df.index >= cur_train_end) & (df.index < cur_test_end)]
        if not train.empty and not test.empty:
            yield train, test
        cur_train_start = cur_train_start + timedelta(days=test_months * 30)


def walk_forward(
    symbol: str,
    df: pd.DataFrame,
    market: str = "KR",
    train_months: int = 6,
    test_months: int = 1,
) -> list[BacktestResult]:
    """각 윈도우에서 train+test 결합 후 백테스트. test 구간 결과만 반환."""
    results: list[BacktestResult] = []
    for train, test in walk_forward_windows(df, train_months, test_months):
        combined = pd.concat([train, test])
        try:
            r = run_single(
                symbol, combined, market=market,
                warmup_bars=min(200, len(train) - 1),
            )
            results.append(r)
        except ValueError:
            continue
    return results
