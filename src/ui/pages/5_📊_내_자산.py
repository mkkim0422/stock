"""📊 투자결과 — 평가액, 보유, 자산곡선 (작동 페이지)."""
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
from src.ui.components import kpi_row, render_disclaimer, render_sidebar
from src.ui.components.kpi_card import fmt_krw, fmt_pct

st.set_page_config(page_title="투자결과 · swing-advisor", page_icon="📊", layout="wide")
apply_migrations()
render_sidebar()

st.title("📊 투자결과")
st.caption("현재 보유, 손익, 자산곡선")

e = evaluate()

# KPI 4카드
ret = e["cum_return_pct"]
day_pnl_value = e["total_value_krw"] - e["initial_value_krw"]
kpi_row(
    [
        {"label": "총 평가액", "value": fmt_krw(e["total_value_krw"])},
        {
            "label": "총 손익",
            "value": fmt_krw(day_pnl_value),
            "delta": fmt_pct(ret),
        },
        {"label": "보유 종목", "value": f"{len(e['positions'])} 개"},
        {"label": "현금 (KRW)", "value": fmt_krw(e["cash_krw"])},
    ]
)

# ─── 보유 포지션 표 ─────────────────────────────────────────
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
            color = "color: #16a34a;"
        elif pnl < 0:
            color = "color: #dc2626;"
        else:
            color = ""
        return [color] * len(row)

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
        "📥 CSV 다운로드",
        csv,
        file_name="positions.csv",
        mime="text/csv",
        use_container_width=False,
    )
else:
    st.info(
        "🪄 아직 보유 종목이 없습니다. "
        "왼쪽 메뉴 **💼 가상투자** 에서 첫 매수를 해보세요."
    )

# ─── 자산곡선 ─────────────────────────────────────────────
st.markdown("### 📈 자산곡선")
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
            mode="lines+markers",
            line=dict(color="#1f77b4", width=2),
            name="총 평가액",
            hovertemplate="%{x}<br>₩%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=e["initial_value_krw"], line_dash="dash", line_color="#6b7280",
        annotation_text="초기 자본", annotation_position="bottom right",
    )
    fig.update_layout(
        height=400, margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="날짜", yaxis_title="KRW",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("자산곡선은 일일 스냅샷이 2건 이상 쌓이면 표시됩니다.")
    if st.button("📸 오늘 스냅샷 저장"):
        snapshot_today()
        st.success("저장됨. 새로고침하세요.")

# ─── 거래 이력 ─────────────────────────────────────────────
st.markdown("### 📜 전체 거래 이력")
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
    st.caption("거래 기록이 없습니다.")

render_disclaimer()
