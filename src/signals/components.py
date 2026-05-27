"""시그널 컴포넌트 — 각 지표가 +/- 점수 반환.

docs/SIGNALS.md 가중치 표 그대로 구현.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.indicators import macd, obv, rsi, sma, volume_ratio


@dataclass(slots=True)
class Component:
    name: str
    score: int
    reason: str


def score_rsi(close: pd.Series, n: int = 14) -> Component:
    if len(close) < n + 1:
        return Component("RSI", 0, "데이터 부족")
    r = rsi(close, n).iloc[-1]
    if pd.isna(r):
        return Component("RSI", 0, "RSI 계산 불가")
    if r < 30:
        return Component("RSI", 2, f"RSI {r:.1f} < 30 (과매도)")
    if r > 70:
        return Component("RSI", -2, f"RSI {r:.1f} > 70 (과매수)")
    return Component("RSI", 0, f"RSI {r:.1f} (중립)")


def score_macd_cross(close: pd.Series) -> Component:
    if len(close) < 35:
        return Component("MACD", 0, "데이터 부족")
    m = macd(close)
    hist = m["hist"]
    if hist.isna().iloc[-2:].any():
        return Component("MACD", 0, "MACD 계산 불가")
    prev = hist.iloc[-2]
    cur = hist.iloc[-1]
    if prev < 0 and cur > 0:
        return Component("MACD", 3, "MACD 골든크로스")
    if prev > 0 and cur < 0:
        return Component("MACD", -3, "MACD 데드크로스")
    return Component("MACD", 0, f"MACD 히스토그램 {cur:+.3f} (추세 유지)")


def score_ma_above(close: pd.Series, n: int, weight: int = 1) -> Component:
    if len(close) < n:
        return Component(f"MA{n}", 0, "데이터 부족")
    ma_n = sma(close, n)
    if pd.isna(ma_n.iloc[-1]):
        return Component(f"MA{n}", 0, "MA 계산 불가")
    last = close.iloc[-1]
    m = ma_n.iloc[-1]
    if last > m:
        return Component(f"MA{n}", weight, f"종가 {last:,.0f} > MA{n} {m:,.0f}")
    return Component(f"MA{n}", 0, f"종가 {last:,.0f} <= MA{n} {m:,.0f}")


def score_short_term_overheat(close: pd.Series, days: int = 5, threshold_pct: float = 5.0) -> Component:
    if len(close) < days + 1:
        return Component("단기과열", 0, "데이터 부족")
    chg = (close.iloc[-1] / close.iloc[-(days + 1)] - 1) * 100
    if chg >= threshold_pct:
        return Component("단기과열", -1, f"{days}일 +{chg:.1f}% (과열)")
    return Component("단기과열", 0, f"{days}일 {chg:+.1f}%")


def score_volume_surge(volume: pd.Series, n: int = 20, multiplier: float = 2.0) -> Component:
    if len(volume) < n + 1:
        return Component("거래량", 0, "데이터 부족")
    vr = volume_ratio(volume, n).iloc[-1]
    if pd.isna(vr):
        return Component("거래량", 0, "VR 계산 불가")
    if vr >= multiplier:
        return Component("거래량", 2, f"거래량 평균 {vr:.1f}x")
    return Component("거래량", 0, f"거래량 평균 {vr:.1f}x")


def score_obv_trend(close: pd.Series, volume: pd.Series, n: int = 20) -> Component:
    """OBV 가 단기 평균보다 위면 매집, 아래면 분산."""
    if len(close) < n + 1:
        return Component("OBV", 0, "데이터 부족")
    o = obv(close, volume)
    o_sma = o.rolling(window=n, min_periods=n).mean()
    if pd.isna(o_sma.iloc[-1]):
        return Component("OBV", 0, "OBV 계산 불가")
    if o.iloc[-1] > o_sma.iloc[-1]:
        return Component("OBV", 1, "OBV 매집 추세")
    return Component("OBV", 0, "OBV 분산 추세")
