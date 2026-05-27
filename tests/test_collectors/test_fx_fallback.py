"""환율 다중 소스 폴백 (네트워크 mock)."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from src.collectors.fx import fetch_fx_today
from src.storage import apply_migrations


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "fx.db"
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.delenv("USE_MOCK", raising=False)
    monkeypatch.delenv("FX_FORCE_MOCK", raising=False)
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def test_primary_success():
    with patch("src.collectors.fx._fetch_exchangerate_host", return_value=Decimal("1380")):
        r = fetch_fx_today()
    assert r == Decimal("1380")


def test_primary_fail_fallback_success():
    with (
        patch("src.collectors.fx._fetch_exchangerate_host", side_effect=Exception("down")),
        patch("src.collectors.fx._fetch_er_api", return_value=Decimal("1390")),
    ):
        r = fetch_fx_today()
    assert r == Decimal("1390")


def test_all_fail_returns_cached(monkeypatch):
    from src.collectors.cache import cache_fx
    cache_fx(date(2026, 5, 1), Decimal("1370"))
    with (
        patch("src.collectors.fx._fetch_exchangerate_host", side_effect=Exception("down")),
        patch("src.collectors.fx._fetch_er_api", side_effect=Exception("down")),
    ):
        r = fetch_fx_today()
    assert r == Decimal("1370")


def test_all_fail_no_cache_returns_mock():
    with (
        patch("src.collectors.fx._fetch_exchangerate_host", side_effect=Exception("down")),
        patch("src.collectors.fx._fetch_er_api", side_effect=Exception("down")),
    ):
        r = fetch_fx_today()
    assert r == Decimal("1350")
