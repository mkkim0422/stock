"""시그널 인터페이스 (Phase 3 활성).

가중치 +8 매수 / -3 매도 (docs/SIGNALS.md).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(slots=True)
class SignalOutput:
    ts: datetime
    symbol: str
    score: int
    components: dict
    action: Literal["BUY", "SELL", "HOLD"]


class BaseSignal(ABC):
    @abstractmethod
    def evaluate(self, symbol: str, as_of: datetime) -> SignalOutput:
        ...


def combine(*args, **kwargs):
    """Phase 3 활성: 가중치 합산 → action."""
    raise NotImplementedError("Phase 3 에서 구현됩니다.")
