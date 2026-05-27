"""시장 상태 배지 컴포넌트."""
from __future__ import annotations

import streamlit as st

from src.utils.market_hours import (
    kr_status,
    next_kr_open,
    next_us_open,
    status_label,
    us_status,
)
from src.utils.timezone import now_kst


def render_market_status() -> None:
    """현재 KR/US 시장 상태를 카드 2개로 표시 + 다음 개장 시각 안내."""
    now = now_kst()
    kr = kr_status(now)
    us = us_status(now)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**한국 (KRX)**: {status_label(kr)}")
        if kr != "OPEN":
            n = next_kr_open(now)
            st.caption(f"다음 개장: {n.strftime('%Y-%m-%d %H:%M KST')}")
        else:
            st.caption("정규장 진행 중 (09:00-15:30 KST)")
    with c2:
        st.markdown(f"**미국 (NYSE)**: {status_label(us)}")
        if us != "OPEN":
            n = next_us_open(now)
            st.caption(f"다음 개장: {n.strftime('%Y-%m-%d %H:%M KST')}")
        else:
            st.caption("정규장 진행 중 (09:30-16:00 ET)")
