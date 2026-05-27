import pandas as pd
import pytest

from src.backtest import walk_forward, walk_forward_windows
from src.storage import apply_migrations


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "wf.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def _ohlcv(n: int) -> pd.DataFrame:
    closes = [100.0 + i * 0.2 for i in range(n)]
    idx = pd.date_range(end="2026-05-28", periods=n, freq="B").date
    return pd.DataFrame({
        "open": closes,
        "high": [c * 1.01 for c in closes],
        "low": [c * 0.99 for c in closes],
        "close": closes,
        "volume": [100000.0] * n,
    }, index=idx)


def test_window_generator_yields_pairs():
    df = _ohlcv(500)
    pairs = list(walk_forward_windows(df, train_months=6, test_months=1))
    assert len(pairs) >= 2
    for train, test in pairs:
        assert not train.empty
        assert not test.empty
        assert train.index[-1] < test.index[0]


def test_walk_forward_returns_results():
    df = _ohlcv(500)
    results = walk_forward("005930", df, train_months=6, test_months=1)
    assert isinstance(results, list)
