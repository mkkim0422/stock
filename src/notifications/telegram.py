"""텔레그램 봇 알림 (Bot API HTTP)."""
from __future__ import annotations

import os

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.notifications.base import BaseNotifier
from src.utils.logger import get_logger

_log = get_logger("notifications.telegram")
_API = "https://api.telegram.org/bot{token}/sendMessage"
_MAX_LEN = 4096


class TelegramNotifier(BaseNotifier):
    name = "telegram"

    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        if not self.token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 미설정")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    def send(self, body: str) -> bool:
        if len(body) > _MAX_LEN:
            body = body[: _MAX_LEN - 20] + "\n…(잘림)"
        r = httpx.post(
            _API.format(token=self.token),
            json={
                "chat_id": self.chat_id,
                "text": body,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10.0,
        )
        r.raise_for_status()
        js = r.json()
        if not js.get("ok"):
            _log.warning("telegram error: %s", js)
            return False
        return True


def is_telegram_configured() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN")) and bool(
        os.environ.get("TELEGRAM_CHAT_ID")
    )


def send_message(body: str) -> bool:
    """편의 함수: 설정 시 전송, 미설정 시 False."""
    if not is_telegram_configured():
        return False
    try:
        return TelegramNotifier().send(body)
    except Exception as e:
        _log.warning("telegram send failed: %s", e)
        return False
