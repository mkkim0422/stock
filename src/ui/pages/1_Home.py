"""🏠 홈 — 오늘의 요약 + 빠른 액션."""
from __future__ import annotations

import streamlit as st

from src.paper.performance import evaluate
from src.storage import apply_migrations, connect
from src.ui.components import kpi_row, render_disclaimer, render_sidebar
from src.ui.components.kpi_card import fmt_krw, fmt_pct
from src.utils.timezone import now_kst

st.set_page_config(page_title="홈 · swing-advisor", page_icon="🏠", layout="wide")

apply_migrations()
render_sidebar()

st.title("🏠 홈")
st.caption(f"오늘 {now_kst().strftime('%Y년 %m월 %d일 (%a)')} 의 가상 포트폴리오 현황")

e = evaluate()

# KPI 4카드
held_count = len(e["positions"])
kpi_row(
    [
        {"label": "총 평가액 (KRW 환산)", "value": fmt_krw(e["total_value_krw"])},
        {
            "label": "누적 수익률",
            "value": fmt_pct(e["cum_return_pct"]),
            "delta": None,
        },
        {"label": "보유 종목 수", "value": f"{held_count} 개"},
        {"label": "현금 (KRW)", "value": fmt_krw(e["cash_krw"])},
    ]
)

st.markdown("### 🧭 지금 무엇을 할까요?")
c1, c2, c3 = st.columns(3)
with c1:
    st.page_link("pages/4_PaperTrading.py", label="💼 가상매매 시작하기", icon="💼")
    st.caption("종목을 사거나 팔 수 있습니다.")
with c2:
    st.page_link("pages/5_Results.py", label="📊 투자결과 확인", icon="📊")
    st.caption("보유 종목, 평가손익, 자산곡선.")
with c3:
    st.page_link("pages/3_Stocks.py", label="🔍 종목 검색", icon="🔍")
    st.caption("관심 종목을 찾아봅니다.")

st.markdown("### 🩺 시스템 상태")
with connect() as conn:
    n_trades = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    n_pos = conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0]
c1, c2, c3 = st.columns(3)
c1.success("DB: 정상 (WAL)")
c2.info(f"거래 기록: {n_trades}건")
c3.info(f"포지션: {n_pos}건")

if held_count == 0 and n_trades == 0:
    st.info(
        "🎉 환영합니다! 아직 거래 기록이 없습니다. "
        "왼쪽 메뉴에서 **💼 가상투자** 페이지로 이동해 첫 매수를 시작하세요."
    )

render_disclaimer()
