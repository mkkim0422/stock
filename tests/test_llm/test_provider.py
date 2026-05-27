"""LLM provider selection + graceful skip."""
from unittest.mock import patch

from src.llm import generate_signal_comment, get_llm, is_available


def test_no_keys_returns_none(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert get_llm() is None
    assert not is_available()


def test_gemini_selected_first(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g_key")
    monkeypatch.setenv("GROQ_API_KEY", "q_key")
    llm = get_llm()
    assert llm is not None
    assert "gemini" in llm.name.lower()


def test_groq_fallback_when_no_gemini(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "q_key")
    llm = get_llm()
    assert llm is not None
    assert "llama" in llm.name.lower()


def test_signal_comment_uses_llm(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g_key")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with patch("src.llm.gemini.GeminiLLM.generate", return_value="테스트 코멘트"):
        out = generate_signal_comment(
            "005930", "삼성전자", "BUY", 9,
            {"RSI": {"score": 2, "reason": "과매도"}},
        )
    assert out == "테스트 코멘트"


def test_signal_comment_none_when_no_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    out = generate_signal_comment(
        "005930", "삼성전자", "BUY", 9, {},
    )
    assert out is None
