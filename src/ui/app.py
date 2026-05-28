"""swing-advisor 메인 진입점.

실행: streamlit run src/ui/app.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

# Streamlit Cloud Secrets → 환경변수 동기화 (pydantic-settings 가 읽도록)
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str) and _k not in os.environ:
            os.environ[_k] = _v
except Exception:
    pass  # secrets 파일 없으면 무시 (로컬 .env 사용)

from src.storage import apply_migrations
from src.ui.components import inject_css, render_disclaimer, render_sidebar
from src.utils.timezone import now_kst

st.set_page_config(
    page_title="swing-advisor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
apply_migrations()

# 종목 마스터 자동 갱신 (3시간 간격, 백그라운드 첫 진입 시 한 번만)
try:
    from src.symbols import maybe_refresh
    maybe_refresh()
except Exception:
    pass  # 갱신 실패해도 앱은 계속 작동

render_sidebar()

_hour = now_kst().hour
if _hour < 6:
    _greet = "늦은 시간이에요"
elif _hour < 12:
    _greet = "좋은 아침이에요"
elif _hour < 18:
    _greet = "오후도 화이팅"
else:
    _greet = "오늘 하루 수고하셨어요"

st.markdown(f"## 👋 {_greet}")
st.caption("좌측 메뉴에서 원하는 화면을 골라보세요 · 페이퍼 트레이딩 전용")

st.markdown("### 어디로 가볼까요?")
c1, c2 = st.columns(2)
with c1:
    st.page_link("pages/1_🏠_홈.py", label="**🏠 홈** · 오늘 내 자산 요약")
    st.page_link("pages/9_🎯_오늘의_추천.py", label="**🎯 오늘의 추천** · AI 매수/매도 후보")
    st.page_link("pages/4_💰_사기_팔기.py", label="**💰 사기 팔기** · 가상 매매")
    st.page_link("pages/5_📊_내_자산.py", label="**📊 내 자산** · 보유·손익·차트")
with c2:
    st.page_link("pages/2_📈_오늘의_시장.py", label="**📈 오늘의 시장** · 한·미 지수")
    st.page_link("pages/3_🔍_종목_찾기.py", label="**🔍 종목 찾기** · 종목 검색·차트")
    st.page_link("pages/6_🧪_전략_검증.py", label="**🧪 전략 검증** · 백테스트 (전문가용)")
    st.page_link("pages/7_⚙️_설정.py", label="**⚙️ 설정** · 환경·연결 상태")

render_disclaimer()
