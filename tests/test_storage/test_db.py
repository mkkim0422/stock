
import pytest

from src.storage import apply_migrations, connect


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]


def test_apply_migrations_creates_tables():
    applied = apply_migrations()
    assert "0001_initial.sql" in applied
    with connect() as conn:
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    expected = {
        "symbols", "prices", "trades", "positions",
        "portfolio_snapshots", "fx_cache", "signals",
        "briefings", "account_cash",
    }
    assert expected.issubset(set(names))


def test_wal_mode():
    apply_migrations()
    with connect() as conn:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"


def test_idempotent_migration():
    apply_migrations()
    apply_migrations()
    with connect() as conn:
        n = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    assert n >= 9
