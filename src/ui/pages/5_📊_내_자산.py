"""📊 내 자산 — 보유·손익·자산곡선 (토스 스타일)."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[3]
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.paper.performance import evaluate, snapshot_today
from src.storage import apply_migrations, connect
from src.ui.components import inject_css, render_disclaimer, render_sidebar
from src.ui.components.kpi_card import fmt_krw, fmt_pct
from src.ui.components.toss_style import (
    COLOR_BORDER,
    COLOR_DOWN,
    COLOR_SUBTLE,
    COLOR_UP,
)

st.set_page_config(page_title="내 자산 · swing-advisor", page_icon="📊", layout="wide")

inject_css()
apply_migrations()
render_sidebar()

st.markdown("## 📊 내 자산")
st.caption("현재 보유 종목, 손익, 자산 추이를 한눈에.")

e = evaluate()
ret = float(e["cum_return_pct"])
total = float(e["total_value_krw"])
init = float(e["initial_value_krw"])
pnl_value = total - init
ret_cls = "toss-up" if ret >= 0 else "toss-down"
pnl_cls = "toss-up" if pnl_value >= 0 else "toss-down"
ret_sign = "+" if ret >= 0 else ""
pnl_sign = "+" if pnl_value >= 0 else ""

# 메인 카드 — 총 평가액
st.markdown(
    f"""
<div class="toss-card">
  <p class="toss-label">내 평가 총액 (KRW 환산)</p>
  <p class="toss-value" style="font-size:36px;">{fmt_krw(total)}</p>
  <p class="toss-sub {ret_cls}" style="font-size:15px;">
    {ret_sign}{fmt_pct(ret)} · {pnl_sign}{fmt_krw(pnl_value)}
  </p>
</div>
""",
    unsafe_allow_html=True,
)

# 보조 카드들
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f"""
<div class="toss-card-tight">
  <p class="toss-label">보유 종목</p>
  <p class="toss-value-md">{len(e['positions'])}개</p>
</div>
""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
<div class="toss-card-tight">
  <p class="toss-label">현금 (KRW)</p>
  <p class="toss-value-md">{fmt_krw(float(e['cash_krw']))}</p>
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

# ─── 보유 포지션 ───────────────────────────────────────
st.markdown("### 💼 보유 포지션")
if e["positions"]:
    df = pd.DataFrame(e["positions"])
    df = df.rename(
        columns={
            "symbol": "종목",
            "market": "시장",
            "qty": "수량",
            "avg_price": "평단가",
            "current_price": "현재가",
            "value_krw": "평가액(KRW)",
            "pnl": "평가손익",
            "pnl_pct": "수익률(%)",
        }
    )

    def _style(row):
        pnl = row["수익률(%)"]
        if pnl > 0:
            return [f"color: {COLOR_UP};"] * len(row)
        if pnl < 0:
            return [f"color: {COLOR_DOWN};"] * len(row)
        return [""] * len(row)

    styled = df.style.apply(_style, axis=1).format(
        {
            "평단가": "{:,.2f}",
            "현재가": "{:,.2f}",
            "평가액(KRW)": "{:,.0f}",
            "평가손익": "{:,.2f}",
            "수익률(%)": "{:+.2f}%",
        }
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 CSV로 받기",
        csv,
        file_name="positions.csv",
        mime="text/csv",
    )
else:
    st.markdown(
        """
<div class="toss-card" style="background:#F1F7FF; border-color:#D6E6FF;">
  <p class="toss-value-md" style="color:#1B64DA;">🪄 아직 보유 종목이 없어요</p>
  <p class="toss-sub" style="margin-top:6px;">
    좌측 메뉴 <b>💰 사기 팔기</b> 에서 첫 매수를 해보세요.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

# ─── 자산곡선 ───────────────────────────────────────
st.markdown("### 📈 자산 추이")
with connect() as conn:
    snap_rows = conn.execute(
        "SELECT date, total_value_krw FROM portfolio_snapshots ORDER BY date"
    ).fetchall()

if len(snap_rows) >= 2:
    sdf = pd.DataFrame([dict(r) for r in snap_rows])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sdf["date"],
            y=sdf["total_value_krw"],
            mode="lines",
            line=dict(color="#3182F6", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(49,130,246,0.08)",
            name="총 평가액",
            hovertemplate="%{x}<br>₩%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=init, line_dash="dash", line_color=COLOR_SUBTLE,
        annotation_text="초기 자본", annotation_position="bottom right",
    )
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=20, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=False, color=COLOR_SUBTLE),
        yaxis=dict(
            showgrid=True, gridcolor=COLOR_BORDER,
            color=COLOR_SUBTLE, tickformat=",",
        ),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("자산 추이는 일일 스냅샷이 2건 이상 쌓이면 표시돼요.")
    if st.button("📸 오늘 스냅샷 저장", type="secondary"):
        snapshot_today()
        st.success("저장됨. 새로고침해 주세요.")

# ─── 거래 이력 ───────────────────────────────────────
st.markdown("### 📜 거래 이력")
with connect() as conn:
    rows = conn.execute(
        """
        SELECT ts, symbol, market, side, qty, fill_price, fee_amt, tax_amt,
               realized_pnl
        FROM trades ORDER BY id DESC LIMIT 100
        """
    ).fetchall()
if rows:
    df = pd.DataFrame([dict(r) for r in rows])
    df.columns = ["시각", "종목", "시장", "주문", "수량", "체결가", "수수료", "거래세", "실현손익"]
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.caption("거래 기록이 없어요.")

render_disclaimer()
