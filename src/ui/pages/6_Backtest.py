"""🧪 백테스트 — Phase 4 활성."""
from __future__ import annotations

import streamlit as st

from src.ui.components import render_disclaimer, render_sidebar

st.set_page_config(page_title="백테스트 · swing-advisor", page_icon="🧪", layout="wide")
render_sidebar()

st.title("🧪 백테스트")
st.info(
    "🚧 이 페이지는 **Phase 4** 에서 활성됩니다.\n\n"
    "- 워크포워드 검증\n"
    "- OOS (Out-of-Sample)\n"
    "- 거래비용 포함 (수수료 + 거래세 + 슬리피지)\n"
    "- 메트릭: CAGR, Sharpe, Sortino, MDD"
)

st.markdown("### 무결성 가드 (Phase 1 이미 작동)")
st.success("✅ look-ahead 방지 모듈: `src/backtest/lookahead_guard.py`")
st.success("✅ survivorship 필터 인터페이스: `src/backtest/survivorship_filter.py`")
st.success("✅ OOS / walk-forward 인터페이스: `src/backtest/`")

render_disclaimer()
