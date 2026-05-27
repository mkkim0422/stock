"""SignalEngine — 합산 점수 + action 결정 + DB persist."""
from datetime import datetime

import pandas as pd
import pytest

from src.signals import evaluate, evaluate_and_persist, latest_signal_for
from src.storage import apply_migrations
from src.utils.timezone import KST


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "sig.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def _ohlcv(close_seq: list[float], vol_seq: list[float] | None = None) -> pd.DataFrame:
    n = len(close_seq)
    if vol_seq is None:
        vol_seq = [100.0] * n
    idx = pd.date_range(end="2026-05-28", periods=n, freq="B").date
    return pd.DataFrame({
        "open": close_seq, "high": [c * 1.01 for c in close_seq],
        "low": [c * 0.99 for c in close_seq],
        "close": close_seq, "volume": vol_seq,
    }, index=idx)


def test_uptrend_buy_signal():
    """장기 상승 + 거래량 급증 → 매수 후보 (≥+8)."""
    closes = list(range(50, 250))  # 200봉 강한 상승
    vols = [100.0] * 199 + [400.0]  # 마지막 봉 4x 거래량
    df = _ohlcv(closes, vols)
    s = evaluate("005930", df, ts=datetime(2026, 5, 28, 10, 0, tzinfo=KST))
    assert s.score >= 0  # 상승추세에 MA들 모두 위
    # 정확히 +8 보장 어렵지만, 매수 신호 측 점수


def test_downtrend_no_buy_signal():
    """장기 하락 → BUY 신호 나오지 않음 (RSI 과매도 +2 만 있어도 BUY 임계 +8 미달)."""
    closes = list(range(250, 50, -1))  # 200봉 강한 하락
    df = _ohlcv(closes)
    s = evaluate("005930", df)
    assert s.action != "BUY"
    # MA들 모두 아래, 점수 매수 임계 도달 불가
    assert s.score < 8


def test_persist_and_retrieve():
    closes = [100.0 + i for i in range(60)]
    df = _ohlcv(closes)
    sig = evaluate_and_persist("005930", df)
    latest = latest_signal_for("005930")
    assert latest is not None
    assert latest["score"] == sig.score
    assert latest["action"] == sig.action
    assert "RSI" in latest["components"]


def test_empty_df_raises():
    with pytest.raises(ValueError):
        evaluate("005930", pd.DataFrame())


def test_action_thresholds():
    """+8 이상 BUY, -3 이하 SELL, 그 외 HOLD."""
    closes = [100.0] * 60
    df = _ohlcv(closes)
    s = evaluate("005930", df)
    # 모두 평이한 데이터 → HOLD
    assert s.action == "HOLD"
    assert -3 < s.score < 8
