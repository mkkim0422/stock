"""시그널 엔진 — 컴포넌트 합산 → action 결정 + DB 기록.

가중치 기준점 (확정):
- BUY  ≥ +8
- SELL ≤ -3
- 그 외: HOLD
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Literal

import pandas as pd

from src.config.constants import SIGNAL_BUY_THRESHOLD, SIGNAL_SELL_THRESHOLD
from src.signals.base import SignalOutput
from src.signals.components import (
    Component,
    score_ma_above,
    score_macd_cross,
    score_obv_trend,
    score_rsi,
    score_short_term_overheat,
    score_volume_surge,
)
from src.storage import connect
from src.utils.timezone import now_kst

Action = Literal["BUY", "SELL", "HOLD"]


def _decide(score: int) -> Action:
    if score >= SIGNAL_BUY_THRESHOLD:
        return "BUY"
    if score <= SIGNAL_SELL_THRESHOLD:
        return "SELL"
    return "HOLD"


def evaluate(symbol: str, df: pd.DataFrame, ts: datetime | None = None) -> SignalOutput:
    """OHLCV DataFrame 으로 종합 시그널 평가.

    df 컬럼: open, high, low, close, volume.
    """
    if df.empty:
        raise ValueError("빈 데이터로 시그널 평가 불가")
    close = df["close"].astype(float)
    volume = df["volume"].astype(float)
    ts = ts or now_kst()

    comps: list[Component] = [
        score_rsi(close),
        score_macd_cross(close),
        score_ma_above(close, 20, weight=1),
        score_ma_above(close, 60, weight=1),
        score_ma_above(close, 200, weight=1),
        score_short_term_overheat(close, days=5, threshold_pct=5.0),
        score_volume_surge(volume, n=20, multiplier=2.0),
        score_obv_trend(close, volume, n=20),
    ]
    total = sum(c.score for c in comps)
    return SignalOutput(
        ts=ts,
        symbol=symbol,
        score=total,
        components={c.name: {"score": c.score, "reason": c.reason} for c in comps},
        action=_decide(total),
    )


def persist(signal: SignalOutput) -> int:
    """DB signals 테이블에 기록. 반환: id."""
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO signals (ts, symbol, score, components, action)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                signal.ts.isoformat(timespec="seconds"),
                signal.symbol,
                signal.score,
                json.dumps(signal.components, ensure_ascii=False),
                signal.action,
            ),
        )
        rid = cur.lastrowid
        if rid is None:
            raise RuntimeError("INSERT failed (lastrowid None)")
        return rid


def evaluate_and_persist(symbol: str, df: pd.DataFrame) -> SignalOutput:
    s = evaluate(symbol, df)
    persist(s)
    return s


def latest_signals(limit: int = 20) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT ts, symbol, score, components, action FROM signals "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "ts": r["ts"],
            "symbol": r["symbol"],
            "score": int(r["score"]),
            "components": json.loads(r["components"]),
            "action": r["action"],
        })
    return out


def latest_signal_for(symbol: str) -> dict | None:
    with connect() as conn:
        r = conn.execute(
            "SELECT ts, symbol, score, components, action FROM signals "
            "WHERE symbol=? ORDER BY id DESC LIMIT 1",
            (symbol,),
        ).fetchone()
    if r is None:
        return None
    return {
        "ts": r["ts"],
        "symbol": r["symbol"],
        "score": int(r["score"]),
        "components": json.loads(r["components"]),
        "action": r["action"],
    }
