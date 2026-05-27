"""daily_pnl_krw 가 전일 스냅샷 대비 차분으로 계산되는지."""
from decimal import Decimal

import pytest

from src.paper.performance import snapshot_today
from src.storage import apply_migrations, connect


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "pnl.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def test_first_snapshot_zero_pnl():
    snapshot_today()
    with connect() as conn:
        row = conn.execute(
            "SELECT daily_pnl_krw FROM portfolio_snapshots ORDER BY date DESC LIMIT 1"
        ).fetchone()
    assert row["daily_pnl_krw"] == Decimal(0)


def test_second_snapshot_uses_diff():
    # 어제 스냅샷 수동 삽입
    yesterday = "2026-05-26"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO portfolio_snapshots
            (date, cash_krw, cash_usd, fx_rate, positions_value_krw,
             total_value_krw, daily_pnl_krw)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (yesterday, Decimal("10000000"), Decimal("10000"),
             Decimal("1350"), Decimal("0"),
             Decimal("20000000"), Decimal("0")),
        )
    snapshot_today()
    with connect() as conn:
        row = conn.execute(
            "SELECT total_value_krw, daily_pnl_krw FROM portfolio_snapshots "
            "WHERE date != ? ORDER BY date DESC LIMIT 1",
            (yesterday,),
        ).fetchone()
    expected_diff = row["total_value_krw"] - Decimal("20000000")
    assert row["daily_pnl_krw"] == expected_diff
