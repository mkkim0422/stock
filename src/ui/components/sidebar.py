"""사이드바 — 모드, 평가액, 시장상태, 갱신시각 (모든 페이지 동일)."""
from __future__ import annotations

import streamlit as st

from src.config import get_settings
from src.paper.performance import evaluate
from src.storage import apply_migrations
from src.ui.components.kpi_card import fmt_krw, fmt_pct, fmt_usd
from src.utils.market_hours import kr_status, status_label, us_status
from src.utils.timezone import now_kst


def render_sidebar() -> None:
    apply_migrations()
    settings = get_settings()
    e = evaluate()
    now = now_kst()

    with st.sidebar:
        st.markdown("### 📊 swing-advisor")
        st.caption(f"모드: **{settings.mode}** (페이퍼 전용)")
        st.markdown("---")

        # 시장 상태 (모든 페이지에 노출)
        st.markdown("**🕒 시장 상태**")
        st.caption(f"🇰🇷 KR: {status_label(kr_status(now))}")
        st.caption(f"🇺🇸 US: {status_label(us_status(now))}")
        st.markdown("---")

        st.markdown("**💰 자산**")
        st.write(f"KRW: {fmt_krw(float(e['cash_krw']))}")
        st.write(f"USD: {fmt_usd(float(e['cash_usd']))}")
        st.write(f"환산 총액: {fmt_krw(float(e['total_value_krw']))}")
        ret = float(e["cum_return_pct"])
        color = "🟢" if ret >= 0 else "🔴"
        st.write(f"누적 수익률: {color} {fmt_pct(ret)}")
        st.markdown("---")
        st.caption(f"갱신: {now.strftime('%Y-%m-%d %H:%M KST')}")
        st.caption(f"환율: ₩{float(e['fx_rate']):,.0f}/USD")
