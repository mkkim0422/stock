"""종목 자동 갱신 (3시간 간격) 로직 검증."""
from datetime import UTC, datetime, timedelta

import pytest

from src.storage import apply_migrations
from src.symbols.refresh import (
    get_last_refresh,
    set_last_refresh,
    should_refresh,
)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "ref.db"
    monkeypatch.setenv("DB_PATH", str(db))
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def test_should_refresh_when_never():
    assert should_refresh()


def test_set_and_get():
    ts = datetime(2026, 5, 28, 12, 0, tzinfo=UTC)
    set_last_refresh(ts)
    got = get_last_refresh()
    assert got.isoformat() == ts.isoformat()


def test_not_refresh_within_3_hours():
    now = datetime(2026, 5, 28, 12, 0, tzinfo=UTC)
    set_last_refresh(now - timedelta(hours=2))
    assert not should_refresh(now)


def test_refresh_after_3_hours():
    now = datetime(2026, 5, 28, 12, 0, tzinfo=UTC)
    set_last_refresh(now - timedelta(hours=4))
    assert should_refresh(now)


def test_exactly_3h_triggers():
    now = datetime(2026, 5, 28, 12, 0, tzinfo=UTC)
    set_last_refresh(now - timedelta(hours=3))
    assert should_refresh(now)
