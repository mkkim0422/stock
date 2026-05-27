from datetime import date

import pytest

from src.collectors.mock import MockCollector


@pytest.fixture
def coll():
    return MockCollector()


def test_fetch_realtime_kr(coll):
    p = coll.fetch_realtime("005930")
    assert p > 0


def test_fetch_realtime_us(coll):
    p = coll.fetch_realtime("AAPL")
    assert p > 0


def test_fetch_ohlcv_kr(coll):
    df = coll.fetch_ohlcv("005930", date(2025, 5, 27), date(2026, 5, 27))
    assert not df.empty
    assert set(df.columns) >= {"open", "high", "low", "close", "volume"}


def test_fetch_unknown_raises(coll):
    with pytest.raises(ValueError):
        coll.fetch_realtime("XXXXX1")
