"""LLM 보조 — Gemini 우선, Groq 폴백, 둘 다 미설정이면 graceful skip."""
from __future__ import annotations

import os

from src.llm.base import BaseLLM


def get_llm() -> BaseLLM | None:
    """환경변수 기반으로 사용 가능한 LLM 반환. 없으면 None."""
    if os.environ.get("GEMINI_API_KEY"):
        try:
            from src.llm.gemini import GeminiLLM
            return GeminiLLM()
        except Exception:
            pass
    if os.environ.get("GROQ_API_KEY"):
        try:
            from src.llm.groq import GroqLLM
            return GroqLLM()
        except Exception:
            pass
    return None


def is_available() -> bool:
    return get_llm() is not None


def generate_signal_comment(symbol: str, name_kr: str, action: str, score: int,
                            components: dict) -> str | None:
    """시그널 결과에 대한 2-3 문장 한국어 요약."""
    llm = get_llm()
    if llm is None:
        return None
    reasons = "; ".join(
        f"{n}({c['score']:+d})" for n, c in components.items() if c.get("score") != 0
    ) or "전 항목 중립"
    prompt = (
        f"종목 {name_kr}({symbol}) 의 기술적 시그널 결과:\n"
        f"- 액션: {action}\n"
        f"- 합산 점수: {score:+d}\n"
        f"- 활성 컴포넌트: {reasons}\n\n"
        f"개인 투자자에게 위 시그널의 의미를 한국어 2-3 문장으로 객관적으로 설명하세요. "
        f"매수/매도 권유 표현은 피하고, 가능성과 리스크를 균형있게 다뤄주세요. "
        f"끝에 면책은 추가하지 마세요."
    )
    try:
        return llm.generate(prompt, max_tokens=300).strip()
    except Exception:
        return None


def score_news_sentiment(
    name_kr: str,
    symbol: str,
    headlines: list[dict],
) -> tuple[int, str] | None:
    """뉴스 헤드라인을 LLM 으로 -2 ~ +2 점수화. 호재면 +, 악재면 -.

    반환: (score, one-line-reason) 또는 None.
    """
    llm = get_llm()
    if llm is None or not headlines:
        return None
    bullets = "\n".join(
        f"- {h['title']} ({h.get('source','')})" for h in headlines[:5]
    )
    prompt = (
        f"종목: {name_kr}({symbol})\n"
        f"오늘자 한국 뉴스 헤드라인 5개:\n{bullets}\n\n"
        "위 뉴스가 단기 주가에 미치는 영향을 -2~+2 정수로 평가하세요.\n"
        "  +2: 강한 호재 (실적 호조, 대형 수주, 신사업)\n"
        "  +1: 약한 호재\n"
        "   0: 중립 또는 정보 부족\n"
        "  -1: 약한 악재\n"
        "  -2: 강한 악재 (실적 부진, 리콜, 제재)\n\n"
        "반드시 '점수: <정수>\\n사유: <한 문장>' 형식만 출력. 다른 텍스트 금지."
    )
    try:
        out = llm.generate(prompt, max_tokens=80).strip()
    except Exception:
        return None
    score, reason = 0, ""
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("점수"):
            digits = "".join(c for c in line if c in "+-0123456789")
            try:
                score = max(-2, min(2, int(digits)))
            except ValueError:
                score = 0
        elif line.startswith("사유"):
            reason = line.split(":", 1)[-1].strip()
    return score, reason or out[:80]


def analyze_news_for_stock(
    name_kr: str,
    symbol: str,
    action: str,
    score: int,
    headlines: list[dict],
) -> str | None:
    """뉴스 헤드라인 + 기술적 시그널을 종합해 2-3 문장 한국어 평가.

    headlines: [{"title", "link", "published", "source"}]
    """
    llm = get_llm()
    if llm is None or not headlines:
        return None
    bullets = "\n".join(
        f"- {h['title']} ({h.get('source','')})" for h in headlines[:5]
    )
    prompt = (
        f"종목 {name_kr}({symbol}) 의 오늘자 상황:\n"
        f"- 기술적 시그널: {action} (점수 {score:+d})\n"
        f"- 최근 뉴스 헤드라인:\n{bullets}\n\n"
        "위 뉴스가 기술적 시그널과 일치하는지, 단기적으로 호재/악재 요인은 무엇인지 "
        "한국어 2-3 문장으로 객관적으로 정리해 주세요. "
        "투자 권유 표현은 피하고, 가능성과 리스크를 균형있게 다루세요. "
        "면책 문구는 생략."
    )
    try:
        return llm.generate(prompt, max_tokens=320).strip()
    except Exception:
        return None


__all__ = [
    "BaseLLM", "get_llm", "is_available",
    "generate_signal_comment", "analyze_news_for_stock", "score_news_sentiment",
]
