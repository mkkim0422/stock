"""LLM 인터페이스 (Phase 5 활성). Gemini Flash / Groq Llama."""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        ...


class GeminiLLM(BaseLLM):
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        raise NotImplementedError("Phase 5 에서 구현됩니다.")


class GroqLLM(BaseLLM):
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        raise NotImplementedError("Phase 5 에서 구현됩니다.")
