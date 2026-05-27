"""백테스트 성과 메트릭 — CAGR, Sharpe, Sortino, MDD, 승률, Profit Factor."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

_TRADING_DAYS = 252


@dataclass(slots=True)
class Metrics:
    cagr_pct: float
    total_return_pct: float
    sharpe: float
    sortino: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    n_trades: int
    avg_holding_days: float
    start: date
    end: date


def _annualize_return(curve: pd.Series) -> float:
    if len(curve) < 2:
        return 0.0
    total_ret = float(curve.iloc[-1] / curve.iloc[0]) - 1.0
    years = max(1e-9, len(curve) / _TRADING_DAYS)
    return (1 + total_ret) ** (1 / years) - 1.0


def sharpe_ratio(returns: pd.Series, rf_annual: float = 0.0) -> float:
    if returns.std() == 0 or len(returns) < 2:
        return 0.0
    daily_rf = (1 + rf_annual) ** (1 / _TRADING_DAYS) - 1
    excess = returns - daily_rf
    return float(excess.mean() / excess.std() * np.sqrt(_TRADING_DAYS))


def sortino_ratio(returns: pd.Series, rf_annual: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    daily_rf = (1 + rf_annual) ** (1 / _TRADING_DAYS) - 1
    excess = returns - daily_rf
    downside = excess[excess < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0.0
    return float(excess.mean() / downside.std() * np.sqrt(_TRADING_DAYS))


def max_drawdown(curve: pd.Series) -> float:
    """최대 낙폭 (음수, %)."""
    if len(curve) < 2:
        return 0.0
    peak = curve.cummax()
    dd = (curve / peak - 1.0) * 100
    return float(dd.min())


def compute(
    equity_curve: pd.Series,
    trades: list[dict],
) -> Metrics:
    """자산곡선 + 거래 리스트로 메트릭 계산.

    equity_curve: 날짜 인덱스, 자산 평가액(KRW) 시리즈.
    trades: [{"entry_date", "exit_date", "pnl"}].
    """
    if equity_curve.empty:
        return Metrics(0, 0, 0, 0, 0, 0, 0, 0, 0,
                       date.today(), date.today())

    returns = equity_curve.pct_change().dropna()
    total_ret = float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100
    cagr = _annualize_return(equity_curve) * 100
    sh = sharpe_ratio(returns)
    so = sortino_ratio(returns)
    mdd = max_drawdown(equity_curve)

    closed = [t for t in trades if t.get("exit_date") is not None]
    if closed:
        wins = [t for t in closed if t["pnl"] > 0]
        losses = [t for t in closed if t["pnl"] <= 0]
        win_rate = len(wins) / len(closed) * 100
        gross_profit = sum(t["pnl"] for t in wins)
        gross_loss = abs(sum(t["pnl"] for t in losses)) or 1e-9
        pf = gross_profit / gross_loss
        avg_hold = float(np.mean(
            [(t["exit_date"] - t["entry_date"]).days for t in closed]
        ))
    else:
        win_rate = 0.0
        pf = 0.0
        avg_hold = 0.0

    start_idx = equity_curve.index[0]
    end_idx = equity_curve.index[-1]
    start = start_idx if isinstance(start_idx, date) else start_idx.date()
    end = end_idx if isinstance(end_idx, date) else end_idx.date()

    return Metrics(
        cagr_pct=cagr,
        total_return_pct=total_ret,
        sharpe=sh,
        sortino=so,
        max_drawdown_pct=mdd,
        win_rate_pct=win_rate,
        profit_factor=pf,
        n_trades=len(closed),
        avg_holding_days=avg_hold,
        start=start,
        end=end,
    )
