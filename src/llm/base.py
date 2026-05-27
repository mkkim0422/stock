"""LLM 인터페이스. 구현체: GeminiLLM, GroqLLM."""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    name: str = "base"

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        ...
