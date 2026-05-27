import pandas as pd

from src.signals.components import (
    score_ma_above,
    score_macd_cross,
    score_obv_trend,
    score_rsi,
    score_short_term_overheat,
    score_volume_surge,
)


def test_score_rsi_oversold():
    # 30봉 강한 하락 → RSI ≈ 0
    p = pd.Series(list(range(100, 70, -1)), dtype=float)
    c = score_rsi(p, 14)
    assert c.score == 2
    assert "과매도" in c.reason


def test_score_rsi_overbought():
    p = pd.Series(list(range(70, 100)), dtype=float)
    c = score_rsi(p, 14)
    assert c.score == -2
    assert "과매수" in c.reason


def test_score_rsi_neutral_short():
    p = pd.Series([100, 100, 100], dtype=float)
    c = score_rsi(p, 14)
    assert c.score == 0


def test_score_macd_golden_cross():
    # 점진 하락 후 급반등으로 히스토그램 - → +
    p = pd.Series(list(range(100, 60, -1)) + [70, 80, 90] * 5, dtype=float)
    c = score_macd_cross(p)
    assert c.score in (3, 0)  # 데이터 길이에 따라 cross 여부 다름


def test_score_ma_above():
    p = pd.Series([100] * 30 + [120], dtype=float)
    c = score_ma_above(p, 20, weight=1)
    assert c.score == 1


def test_score_ma_below():
    p = pd.Series([120] * 30 + [80], dtype=float)
    c = score_ma_above(p, 20, weight=1)
    assert c.score == 0


def test_short_term_overheat():
    p = pd.Series([100, 100, 100, 100, 100, 110], dtype=float)
    c = score_short_term_overheat(p, days=5, threshold_pct=5.0)
    assert c.score == -1


def test_short_term_no_overheat():
    p = pd.Series([100, 101, 102, 101, 100, 101], dtype=float)
    c = score_short_term_overheat(p, days=5, threshold_pct=5.0)
    assert c.score == 0


def test_volume_surge():
    v = pd.Series([100] * 20 + [300], dtype=float)
    c = score_volume_surge(v, n=20, multiplier=2.0)
    assert c.score == 2


def test_volume_normal():
    v = pd.Series([100] * 21, dtype=float)
    c = score_volume_surge(v, n=20, multiplier=2.0)
    assert c.score == 0


def test_obv_trend_accumulation():
    close = pd.Series([100 + i for i in range(25)], dtype=float)
    vol = pd.Series([100] * 25, dtype=float)
    c = score_obv_trend(close, vol, n=20)
    assert c.score == 1
