"""Groq (Llama) OpenAI 호환 REST 호출."""
from __future__ import annotations

import os

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.llm.base import BaseLLM

_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "llama-3.1-8b-instant"


class GroqLLM(BaseLLM):
    name = _MODEL

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY 미설정")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        body = {
            "model": _MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": max_tokens,
        }
        r = httpx.post(
            _ENDPOINT,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=body,
            timeout=15.0,
        )
        r.raise_for_status()
        js = r.json()
        try:
            return js["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Groq 응답 형식 이상: {js}") from e
