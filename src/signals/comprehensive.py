"""종합 점수 — 기술 + 펀더멘털 + 거시·섹터 + 뉴스 센티먼트.

기존 기술 점수(±11)에 다음을 더해 ±21 범위로 확장:
- 펀더멘털 ±5: PER 저평가/적자, PBR <1 / >3, ROE proxy(EPS 양수), 시총 안정
- 거시·섹터 ±3: KOSPI 추세, 섹터 ETF 추세, USD/KRW (수출주 보너스)
- 센티먼트 ±2: LLM 뉴스 분류 (호재/악재/중립)

새 임계값 (composite):
  STRONG_BUY  ≥ +14
  BUY         ≥ +10
  HOLD        그 외
  SELL        ≤ -5
  STRONG_SELL ≤ -10

이 엔진은 기존 기술 엔진(src/signals/engine.py)을 대체하지 않고 보조한다.
DB 저장은 기술 점수만 (호환). composite 는 화면 표시용.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from src.collectors.fundamentals import Fundamental, industry_median_per
from src.collectors.macro import context_snapshot, sector_etf_return
from src.signals.base import SignalOutput

CompositeAction = Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]


@dataclass(slots=True)
class CompositeScore:
    technical: int = 0
    fundamental: int = 0
    macro: int = 0
    sentiment: int = 0
    total: int = 0
    action: CompositeAction = "HOLD"
    breakdown: dict[str, list[dict]] = field(default_factory=dict)  # 카테고리별 항목


def _decide(total: int) -> CompositeAction:
    if total >= 14:
        return "STRONG_BUY"
    if total >= 10:
        return "BUY"
    if total <= -10:
        return "STRONG_SELL"
    if total <= -5:
        return "SELL"
    return "HOLD"


# ─── 펀더멘털 ──────────────────────────────────────────
def score_fundamental(fund: Fundamental | None) -> tuple[int, list[dict]]:
    """펀더멘털 점수 ±5 + 항목 breakdown."""
    if not fund:
        return 0, [{"name": "펀더멘털", "score": 0, "reason": "데이터 없음"}]

    items: list[dict] = []
    total = 0

    per = fund.get("per")
    pbr = fund.get("pbr")
    eps = fund.get("eps")
    cap = fund.get("market_cap") or 0
    industry = fund.get("industry") or fund.get("sector") or ""

    # PER 평가
    if per is None or per <= 0:
        if eps is not None and eps < 0:
            items.append({"name": "PER", "score": -2, "reason": "적자 (EPS<0)"})
            total -= 2
        else:
            items.append({"name": "PER", "score": 0, "reason": "PER 불명"})
    else:
        med = industry_median_per(industry) if industry else None
        if med:
            if per <= med * 0.7:
                items.append({"name": "PER", "score": 2, "reason": f"PER {per:.1f} (업종 중앙값 {med:.1f} 대비 30%↓ 저평가)"})
                total += 2
            elif per >= med * 1.5:
                items.append({"name": "PER", "score": -1, "reason": f"PER {per:.1f} (업종 중앙값 {med:.1f} 대비 50%↑ 고평가)"})
                total -= 1
            else:
                items.append({"name": "PER", "score": 0, "reason": f"PER {per:.1f} (업종 평균 수준)"})
        else:
            # 업종 비교 불가 → 절대값 기준 fallback
            if per <= 10:
                items.append({"name": "PER", "score": 1, "reason": f"PER {per:.1f} (저평가 구간)"})
                total += 1
            elif per >= 30:
                items.append({"name": "PER", "score": -1, "reason": f"PER {per:.1f} (고평가 구간)"})
                total -= 1
            else:
                items.append({"name": "PER", "score": 0, "reason": f"PER {per:.1f}"})

    # PBR 평가
    if pbr is None or pbr <= 0:
        items.append({"name": "PBR", "score": 0, "reason": "PBR 불명"})
    elif pbr < 1.0:
        items.append({"name": "PBR", "score": 1, "reason": f"PBR {pbr:.2f} (<1, 자산가치 미만)"})
        total += 1
    elif pbr > 3.0:
        items.append({"name": "PBR", "score": -1, "reason": f"PBR {pbr:.2f} (>3, 자산가치 대비 고평가)"})
        total -= 1
    else:
        items.append({"name": "PBR", "score": 0, "reason": f"PBR {pbr:.2f}"})

    # 시가총액 안정성
    if cap >= 5e12:  # 5조 이상 — 대형주
        items.append({"name": "시총", "score": 1, "reason": f"시가총액 {cap/1e12:.1f}조 (대형주 안정)"})
        total += 1
    elif cap >= 5e11:  # 5천억 이상 — 중형주
        items.append({"name": "시총", "score": 0, "reason": f"시가총액 {cap/1e8:,.0f}억 (중형주)"})
    elif cap > 0:
        items.append({"name": "시총", "score": -1, "reason": f"시가총액 {cap/1e8:,.0f}억 (소형주, 변동성↑)"})
        total -= 1

    # 배당
    dy = fund.get("dividend_yield")
    if dy and dy >= 3.0:
        items.append({"name": "배당", "score": 1, "reason": f"배당수익률 {dy:.1f}% (3%↑)"})
        total += 1

    # ±5 캡
    total = max(-5, min(5, total))
    return total, items


# ─── 거시·섹터 ─────────────────────────────────────────
def score_macro(fund: Fundamental | None) -> tuple[int, list[dict]]:
    items: list[dict] = []
    total = 0

    ctx = context_snapshot()
    kospi_ret = ctx.get("KOSPI", {}).get("ret_5d")
    if kospi_ret is not None:
        if kospi_ret >= 2.0:
            items.append({"name": "KOSPI", "score": 1, "reason": f"KOSPI 5일 {kospi_ret:+.1f}% (강세)"})
            total += 1
        elif kospi_ret <= -2.0:
            items.append({"name": "KOSPI", "score": -1, "reason": f"KOSPI 5일 {kospi_ret:+.1f}% (약세)"})
            total -= 1
        else:
            items.append({"name": "KOSPI", "score": 0, "reason": f"KOSPI 5일 {kospi_ret:+.1f}%"})

    # 섹터 ETF
    if fund and (fund.get("industry") or fund.get("sector")):
        key = fund.get("industry") or fund.get("sector") or ""
        sec_ret = sector_etf_return(key, days=5)
        if sec_ret is not None:
            if sec_ret >= 3.0:
                items.append({"name": "섹터", "score": 1, "reason": f"{key} ETF 5일 {sec_ret:+.1f}% (테마 강세)"})
                total += 1
            elif sec_ret <= -3.0:
                items.append({"name": "섹터", "score": -1, "reason": f"{key} ETF 5일 {sec_ret:+.1f}% (테마 약세)"})
                total -= 1
            else:
                items.append({"name": "섹터", "score": 0, "reason": f"{key} ETF 5일 {sec_ret:+.1f}%"})

    # USD/KRW (수출주 가산)
    fx_ret = ctx.get("USDKRW", {}).get("ret_5d")
    if fx_ret is not None and fund:
        industry = (fund.get("industry") or "").lower()
        export_sensitive = any(
            k in industry for k in ("반도체", "자동차", "조선", "철강", "화학", "디스플레이")
        )
        if export_sensitive:
            if fx_ret >= 1.0:
                items.append({"name": "환율", "score": 1, "reason": f"USD/KRW 5일 +{fx_ret:.1f}% (수출주 호재)"})
                total += 1
            elif fx_ret <= -1.0:
                items.append({"name": "환율", "score": -1, "reason": f"USD/KRW 5일 {fx_ret:.1f}% (수출주 부담)"})
                total -= 1

    total = max(-3, min(3, total))
    return total, items


# ─── 종합 평가 ─────────────────────────────────────────
def evaluate_composite(
    symbol: str,
    technical: SignalOutput,
    fundamental: Fundamental | None,
    sentiment_score: int = 0,
    sentiment_reason: str = "",
) -> CompositeScore:
    """기존 기술 시그널에 펀더멘털·거시·센티먼트를 더해 composite."""
    fund_score, fund_items = score_fundamental(fundamental)
    macro_score, macro_items = score_macro(fundamental)
    tech_items = [
        {"name": n, "score": c["score"], "reason": c["reason"]}
        for n, c in technical.components.items()
    ]
    sent_items = (
        [{"name": "뉴스 센티먼트", "score": sentiment_score, "reason": sentiment_reason or "—"}]
        if sentiment_reason else []
    )

    sentiment_score = max(-2, min(2, sentiment_score))
    total = technical.score + fund_score + macro_score + sentiment_score
    return CompositeScore(
        technical=technical.score,
        fundamental=fund_score,
        macro=macro_score,
        sentiment=sentiment_score,
        total=total,
        action=_decide(total),
        breakdown={
            "기술 분석": tech_items,
            "펀더멘털": fund_items,
            "거시·섹터": macro_items,
            "뉴스 센티먼트": sent_items,
        },
    )
