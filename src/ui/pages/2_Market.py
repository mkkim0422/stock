"""📈 시장 — 시장 지표 (Phase 2 활성)."""
from __future__ import annotations

import streamlit as st

from src.ui.components import render_disclaimer, render_sidebar

st.set_page_config(page_title="시장 · swing-advisor", page_icon="📈", layout="wide")
render_sidebar()

st.title("📈 시장")
st.caption("KOSPI/KOSDAQ/S&P500/NASDAQ 지표")

st.info("🚧 이 페이지는 **Phase 2** 에서 활성됩니다. 실데이터 수집 후 KOSPI/KOSDAQ/미국 지수가 표시됩니다.")

st.markdown("### 미리 보기 (mock)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("KOSPI", "2,750.12", "+0.5%")
c2.metric("KOSDAQ", "880.45", "-0.2%")
c3.metric("S&P 500", "5,890.10", "+0.3%")
c4.metric("NASDAQ", "19,120.55", "+0.7%")
st.caption("위 수치는 mock 입니다. 실데이터 아님.")

render_disclaimer()
