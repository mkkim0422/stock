"""corporate_actions 의 trader/portfolio 통합 헬퍼 검증."""
from datetime import datetime
from decimal import Decimal

import pytest

from src.paper.corporate_actions import (
    apply_dividend_to_portfolio,
    apply_split_to_portfolio,
)
from src.paper.portfolio import get_cash, get_position, reset_portfolio
from src.paper.trader import execute_order
from src.storage import apply_migrations
from src.utils.timezone import KST

OPEN_KR = datetime(2026, 5, 28, 10, 30, tzinfo=KST)
OPEN_US_KST = datetime(2026, 5, 28, 23, 30, tzinfo=KST)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "ca.db"
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


def test_split_applies_to_existing_position():
    execute_order("005930", "BUY", 50, Decimal("100000"), ts=OPEN_KR)
    out = apply_split_to_portfolio("005930", 5, 1)
    assert out is not None
    new_qty, new_avg = out
    assert new_qty == 250
    pos = get_position("005930")
    assert pos[0] == 250
    assert pos[1] == pytest.approx(Decimal("20014"), rel=Decimal("0.0001"))


def test_split_no_position_returns_none():
    out = apply_split_to_portfolio("000660", 2, 1)
    assert out is None


def test_dividend_increases_cash_kr():
    execute_order("005930", "BUY", 100, Decimal("70000"), ts=OPEN_KR)
    cash_before = get_cash()[0]
    paid = apply_dividend_to_portfolio("005930", Decimal("500"))
    assert paid == Decimal("50000")
    cash_after = get_cash()[0]
    assert cash_after - cash_before == Decimal("50000")


def test_dividend_increases_cash_us():
    execute_order("AAPL", "BUY", 10, Decimal("200"), ts=OPEN_US_KST)
    _, usd_before = get_cash()
    paid = apply_dividend_to_portfolio("AAPL", Decimal("0.25"))
    assert paid == Decimal("2.50")
    _, usd_after = get_cash()
    assert usd_after - usd_before == Decimal("2.50")
