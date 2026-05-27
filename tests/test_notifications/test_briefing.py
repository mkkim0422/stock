"""브리핑 생성 + DB 기록."""
import pytest

from src.notifications.briefing import (
    compose_briefing,
    persist_briefing,
    send_briefing,
)
from src.storage import apply_migrations, connect


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "brf.db"
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.setenv("USE_MOCK", "1")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    from src.config.settings import get_settings
    get_settings.cache_clear()
    from src.storage import db as _db
    _db._applied_for_path.clear()
    apply_migrations()
    yield
    get_settings.cache_clear()
    _db._applied_for_path.clear()


def test_compose_has_required_sections():
    body = compose_briefing("test-slot")
    assert "swing-advisor" in body
    assert "평가액" in body
    assert "페이퍼" in body  # 면책 단어


def test_persist_returns_id():
    body = compose_briefing("test")
    rid = persist_briefing("test", body)
    assert rid > 0
    with connect() as conn:
        row = conn.execute("SELECT slot, body FROM briefings WHERE id=?",
                           (rid,)).fetchone()
    assert row["slot"] == "test"
    assert "swing-advisor" in row["body"]


def test_send_briefing_skipped_when_no_telegram():
    r = send_briefing("09:30")
    assert "skipped" in r["status"]
    assert r["ok"] is False
