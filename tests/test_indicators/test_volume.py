import pandas as pd

from src.indicators import obv, volume_ratio


def test_volume_ratio_basic():
    v = pd.Series([100] * 20 + [200])
    vr = volume_ratio(v, n=20)
    # 직전 20봉 평균=100, 21번째=200 → vr=2.0
    assert vr.iloc[-1] == 2.0


def test_obv_uptrend():
    close = pd.Series([10, 11, 12, 13, 14])
    vol = pd.Series([100, 100, 100, 100, 100])
    o = obv(close, vol)
    # 4번 상승 → 누적 +400
    assert o.iloc[-1] == 400


def test_obv_alternating():
    close = pd.Series([10, 11, 10, 11, 10])
    vol = pd.Series([100, 100, 100, 100, 100])
    o = obv(close, vol)
    # +100 -100 +100 -100 = 0
    assert o.iloc[-1] == 0
