import pandas as pd

from src.backtest.metrics import compute, max_drawdown, sharpe_ratio


def test_max_drawdown_basic():
    curve = pd.Series([100, 110, 90, 95, 100])
    dd = max_drawdown(curve)
    # 110 → 90 = -18.18%
    assert dd < -18
    assert dd > -19


def test_sharpe_zero_when_no_variance():
    rets = pd.Series([0.0] * 10)
    assert sharpe_ratio(rets) == 0.0


def test_compute_empty_curve():
    m = compute(pd.Series(dtype=float), [])
    assert m.cagr_pct == 0
    assert m.n_trades == 0


def test_compute_with_trades():
    from datetime import date
    idx = pd.date_range(end="2026-05-28", periods=252, freq="B").date
    curve = pd.Series([100 + i for i in range(252)], index=idx)
    trades = [
        {"entry_date": date(2026, 1, 1), "exit_date": date(2026, 1, 10), "pnl": 50},
        {"entry_date": date(2026, 2, 1), "exit_date": date(2026, 2, 10), "pnl": -20},
        {"entry_date": date(2026, 3, 1), "exit_date": date(2026, 3, 10), "pnl": 30},
    ]
    m = compute(curve, trades)
    assert m.n_trades == 3
    assert m.win_rate_pct > 60  # 2/3
    assert m.profit_factor > 1  # 80 / 20
