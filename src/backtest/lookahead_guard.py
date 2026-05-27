"""look-ahead bias 가드.

원칙: 시점 t 에서 의사결정 시, 입력은 t-1 까지의 데이터만 허용.
"""
from __future__ import annotations

from datetime import date

import pandas as pd


class LookaheadError(Exception):
    """미래 데이터 접근 감지."""


def check_no_lookahead(df: pd.DataFrame, decision_date: date) -> None:
    """df 인덱스가 모두 decision_date 이전인지 검사."""
    if df.empty:
        return
    max_d = df.index.max()
    if isinstance(max_d, pd.Timestamp):
        max_d = max_d.date()
    if max_d >= decision_date:
        raise LookaheadError(
            f"look-ahead detected: max date in df is {max_d}, decision date is {decision_date}"
        )
