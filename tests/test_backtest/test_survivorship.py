from datetime import date

import pandas as pd

from src.backtest import filter_active_only


def test_active_only():
    df = pd.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "delisted_at": [None, "2025-01-01", "2030-01-01"],
        }
    )
    out = filter_active_only(df, date(2026, 1, 1))
    assert set(out["symbol"]) == {"A", "C"}


def test_no_delisted_col():
    df = pd.DataFrame({"symbol": ["A", "B"]})
    out = filter_active_only(df, date(2026, 1, 1))
    assert len(out) == 2
