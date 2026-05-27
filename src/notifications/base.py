"""알림 인터페이스 (Phase 6 활성)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    @abstractmethod
    def send(self, body: str) -> bool:
        ...


class TelegramNotifier(BaseNotifier):
    def send(self, body: str) -> bool:
        raise NotImplementedError("Phase 6 에서 구현됩니다.")
