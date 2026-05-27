"""통합 시나리오 5개 — 매매 흐름 E2E."""
from decimal import Decimal

import pytest

from src.paper.corporate_actions import apply_stock_split
from src.paper.portfolio import get_cash, get_position, reset_portfolio, upsert_position
from src.paper.trader import execute_order
from src.storage import apply_migrations


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "int.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    apply_migrations()
    reset_portfolio()
    yield
    get_settings.cache_clear()


def test_scenario_1_buy_sell_realized_pnl():
    """시나리오 1: 매수 → 매도 → 실현손익 확인."""
    execute_order("005930", "BUY", 10, Decimal("70000"))
    r = execute_order("005930", "SELL", 10, Decimal("80000"))
    assert r["realized_pnl"] is not None
    # 매수 fill = 70000*1.0007 = 70049
    # 매도 fill = 80000*0.9993 = 79944
    # 매수 수수료 = 10*70049*0.00015 = 105.07
    # 매도 수수료 = 10*79944*0.00015 = 119.92
    # 거래세 = 10*79944*0.0018 = 1438.99
    # realized = (79944-70049)*10 - 119.92 - 1438.99 = 98950 - 1558.91 ≈ 97391
    assert float(r["realized_pnl"]) > 0
    pos = get_position("005930")
    assert pos is None or pos[0] == 0


def test_scenario_2_avg_cost_after_split_buys():
    """시나리오 2: 분할매수 → 가중평균 평단가."""
    execute_order("005930", "BUY", 10, Decimal("70000"))
    execute_order("005930", "BUY", 30, Decimal("80000"))
    pos = get_position("005930")
    assert pos is not None
    qty, avg = pos
    assert qty == 40
    # 평단 = (10 * 70000*1.0007 + 30 * 80000*1.0007) / 40
    # = 10*70049 + 30*80056 = 700490 + 2401680 = 3102170 → /40 = 77554.25
    assert avg == pytest.approx(Decimal("77554.25"), rel=Decimal("0.001"))


def test_scenario_3_usd_buy_with_fx():
    """시나리오 3: 미국 종목 매수 — USD 잔고 차감."""
    cash_before_usd = get_cash()[1]
    execute_order("AAPL", "BUY", 5, Decimal("200"))
    cash_after_usd = get_cash()[1]
    # 5*200*1.0007 = 1000.7 USD (수수료 0)
    spent = cash_before_usd - cash_after_usd
    assert spent == pytest.approx(Decimal("1000.7"), rel=Decimal("0.001"))


def test_scenario_4_kr_tax_020():
    """시나리오 4: 매도 거래세 0.20% 적용 (2026-01-01 시행)."""
    execute_order("005930", "BUY", 10, Decimal("70000"))
    r = execute_order("005930", "SELL", 10, Decimal("70000"))
    # 매도 거래대금 = 10 * 70000 * 0.9993 = 699510
    # 거래세 = 699510 * 0.0020 = 1399.02
    assert float(r["tax"]) == pytest.approx(1399.02, rel=0.001)


def test_scenario_5_stock_split_5_to_1():
    """시나리오 5: 5:1 액면분할 → 50주→250주, 평단 1/5."""
    qty_before = 50
    avg_before = Decimal("100000")
    qty_after, avg_after = apply_stock_split(qty_before, avg_before, 5, 1)
    assert qty_after == 250
    assert avg_after == Decimal("20000")

    upsert_position("005930", "KR", qty_before, avg_before)
    new_q, new_p = apply_stock_split(qty_before, avg_before, 5, 1)
    upsert_position("005930", "KR", new_q, new_p)
    p = get_position("005930")
    assert p is not None
    assert p[0] == 250
    assert p[1] == Decimal("20000")
