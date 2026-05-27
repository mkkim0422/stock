"""모든 페이지 하단에 일관된 면책 표시."""
from __future__ import annotations

import streamlit as st


def render_disclaimer() -> None:
    st.markdown("---")
    st.caption(
        "⚠️ 본 도구는 **페이퍼 트레이딩(가상매매) 전용**입니다. "
        "제공되는 정보·시그널은 참고용이며 매수/매도 권유가 아닙니다. "
        "모든 투자 책임은 사용자 본인에게 있으며, 가상매매 결과는 실거래 성과를 보장하지 않습니다."
    )
