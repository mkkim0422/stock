"""USCollector 다중 소스 폴백 검증 (네트워크 mock)."""
from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest

from src.collectors.us import USCollector
from src.storage import apply_migrations


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "us.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def _sample_df():
    idx = pd.to_datetime(["2026-05-26", "2026-05-27"]).date
    return pd.DataFrame({
        "open": [200.0, 201.0], "high": [202.0, 203.0],
        "low": [199.0, 200.0], "close": [201.5, 202.5],
        "volume": [10000, 11000],
    }, index=idx)


def test_yfinance_success():
    with patch("src.collectors.us._yf_ohlcv", return_value=_sample_df()) as yf:
        c = USCollector()
        df = c.fetch_ohlcv("AAPL", date(2026, 5, 1), date(2026, 5, 30))
    assert yf.called
    assert not df.empty


def test_yfinance_fail_fdr_success():
    with (
        patch("src.collectors.us._yf_ohlcv", side_effect=RuntimeError("yf down")),
        patch("src.collectors.us._fdr_ohlcv", return_value=_sample_df()) as fdr,
    ):
        c = USCollector()
        df = c.fetch_ohlcv("AAPL", date(2026, 5, 1), date(2026, 5, 30))
    assert fdr.called
    assert not df.empty


def test_all_fail_raises():
    with (
        patch("src.collectors.us._yf_ohlcv", side_effect=RuntimeError("yf")),
        patch("src.collectors.us._fdr_ohlcv", side_effect=RuntimeError("fdr")),
    ):
        c = USCollector()
        with pytest.raises(RuntimeError, match="모든 US"):
            c.fetch_ohlcv("AAPL", date(2026, 5, 1), date(2026, 5, 30))


def test_all_fail_returns_cache():
    """직전 캐시가 있으면 fallback."""
    from src.collectors.cache import cache_ohlcv
    cache_ohlcv("AAPL", _sample_df())
    with (
        patch("src.collectors.us._yf_ohlcv", side_effect=RuntimeError("yf")),
        patch("src.collectors.us._fdr_ohlcv", side_effect=RuntimeError("fdr")),
    ):
        c = USCollector()
        df = c.fetch_ohlcv("AAPL", date(2026, 5, 26), date(2026, 5, 27))
    assert not df.empty
