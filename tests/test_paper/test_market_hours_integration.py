"""trader 가 시장 시간 외 주문을 다음 정규장 시가로 조정하는지."""
from datetime import datetime
from decimal import Decimal

import pytest

from src.paper.portfolio import reset_portfolio
from src.paper.trader import execute_order
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


def test_kr_order_during_open_keeps_ts():
    open_ts = datetime(2026, 5, 28, 10, 30, tzinfo=KST)
    r = execute_order("005930", "BUY", 1, Decimal("70000"), ts=open_ts)
    assert r["market_status_at_request"] == "OPEN"
    assert r["executed_ts"] == open_ts


def test_kr_order_after_close_adjusts_to_next_open():
    closed_ts = datetime(2026, 5, 28, 20, 0, tzinfo=KST)
    r = execute_order("005930", "BUY", 1, Decimal("70000"), ts=closed_ts)
    assert r["market_status_at_request"] == "AFTER_CLOSE"
    # 다음 거래일 (5/29 금) 09:00 KST
    assert r["executed_ts"].hour == 9
    assert r["executed_ts"].date().isoformat() == "2026-05-29"


def test_kr_weekend_adjusts_to_monday():
    sat = datetime(2026, 5, 30, 10, 0, tzinfo=KST)
    r = execute_order("005930", "BUY", 1, Decimal("70000"), ts=sat)
    assert r["market_status_at_request"] == "WEEKEND"
    assert r["executed_ts"].weekday() == 0  # 월요일
    assert r["executed_ts"].hour == 9


def test_kr_holiday_adjusts():
    holiday = datetime(2026, 1, 1, 10, 0, tzinfo=KST)
    r = execute_order("005930", "BUY", 1, Decimal("70000"), ts=holiday)
    assert r["market_status_at_request"] == "HOLIDAY"
    assert r["executed_ts"] > holiday


def test_respect_market_hours_false_disables_adjust():
    closed = datetime(2026, 5, 30, 12, 0, tzinfo=KST)  # 토요일
    r = execute_order(
        "005930", "BUY", 1, Decimal("70000"),
        ts=closed, respect_market_hours=False,
    )
    assert r["executed_ts"] == closed
    assert r["market_status_at_request"] is None
