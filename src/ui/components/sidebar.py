"""사이드바 — 모드, 평가액, 갱신시각 (모든 페이지 동일)."""
from __future__ import annotations

import streamlit as st

from src.config import get_settings
from src.paper.performance import evaluate
from src.storage import apply_migrations
from src.ui.components.kpi_card import fmt_krw, fmt_pct, fmt_usd
from src.utils.timezone import now_kst


def render_sidebar() -> None:
    apply_migrations()
    settings = get_settings()
    e = evaluate()

    with st.sidebar:
        st.markdown("### 📊 swing-advisor")
        st.caption(f"모드: **{settings.mode}** (페이퍼 전용)")
        st.markdown("---")
        st.markdown("**💰 자산**")
        st.write(f"KRW: {fmt_krw(e['cash_krw'])}")
        st.write(f"USD: {fmt_usd(e['cash_usd'])}")
        st.write(f"환산 총액: {fmt_krw(e['total_value_krw'])}")
        ret = e["cum_return_pct"]
        color = "🟢" if ret >= 0 else "🔴"
        st.write(f"누적 수익률: {color} {fmt_pct(ret)}")
        st.markdown("---")
        st.caption(f"갱신: {now_kst().strftime('%Y-%m-%d %H:%M KST')}")
        st.caption(f"환율(mock): ₩{e['fx_rate']:,.0f}/USD")
