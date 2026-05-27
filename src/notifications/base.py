"""알림 인터페이스."""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    name: str = "base"

    @abstractmethod
    def send(self, body: str) -> bool:
        ...
