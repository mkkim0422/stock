"""prices/fx_cache 캐시 라운드트립 검증."""
from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from src.collectors.cache import (
    cache_fx,
    cache_ohlcv,
    read_cached_fx,
    read_cached_ohlcv,
    read_latest_cached_fx,
)
from src.storage import apply_migrations


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "cache.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def test_ohlcv_round_trip():
    idx = pd.to_datetime(["2026-01-02", "2026-01-03"]).date
    df = pd.DataFrame({
        "open": [100.0, 101.0],
        "high": [102.0, 103.0],
        "low":  [99.0, 100.0],
        "close": [101.5, 102.5],
        "volume": [1000, 2000],
    }, index=idx)
    n = cache_ohlcv("AAPL", df)
    assert n == 2
    back = read_cached_ohlcv("AAPL", date(2026, 1, 1), date(2026, 1, 5))
    assert len(back) == 2
    assert back.iloc[0]["close"] == 101.5
    assert int(back.iloc[1]["volume"]) == 2000


def test_ohlcv_upsert_idempotent():
    idx = pd.to_datetime(["2026-01-02"]).date
    df = pd.DataFrame({
        "open": [100.0], "high": [110.0], "low": [99.0],
        "close": [104.0], "volume": [500],
    }, index=idx)
    cache_ohlcv("MSFT", df)
    df2 = df.copy()
    df2["close"] = [108.0]   # high=110 이상으로 유지
    cache_ohlcv("MSFT", df2)
    back = read_cached_ohlcv("MSFT", date(2026, 1, 1), date(2026, 1, 5))
    assert back.iloc[0]["close"] == 108.0


def test_fx_round_trip():
    cache_fx(date(2026, 5, 28), Decimal("1340.12"))
    got = read_cached_fx(date(2026, 5, 28))
    assert got == Decimal("1340.12")
    latest = read_latest_cached_fx()
    assert latest == Decimal("1340.12")


def test_fx_overwrite():
    cache_fx(date(2026, 5, 28), Decimal("1340"))
    cache_fx(date(2026, 5, 28), Decimal("1360"))
    assert read_cached_fx(date(2026, 5, 28)) == Decimal("1360")
