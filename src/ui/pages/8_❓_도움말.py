"""❓ 도움말 — FAQ + 면책 전문."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[3]
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import streamlit as st

from src.ui.components import inject_css, render_disclaimer, render_sidebar

st.set_page_config(page_title="도움말 · swing-advisor", page_icon="❓", layout="wide")
inject_css()
render_sidebar()

st.markdown("## ❓ 도움말")
st.caption("자주 묻는 질문과 면책 전문.")

st.markdown("### 자주 묻는 질문")
with st.expander("이 도구는 실제로 주식을 사주나요?"):
    st.write("**아니요.** 이 도구는 페이퍼 트레이딩(가상매매) 전용입니다. 실주문 API 코드가 없습니다.")
with st.expander("가상매매 결과를 그대로 실거래로 옮기면 어떻게 되나요?"):
    st.write(
        "보장 못 합니다. 실거래에서는 슬리피지, 호가 깊이, 시장가 부족, 미체결, 수수료 차이 등으로 "
        "결과가 달라집니다. 모든 투자 책임은 사용자 본인에게 있습니다."
    )
with st.expander("환율은 어떻게 적용되나요?"):
    st.write(
        "Phase 1 은 mock 환율 1,350 KRW/USD 고정. 환전 수수료 0.1% 적용. "
        "Phase 2 에서 실시간 환율로 전환됩니다."
    )
with st.expander("거래세/수수료는 얼마인가요?"):
    st.write(
        "- 한국 매수 수수료: 0.015%\n"
        "- 한국 매도 수수료: 0.015% + 거래세 0.20% (2026-01-01 시행)\n"
        "- 미국 수수료: $0 (모의)\n"
        "- 슬리피지: 0.07% (스윙 기준)"
    )
with st.expander("Phase 별 활성 기능은?"):
    st.markdown(
        "- **Phase 1 (현재)**: 가상매매 + 결과\n"
        "- **Phase 2**: 실데이터 수집\n"
        "- **Phase 3**: 지표/시그널 엔진\n"
        "- **Phase 4**: 백테스트\n"
        "- **Phase 5**: LLM 보조\n"
        "- **Phase 6**: 텔레그램 알림\n"
        "- **Phase 7**: 자동 운영"
    )
with st.expander("내 데이터는 어디 저장되나요?"):
    st.write("로컬 SQLite (`data/db/swing.db`). 외부 송신 없음.")

st.markdown("### 📜 면책 전문")
st.warning(
    """
    1. 본 도구는 **페이퍼 트레이딩(가상매매) 전용**이며, 실주문 기능이 없습니다.
    2. 제공되는 시그널/분석은 **참고용**이며 매수/매도 권유가 아닙니다.
    3. 모든 투자 결정과 결과(이익/손실)의 **책임은 사용자 본인**에게 있습니다.
    4. 페이퍼 트레이딩 결과는 **실거래 성과를 보장하지 않습니다**.
    5. 데이터 오류/누락/지연 가능성이 있습니다.
    6. 본 도구는 **투자자문업·투자권유** 행위가 아닙니다.
    7. 본 도구는 **개인 학습/연구** 목적입니다.
    """
)

render_disclaimer()
