"""🔍 종목 — 검색 + 상세 (Phase 2 활성: 차트, 지표)."""
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
from plotly.subplots import make_subplots

from src.indicators import macd, rsi, sma
from src.symbols import Symbol, search_symbols
from src.ui.components import inject_css, render_disclaimer, render_sidebar
from src.ui.components.kpi_card import fmt_krw, fmt_usd

st.set_page_config(page_title="종목 찾기 · swing-advisor", page_icon="🔍", layout="wide")
inject_css()
render_sidebar()

st.markdown("## 🔍 종목 찾기")
st.caption("종목명·코드·영문명으로 검색해 차트와 지표를 확인해 보세요.")


@st.cache_data(ttl=900, show_spinner=False)
def _fetch_ohlcv(symbol: str, days: int) -> pd.DataFrame:
    if os.environ.get("USE_MOCK") == "1":
        from src.collectors.mock import MockCollector
        end = date.today()
        try:
            return MockCollector().fetch_ohlcv(symbol, end - timedelta(days=days), end)
        except Exception:
            return pd.DataFrame()
    from src.collectors import fetch_ohlcv
    end = date.today()
    try:
        return fetch_ohlcv(symbol, end - timedelta(days=days), end)
    except Exception as e:
        st.warning(f"가져오기 실패: {e}")
        return pd.DataFrame()


# ── 검색 ──────────────────────────────────────────────
q = st.text_input(
    "검색", placeholder="예: 삼성, 005930, AAPL", key="stock_search",
    label_visibility="collapsed",
)

if not q:
    st.info("🔎 검색어를 입력하세요 (티커, 영문명, 한글명).")
    render_disclaimer()
    st.stop()

with st.spinner("검색 중..."):
    hits: list[Symbol] = search_symbols(q, limit=30)

if not hits:
    st.warning(f'"{q}" 에 대한 결과가 없습니다.')
    render_disclaimer()
    st.stop()

table = pd.DataFrame(
    [
        {"코드": s.symbol, "시장": s.market,
         "영문명": s.name, "한글명": s.name_kr or "",
         "섹터": s.sector or ""}
        for s in hits
    ]
)
st.dataframe(table, hide_index=True, use_container_width=True)

# ── 상세: 첫 결과 자동 선택, 사용자가 변경 가능 ─────────────
labels = [f"{h.symbol} · {h.name_kr or h.name} ({h.market})" for h in hits]
idx = st.selectbox(
    "상세 보기 종목", range(len(hits)), format_func=lambda i: labels[i]
)
sel: Symbol = hits[idx]

period = st.radio(
    "기간", ["1M", "3M", "6M", "1Y"], horizontal=True, index=2
)
days_map = {"1M": 35, "3M": 100, "6M": 200, "1Y": 380}
days = days_map[period]

with st.spinner("차트 로딩..."):
    df = _fetch_ohlcv(sel.symbol, days)

if df.empty:
    st.error(
        "이 종목은 현재 데이터를 받아올 수 없습니다. "
        "다른 종목을 선택하거나 잠시 후 다시 시도하세요."
    )
    render_disclaimer()
    st.stop()

last = float(df["close"].iloc[-1])
prev = float(df["close"].iloc[-2]) if len(df) >= 2 else last
chg_pct = (last / prev - 1) * 100 if prev else 0.0
unit_fmt = fmt_krw if sel.market == "KR" else fmt_usd

c1, c2, c3 = st.columns([1, 1, 2])
c1.metric("현재가", unit_fmt(last), f"{chg_pct:+.2f}%")
c2.metric("기간 시작가", unit_fmt(float(df["close"].iloc[0])))
hi = float(df["high"].max())
lo = float(df["low"].min())
c3.metric("기간 고/저", f"{unit_fmt(hi)} / {unit_fmt(lo)}")

# 캔들 + MA + 거래량 + RSI/MACD
close = df["close"].astype(float)
ma20 = sma(close, 20)
ma60 = sma(close, 60)
rsi14 = rsi(close, 14)
m = macd(close)

fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=[0.55, 0.2, 0.25],
)

fig.add_trace(
    go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="가격",
        increasing_line_color="#16a34a", decreasing_line_color="#dc2626",
    ),
    row=1, col=1,
)
fig.add_trace(go.Scatter(x=df.index, y=ma20, mode="lines",
                        name="MA20", line=dict(color="#1f77b4", width=1)),
              row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=ma60, mode="lines",
                        name="MA60", line=dict(color="#9333ea", width=1)),
              row=1, col=1)

fig.add_trace(
    go.Bar(x=df.index, y=df["volume"], name="거래량",
           marker_color="#94a3b8"),
    row=2, col=1,
)

fig.add_trace(
    go.Scatter(x=df.index, y=rsi14, mode="lines", name="RSI(14)",
               line=dict(color="#0ea5e9")),
    row=3, col=1,
)
fig.add_hline(y=70, line_dash="dash", line_color="#dc2626", row=3, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="#16a34a", row=3, col=1)

fig.update_layout(
    height=700, margin=dict(l=20, r=20, t=20, b=20),
    showlegend=True,
    xaxis_rangeslider_visible=False,
)
fig.update_yaxes(title_text="가격", row=1, col=1)
fig.update_yaxes(title_text="거래량", row=2, col=1)
fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)

st.plotly_chart(fig, use_container_width=True)

with st.expander("📐 MACD 차트"):
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df.index, y=m["macd"], mode="lines",
                              name="MACD", line=dict(color="#1f77b4")))
    fig2.add_trace(go.Scatter(x=df.index, y=m["signal"], mode="lines",
                              name="Signal", line=dict(color="#dc2626")))
    colors = ["#16a34a" if v >= 0 else "#dc2626" for v in m["hist"].fillna(0)]
    fig2.add_trace(go.Bar(x=df.index, y=m["hist"], name="Histogram",
                          marker_color=colors))
    fig2.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig2, use_container_width=True)

st.caption("⓵ 가격: Phase 2 다중 소스 (KR: pykrx, US: yfinance→FDR 폴백). 캐시 15분.")
render_disclaimer()
