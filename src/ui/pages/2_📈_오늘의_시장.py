"""📈 시장 — KOSPI/KOSDAQ/S&P 500/NASDAQ 지수 (Phase 2 활성)."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[3]
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import os
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.components import inject_css, render_disclaimer, render_sidebar
from src.ui.components.toss_style import COLOR_BORDER, COLOR_BRAND, COLOR_SUBTLE

st.set_page_config(page_title="오늘의 시장 · swing-advisor", page_icon="📈", layout="wide")
inject_css()
render_sidebar()

st.markdown("## 📈 오늘의 시장")
st.caption("한국·미국 주요 지수의 오늘 현황과 6개월 추이.")


INDEX_DEFS = [
    ("KS11", "KOSPI", "KR"),
    ("KQ11", "KOSDAQ", "KR"),
    ("US500", "S&P 500", "US"),
    ("IXIC", "NASDAQ", "US"),
]


@st.cache_data(ttl=900, show_spinner=False)
def _fetch_index(code: str, days: int = 180) -> pd.DataFrame:
    if os.environ.get("USE_MOCK") == "1":
        # mock: 임의 횡보 곡선
        import numpy as np
        idx = pd.date_range(end=date.today(), periods=days, freq="B")
        rng = np.random.default_rng(hash(code) & 0xFFFF)
        rets = rng.normal(0.0003, 0.01, size=len(idx))
        close = 1000 * (1 + rets).cumprod()
        return pd.DataFrame({"close": close}, index=idx.date)
    try:
        import FinanceDataReader as fdr
        end = date.today()
        start = end - timedelta(days=days)
        df = fdr.DataReader(code, start.isoformat(), end.isoformat())
        if df.empty:
            return pd.DataFrame()
        df = df.rename(columns={"Close": "close"})
        return df[["close"]]
    except Exception as e:
        st.warning(f"{code} 가져오기 실패: {e}")
        return pd.DataFrame()


cols = st.columns(4)
for col, (code, name, _market) in zip(cols, INDEX_DEFS, strict=True):
    with col:
        with st.spinner(f"{name} 불러오는 중..."):
            df = _fetch_index(code, days=10)
        if df.empty or len(df) < 2:
            st.metric(name, "—", help="데이터 없음")
            continue
        last = float(df["close"].iloc[-1])
        prev = float(df["close"].iloc[-2])
        chg_pct = (last / prev - 1) * 100 if prev else 0.0
        st.metric(name, f"{last:,.2f}", f"{chg_pct:+.2f}%")

st.markdown("### 📊 6개월 추이")
tabs = st.tabs([n for _, n, _ in INDEX_DEFS])
for tab, (code, name, _market) in zip(tabs, INDEX_DEFS, strict=True):
    with tab:
        with st.spinner(f"{name} 6개월 차트..."):
            df = _fetch_index(code, days=180)
        if df.empty:
            st.info("데이터 없음")
            continue
        fig = go.Figure(
            go.Scatter(
                x=df.index,
                y=df["close"],
                mode="lines",
                line=dict(color=COLOR_BRAND, width=2.5),
                fill="tozeroy",
                fillcolor="rgba(49,130,246,0.06)",
                name=name,
                hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
            )
        )
        fig.update_layout(
            height=380, margin=dict(l=10, r=10, t=20, b=20),
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(showgrid=False, color=COLOR_SUBTLE),
            yaxis=dict(showgrid=True, gridcolor=COLOR_BORDER, color=COLOR_SUBTLE, tickformat=","),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

st.caption("⓵ 데이터: FinanceDataReader (지연 가능). 캐시: 15분.")
render_disclaimer()
