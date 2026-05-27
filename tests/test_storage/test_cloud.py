"""클라우드 DB 상태 검출."""
from src.storage.cloud import _extract_host, get_status, is_turso_configured


def test_not_configured(monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    assert not is_turso_configured()


def test_partial_config_returns_false(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://x.turso.io")
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    assert not is_turso_configured()


def test_full_config(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://x.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "tok")
    assert is_turso_configured()


def test_status_structure():
    s = get_status()
    assert set(s.keys()) == {"configured", "library_available", "active", "url_host"}


def test_extract_host():
    assert _extract_host("libsql://swing-abc.turso.io") == "swing-abc.turso.io"
    assert _extract_host("libsql://swing.io/db") == "swing.io"
    assert _extract_host("") == ""
