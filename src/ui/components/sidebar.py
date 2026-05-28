"""사이드바 — 토스 스타일 자산 요약 (모든 페이지 동일)."""
from __future__ import annotations

import streamlit as st

from src.config import get_settings
from src.paper.performance import evaluate
from src.storage import apply_migrations
from src.ui.components.kpi_card import fmt_krw, fmt_pct, fmt_usd
from src.utils.market_hours import kr_status, status_label, us_status
from src.utils.timezone import now_kst


def _market_dot(status: str) -> str:
    s = status.lower()
    if "open" in s or "정규" in s or "장중" in s:
        return "🟢"
    if "pre" in s or "after" in s or "동시호가" in s:
        return "🟡"
    return "⚫"


def render_sidebar() -> None:
    apply_migrations()
    settings = get_settings()
    e = evaluate()
    now = now_kst()
    ret = float(e["cum_return_pct"])

    with st.sidebar:
        st.markdown(
            "<div style='padding:6px 4px 16px 4px;'>"
            "<div style='font-size:18px; font-weight:800; letter-spacing:-0.02em;'>📊 swing-advisor</div>"
            f"<div style='font-size:12px; color:#6B7684; margin-top:2px;'>모드: {settings.mode} · 페이퍼 전용</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        # 내 자산 카드
        ret_cls = "toss-up" if ret >= 0 else "toss-down"
        ret_sign = "+" if ret >= 0 else ""
        st.markdown(
            f"""
<div class="toss-card-tight">
  <p class="toss-label">내 평가 총액 (KRW 환산)</p>
  <p class="toss-value-md">{fmt_krw(float(e['total_value_krw']))}</p>
  <p class="toss-sub {ret_cls}">{ret_sign}{fmt_pct(ret)} (누적)</p>
</div>
""",
            unsafe_allow_html=True,
        )

        # 보유 현금
        st.markdown(
            f"""
<div class="toss-card-tight">
  <p class="toss-label">보유 현금</p>
  <div style="display:flex; justify-content:space-between; align-items:baseline;">
    <span class="toss-value-md">{fmt_krw(float(e['cash_krw']))}</span>
    <span class="toss-sub">{fmt_usd(float(e['cash_usd']))}</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # 시장 상태
        kr = kr_status(now)
        us = us_status(now)
        st.markdown(
            f"""
<div class="toss-card-tight">
  <p class="toss-label">시장 상태</p>
  <div style="font-size:13px; line-height:1.8;">
    {_market_dot(str(kr))} 🇰🇷 한국 · <span style="color:#6B7684">{status_label(kr)}</span><br/>
    {_market_dot(str(us))} 🇺🇸 미국 · <span style="color:#6B7684">{status_label(us)}</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.caption(
            f"환율 ₩{float(e['fx_rate']):,.0f}/USD · {now.strftime('%m-%d %H:%M KST')}"
        )
