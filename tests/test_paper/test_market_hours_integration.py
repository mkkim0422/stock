"""trader 가 시장 시간 외 주문을 차단하는지 (실 증권사처럼)."""
from datetime import datetime
from decimal import Decimal

import pytest

from src.paper.portfolio import reset_portfolio
from src.paper.trader import MarketClosedError, execute_order
from src.storage import apply_migrations
from src.utils.timezone import KST


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "mh.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    reset_portfolio()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def test_kr_order_during_open_succeeds():
    open_ts = datetime(2026, 5, 28, 10, 30, tzinfo=KST)
    r = execute_order("005930", "BUY", 1, Decimal("70000"), ts=open_ts)
    assert r["market_status_at_request"] == "OPEN"
    assert r["executed_ts"] == open_ts


def test_kr_order_after_close_raises():
    closed_ts = datetime(2026, 5, 28, 20, 0, tzinfo=KST)
    with pytest.raises(MarketClosedError, match="AFTER_CLOSE"):
        execute_order("005930", "BUY", 1, Decimal("70000"), ts=closed_ts)


def test_kr_weekend_raises():
    sat = datetime(2026, 5, 30, 10, 0, tzinfo=KST)
    with pytest.raises(MarketClosedError, match="WEEKEND"):
        execute_order("005930", "BUY", 1, Decimal("70000"), ts=sat)


def test_kr_holiday_raises():
    holiday = datetime(2026, 1, 1, 10, 0, tzinfo=KST)
    with pytest.raises(MarketClosedError, match="HOLIDAY"):
        execute_order("005930", "BUY", 1, Decimal("70000"), ts=holiday)


def test_respect_market_hours_false_allows_anytime():
    """테스트/백테스트용. 기본 동작이 아님."""
    closed = datetime(2026, 5, 30, 12, 0, tzinfo=KST)  # 토요일
    r = execute_order(
        "005930", "BUY", 1, Decimal("70000"),
        ts=closed, respect_market_hours=False,
    )
    assert r["executed_ts"] == closed
    assert r["market_status_at_request"] is None
