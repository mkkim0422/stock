"""🧪 백테스트 — 시그널 전략 과거 성과 (Phase 4)."""
from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.backtest import evaluate_oos, run_single
from src.collectors import fetch_ohlcv
from src.collectors.mock import MockCollector
from src.storage import apply_migrations
from src.symbols import search_symbols
from src.ui.components import render_disclaimer, render_sidebar

st.set_page_config(page_title="백테스트 · swing-advisor", page_icon="🧪", layout="wide")
apply_migrations()
render_sidebar()

st.title("🧪 백테스트")
st.caption(
    "시그널 엔진의 과거 성과를 시뮬레이션합니다. 거래비용(수수료+거래세+슬리피지) 포함. "
    "look-ahead 가드 적용. **과거 성과는 미래를 보장하지 않습니다.**"
)


@st.cache_data(ttl=600, show_spinner=False)
def _fetch(symbol: str, days: int) -> pd.DataFrame:
    end = date.today()
    start = end - timedelta(days=days)
    if os.environ.get("USE_MOCK") == "1":
        try:
            return MockCollector().fetch_ohlcv(symbol, start, end)
        except Exception:
            return pd.DataFrame()
    try:
        return fetch_ohlcv(symbol, start, end)
    except Exception as e:
        st.warning(f"{symbol} 데이터 실패: {e}")
        return pd.DataFrame()


q = st.text_input("종목 검색", placeholder="삼성, 005930, AAPL", key="bt_q")
selected = None
if q:
    hits = search_symbols(q, limit=5)
    if hits:
        labels = [f"{h.symbol} · {h.name_kr or h.name} ({h.market})" for h in hits]
        idx = st.selectbox(
            "종목 선택", range(len(hits)),
            format_func=lambda i: labels[i],
        )
        selected = hits[idx]
    else:
        st.warning(f'"{q}" 결과 없음')

if selected is None:
    st.info("👆 종목을 검색하세요.")
    render_disclaimer()
    st.stop()

c1, c2, c3 = st.columns(3)
with c1:
    days = st.selectbox(
        "데이터 기간",
        [365, 730, 1095, 1825],
        format_func=lambda d: f"{d // 365}년",
        index=1,
    )
with c2:
    mode = st.radio("검증 모드", ["전체", "OOS 분할 (70/30)"], horizontal=True)
with c3:
    st.write("")
    st.write("")
    go_btn = st.button(
        "🚀 백테스트 실행", type="primary", use_container_width=True
    )

if not go_btn:
    render_disclaimer()
    st.stop()

with st.spinner(f"데이터 로딩 (최근 {days}일)..."):
    df = _fetch(selected.symbol, days)

if df.empty or len(df) < 250:
    st.error("데이터 부족 (250봉 이상 필요). 더 긴 기간 또는 다른 종목.")
    render_disclaimer()
    st.stop()


def _render_result(title: str, r) -> None:
    st.markdown(f"### {title}")
    m = r.metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 수익률", f"{m.total_return_pct:+.2f}%")
    c2.metric("CAGR", f"{m.cagr_pct:+.2f}%")
    c3.metric("최대 낙폭", f"{m.max_drawdown_pct:.2f}%")
    c4.metric("Sharpe", f"{m.sharpe:.2f}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sortino", f"{m.sortino:.2f}")
    c2.metric("승률", f"{m.win_rate_pct:.1f}%")
    c3.metric("Profit Factor", f"{m.profit_factor:.2f}")
    c4.metric("거래수", f"{m.n_trades}회")

    if not r.equity_curve.empty:
        fig = go.Figure(
            go.Scatter(
                x=r.equity_curve.index, y=r.equity_curve.values,
                mode="lines", line=dict(color="#1f77b4", width=2),
                name="자산곡선",
                hovertemplate="%{x}<br>₩%{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(
            height=320, margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="날짜", yaxis_title="평가액(KRW)",
        )
        st.plotly_chart(fig, use_container_width=True)

    if r.trades:
        st.markdown(f"**거래 내역 ({len(r.trades)}건)**")
        tdf = pd.DataFrame(r.trades)
        tdf = tdf.rename(columns={
            "entry_date": "진입일", "exit_date": "청산일",
            "entry_price": "진입가", "exit_price": "청산가",
            "qty": "수량", "pnl": "손익",
        })
        st.dataframe(tdf, hide_index=True, use_container_width=True)


market = "KR" if selected.market == "KR" else "US"

if mode == "전체":
    with st.spinner("백테스트 실행 중..."):
        try:
            r = run_single(selected.symbol, df, market=market)
            rid = r.persist(selected.symbol, market, mode="full")
            st.caption(f"💾 결과 저장됨 (ID #{rid})")
        except Exception as e:
            st.error(f"실행 실패: {e}")
            render_disclaimer()
            st.stop()
    _render_result(f"📈 {selected.symbol} 전체 기간", r)
else:
    with st.spinner("OOS 분할 백테스트..."):
        try:
            is_r, oos_r = evaluate_oos(selected.symbol, df, market=market)
            is_r.persist(selected.symbol, market, mode="in_sample")
            oos_r.persist(selected.symbol, market, mode="oos")
            st.caption("💾 In-Sample / OOS 결과 모두 저장됨")
        except Exception as e:
            st.error(f"실행 실패: {e}")
            render_disclaimer()
            st.stop()
    _render_result("🟦 In-Sample (학습 70%)", is_r)
    st.markdown("---")
    _render_result("🟢 Out-of-Sample (검증 30%)", oos_r)
    st.info(
        "💡 OOS 성과가 In-Sample 보다 크게 떨어지면 과최적화 가능성. "
        "Sharpe 차이 0.5+ 또는 CAGR 차이 50%+ 시 주의."
    )

render_disclaimer()
