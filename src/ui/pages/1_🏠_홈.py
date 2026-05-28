"""🏠 홈 — 오늘의 요약 + 빠른 액션 (토스 스타일)."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[3]
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import streamlit as st

from src.paper.performance import evaluate
from src.storage import apply_migrations, connect
from src.ui.components import (
    inject_css,
    render_disclaimer,
    render_sidebar,
)
from src.ui.components.kpi_card import fmt_krw, fmt_pct
from src.utils.timezone import now_kst

st.set_page_config(page_title="홈 · swing-advisor", page_icon="🏠", layout="wide")

inject_css()
apply_migrations()
render_sidebar()

now = now_kst()
hour = now.hour
if hour < 6:
    greet = "늦은 시간이에요"
elif hour < 12:
    greet = "좋은 아침이에요"
elif hour < 18:
    greet = "오후도 화이팅"
else:
    greet = "오늘 하루 수고하셨어요"

st.markdown(f"## 👋 {greet}")
st.caption(f"{now.strftime('%Y년 %m월 %d일 %A')} · 가상 포트폴리오")

e = evaluate()
ret = float(e["cum_return_pct"])
total = float(e["total_value_krw"])
cash = float(e["cash_krw"])
held = len(e["positions"])
ret_cls = "toss-up" if ret >= 0 else "toss-down"
ret_sign = "+" if ret >= 0 else ""

st.markdown(
    f"""
<div class="toss-card">
  <p class="toss-label">내 평가 총액 (KRW 환산)</p>
  <p class="toss-value" style="font-size:36px;">{fmt_krw(total)}</p>
  <p class="toss-sub {ret_cls}" style="font-size:15px;">{ret_sign}{fmt_pct(ret)} · 누적 수익률</p>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f"""
<div class="toss-card-tight">
  <p class="toss-label">현금 (KRW)</p>
  <p class="toss-value-md">{fmt_krw(cash)}</p>
</div>
""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
<div class="toss-card-tight">
  <p class="toss-label">보유 종목</p>
  <p class="toss-value-md">{held}개</p>
</div>
""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""
<div class="toss-card-tight">
  <p class="toss-label">현금 (USD)</p>
  <p class="toss-value-md">${float(e['cash_usd']):,.2f}</p>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("### 어디로 가볼까요?")
st.caption("자주 쓰는 화면을 빠르게 열 수 있어요.")

c1, c2 = st.columns(2)
with c1:
    st.page_link(
        "pages/9_🎯_오늘의_추천.py",
        label="**🎯 오늘의 추천** · AI가 골라준 매수/매도 후보",
    )
    st.page_link(
        "pages/4_💰_사기_팔기.py",
        label="**💰 사기 팔기** · 가상 매수·매도",
    )
with c2:
    st.page_link(
        "pages/5_📊_내_자산.py",
        label="**📊 내 자산** · 보유 종목·손익·차트",
    )
    st.page_link(
        "pages/3_🔍_종목_찾기.py",
        label="**🔍 종목 찾기** · 종목 검색·상세",
    )

# 시스템 상태 (조용히, 카드 하나로)
with connect() as conn:
    n_trades = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    n_pos = conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0]

if held == 0 and n_trades == 0:
    st.markdown(
        """
<div class="toss-card" style="background:#F1F7FF; border-color:#D6E6FF;">
  <p class="toss-value-md" style="color:#1B64DA;">🎉 환영합니다</p>
  <p class="toss-sub" style="margin-top:6px;">
    아직 거래 기록이 없네요. <b>🎯 오늘의 추천</b>에서 후보 종목을 살펴보고
    <b>💰 사기 팔기</b>에서 첫 매수를 시도해 보세요.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

with st.expander("🩺 시스템 상태 (자세히)", expanded=False):
    st.write(f"DB: 정상 (WAL) · 거래 기록 {n_trades}건 · 포지션 {n_pos}건")
    st.caption(f"마지막 갱신: {now.strftime('%Y-%m-%d %H:%M KST')}")

render_disclaimer()
