"""거래량 지표.

- volume_ratio(VR): 직전 n봉 평균 대비 현재 거래량 배수.
- obv: 종가 상승 시 +volume, 하락 시 -volume 누적.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def volume_ratio(volume: pd.Series, n: int = 20) -> pd.Series:
    avg = volume.shift(1).rolling(window=n, min_periods=n).mean()
    return volume / avg


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).cumsum()
