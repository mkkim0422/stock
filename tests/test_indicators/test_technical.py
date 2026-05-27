import pandas as pd
import pytest

from src.indicators import ema, macd, rsi, sma


def test_sma_basic():
    p = pd.Series([1, 2, 3, 4, 5, 6])
    out = sma(p, 3)
    assert out.iloc[2] == pytest.approx(2.0)
    assert out.iloc[5] == pytest.approx(5.0)


def test_ema_basic():
    p = pd.Series([1, 2, 3, 4, 5])
    out = ema(p, 2)
    # EMA(2): alpha=2/(2+1)=2/3
    # ema[0]=1
    # ema[1]=1*1/3 + 2*2/3 = 5/3 ≈ 1.6667
    # ema[2]=5/3*1/3 + 3*2/3 = 23/9 ≈ 2.5556
    assert out.iloc[0] == pytest.approx(1.0)
    assert out.iloc[1] == pytest.approx(5/3, rel=1e-4)


def test_rsi_uptrend_high():
    p = pd.Series(list(range(1, 30)), dtype=float)
    out = rsi(p, 14)
    assert out.iloc[-1] >= 95  # 순상승이면 RSI ≈ 100


def test_rsi_downtrend_low():
    p = pd.Series(list(range(30, 0, -1)), dtype=float)
    out = rsi(p, 14)
    assert out.iloc[-1] <= 5  # 순하락이면 RSI ≈ 0


def test_macd_columns():
    p = pd.Series([100 + i for i in range(60)], dtype=float)
    m = macd(p)
    assert set(m.columns) == {"macd", "signal", "hist"}
    assert len(m) == len(p)
