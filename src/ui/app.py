"""swing-advisor 메인 진입점.

실행: streamlit run src/ui/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

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

# 종목 마스터 자동 갱신 (3시간 간격, 백그라운드 첫 진입 시 한 번만)
try:
    from src.symbols import maybe_refresh
    maybe_refresh()
except Exception:
    pass  # 갱신 실패해도 앱은 계속 작동

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
