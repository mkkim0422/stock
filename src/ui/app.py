"""swing-advisor 메인 진입점.

실행: streamlit run src/ui/app.py
"""
from __future__ import annotations

import streamlit as st

from src.storage import apply_migrations
from src.ui.components import render_disclaimer, render_sidebar

st.set_page_config(
    page_title="swing-advisor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_migrations()
render_sidebar()

st.title("📊 swing-advisor")
st.caption("한국+미국 스윙 트레이딩 보조 · 페이퍼 트레이딩 전용")

st.markdown(
    """
    좌측 메뉴에서 페이지를 선택하세요.

    - 🏠 **홈** — 오늘의 요약
    - 💼 **가상투자** — 모의 매수/매도
    - 📊 **투자결과** — 평가액, 손익, 보유 종목
    - 🔍 **종목** — 종목 검색
    - 📈 **시장** — 시장 지표 (Phase 2)
    - 🧪 **백테스트** — (Phase 4)
    - ⚙️ **설정** — (Phase 7)
    - ❓ **도움말** — FAQ, 면책
    """
)

render_disclaimer()
