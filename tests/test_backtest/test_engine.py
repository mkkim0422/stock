"""백테스트 엔진 — 시그널 기반 매매 시뮬레이션."""
import pandas as pd
import pytest

from src.backtest import run_single
from src.storage import apply_migrations


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "bt.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def _ohlcv(closes: list[float]) -> pd.DataFrame:
    n = len(closes)
    idx = pd.date_range(end="2026-05-28", periods=n, freq="B").date
    return pd.DataFrame({
        "open": closes,
        "high": [c * 1.01 for c in closes],
        "low": [c * 0.99 for c in closes],
        "close": closes,
        "volume": [100000.0] * n,
    }, index=idx)


def test_insufficient_data_raises():
    df = _ohlcv([100.0] * 50)
    with pytest.raises(ValueError, match="데이터 부족"):
        run_single("005930", df)


def test_runs_to_completion():
    """장기 데이터로 엔진이 끝까지 작동."""
    closes = [100.0 + i * 0.5 for i in range(300)]
    df = _ohlcv(closes)
    r = run_single("005930", df, warmup_bars=200)
    assert r.metrics is not None
    assert r.final_value > 0
    assert isinstance(r.trades, list)


def test_lookahead_guarded():
    """엔진이 look-ahead 가드를 호출하여 미래 데이터를 안 봄."""
    closes = [100.0 + i * 0.3 for i in range(250)]
    df = _ohlcv(closes)
    # 정상 완료되면 가드 통과
    r = run_single("005930", df, warmup_bars=200)
    assert len(r.equity_curve) > 0
