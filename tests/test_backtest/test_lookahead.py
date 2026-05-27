from datetime import date

import pandas as pd
import pytest

from src.backtest import LookaheadError, check_no_lookahead


def test_no_lookahead_ok():
    df = pd.DataFrame({"x": [1, 2]}, index=pd.to_datetime(["2026-01-01", "2026-01-02"]))
    check_no_lookahead(df, date(2026, 1, 3))


def test_lookahead_detected():
    df = pd.DataFrame({"x": [1]}, index=pd.to_datetime(["2026-01-05"]))
    with pytest.raises(LookaheadError):
        check_no_lookahead(df, date(2026, 1, 5))


def test_lookahead_strict_future():
    df = pd.DataFrame({"x": [1]}, index=pd.to_datetime(["2026-02-01"]))
    with pytest.raises(LookaheadError):
        check_no_lookahead(df, date(2026, 1, 1))


def test_empty_df_ok():
    df = pd.DataFrame()
    check_no_lookahead(df, date(2026, 1, 1))
