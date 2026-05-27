from datetime import datetime
from decimal import Decimal

import pytest

from src.paper.portfolio import get_cash, get_position, reset_portfolio
from src.paper.trader import execute_order
from src.storage import apply_migrations
from src.utils.timezone import KST

OPEN_KR = datetime(2026, 5, 28, 10, 30, tzinfo=KST)  # 평일 장중
OPEN_US_KST = datetime(2026, 5, 28, 23, 30, tzinfo=KST)  # 평일 미국장 개장 KST


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "trader_test.db"
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


def test_buy_kr():
    r = execute_order("005930", "BUY", 10, Decimal("70000"), ts=OPEN_KR)
    cash_krw, _ = get_cash()
    pos = get_position("005930")
    assert pos is not None
    qty, avg = pos
    assert qty == 10
    assert cash_krw < Decimal("10_000_000")
    assert r["fee"] > 0


def test_sell_partial_kr():
    execute_order("005930", "BUY", 10, Decimal("70000"), ts=OPEN_KR)
    r = execute_order("005930", "SELL", 5, Decimal("75000"), ts=OPEN_KR)
    pos = get_position("005930")
    assert pos is not None
    qty, _ = pos
    assert qty == 5
    assert r["realized_pnl"] is not None
    assert r["tax"] > 0


def test_average_cost():
    execute_order("005930", "BUY", 10, Decimal("70000"), ts=OPEN_KR)
    execute_order("005930", "BUY", 10, Decimal("80000"), ts=OPEN_KR)
    pos = get_position("005930")
    assert pos is not None
    qty, avg = pos
    assert qty == 20
    assert avg == pytest.approx(Decimal("75052.5"), rel=Decimal("0.001"))


def test_buy_us():
    r = execute_order("AAPL", "BUY", 5, Decimal("200"), ts=OPEN_US_KST)
    _, cash_usd = get_cash()
    pos = get_position("AAPL")
    assert pos is not None
    assert pos[0] == 5
    assert cash_usd < Decimal("10000")
    assert r["fee"] == Decimal("0")


def test_insufficient_balance():
    with pytest.raises(ValueError, match="잔고 부족"):
        execute_order("005930", "BUY", 10_000, Decimal("70000"), ts=OPEN_KR)


def test_oversell():
    execute_order("005930", "BUY", 5, Decimal("70000"), ts=OPEN_KR)
    with pytest.raises(ValueError, match="보유 수량 부족"):
        execute_order("005930", "SELL", 10, Decimal("70000"), ts=OPEN_KR)
