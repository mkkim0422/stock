"""DB Decimal 어댑터/컨버터 확인 + 정밀도 손실 없음."""
from decimal import Decimal

import pytest

from src.storage import apply_migrations, connect


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "dec.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def test_decimal_round_trip():
    with connect() as conn:
        conn.execute(
            "INSERT INTO account_cash (id, cash_krw, cash_usd) VALUES (1, ?, ?)",
            (Decimal("12345678.123456789"), Decimal("0.000000001")),
        )
        row = conn.execute("SELECT cash_krw, cash_usd FROM account_cash WHERE id=1").fetchone()
    assert row["cash_krw"] == Decimal("12345678.123456789")
    assert row["cash_usd"] == Decimal("0.000000001")


def test_decimal_arithmetic_accumulation():
    """1000회 누적 합산이 Decimal 정밀도 유지 (float이면 누적 오차 발생)."""
    with connect() as conn:
        conn.execute(
            "INSERT INTO account_cash (id, cash_krw, cash_usd) VALUES (1, ?, ?)",
            (Decimal("0"), Decimal("0")),
        )
        inc = Decimal("0.0001")
        for _ in range(1000):
            row = conn.execute(
                "SELECT cash_krw FROM account_cash WHERE id=1"
            ).fetchone()
            new_v = row["cash_krw"] + inc
            conn.execute(
                "UPDATE account_cash SET cash_krw=? WHERE id=1", (new_v,)
            )
        final = conn.execute(
            "SELECT cash_krw FROM account_cash WHERE id=1"
        ).fetchone()["cash_krw"]
    assert final == Decimal("0.1000")


def test_trades_decimal_columns():
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO trades
            (ts, symbol, market, side, qty, fill_price, fee_amt, tax_amt,
             cash_delta_krw, cash_delta_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("2026-05-28T00:00:00", "005930", "KR", "BUY", 10,
             Decimal("70049.0"), Decimal("105.0735"), Decimal("0"),
             Decimal("-700595.0735"), Decimal("0")),
        )
        row = conn.execute(
            "SELECT fill_price, fee_amt, cash_delta_krw FROM trades"
        ).fetchone()
    assert row["fill_price"] == Decimal("70049.0")
    assert row["fee_amt"] == Decimal("105.0735")
    assert row["cash_delta_krw"] == Decimal("-700595.0735")
