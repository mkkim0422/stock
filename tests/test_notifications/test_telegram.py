"""Telegram notifier configuration + send."""
from unittest.mock import MagicMock, patch

from src.notifications.telegram import is_telegram_configured, send_message


def test_not_configured(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert not is_telegram_configured()
    assert not send_message("test")


def test_partial_config_returns_false(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:xyz")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert not is_telegram_configured()


def test_send_when_configured(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:xyz")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    mock_resp = MagicMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json = lambda: {"ok": True}
    with patch("httpx.post", return_value=mock_resp) as mp:
        ok = send_message("hello")
    assert ok
    assert mp.called


def test_long_message_truncated(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:xyz")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    mock_resp = MagicMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json = lambda: {"ok": True}
    long_body = "x" * 5000
    with patch("httpx.post", return_value=mock_resp) as mp:
        send_message(long_body)
    sent_body = mp.call_args.kwargs["json"]["text"]
    assert len(sent_body) <= 4096
