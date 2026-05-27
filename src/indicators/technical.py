"""기술 지표 (numpy + pandas 직접 구현).

pandas-ta / ta-lib 의존 금지. 수식은 docs/INDICATORS.md.
"""
from __future__ import annotations

import pandas as pd


def sma(price: pd.Series, n: int = 20) -> pd.Series:
    return price.rolling(window=n, min_periods=n).mean()


def ema(price: pd.Series, n: int = 12) -> pd.Series:
    return price.ewm(span=n, adjust=False).mean()


def rsi(price: pd.Series, n: int = 14) -> pd.Series:
    """Wilder 평균 (rolling mean 대신 ewm alpha=1/n)."""
    delta = price.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    out = 100 - 100 / (1 + rs)
    out = out.fillna(100)  # 모든 손실이 0일 때
    return out


def macd(
    price: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    ema_fast = ema(price, fast)
    ema_slow = ema(price, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})
