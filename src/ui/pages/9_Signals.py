"""🎯 시그널 — 워치리스트 종목 매수/매도 점수 모니터링."""
from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.collectors import fetch_ohlcv
from src.collectors.mock import MockCollector
from src.llm import generate_signal_comment
from src.llm import is_available as llm_available
from src.signals import evaluate as eval_signal_only
from src.signals import evaluate_and_persist
from src.storage import apply_migrations
from src.symbols import search_symbols
from src.symbols.watchlist import add, list_all, remove
from src.ui.components import render_disclaimer, render_sidebar

st.set_page_config(page_title="시그널 · swing-advisor", page_icon="🎯", layout="wide")
apply_migrations()
render_sidebar()

st.title("🎯 시그널 모니터링")
st.caption(
    "관심 종목의 **매수(+8 이상) / 매도(-3 이하) 시그널**을 종합 점수로 표시합니다. "
    "참고용이며 매매 권유가 아닙니다."
)


@st.cache_data(ttl=300, show_spinner=False)
def _fetch(symbol: str, days: int = 250) -> pd.DataFrame:
    if os.environ.get("USE_MOCK") == "1":
        try:
            return MockCollector().fetch_ohlcv(
                symbol, date.today() - timedelta(days=days), date.today()
            )
        except Exception:
            return pd.DataFrame()
    try:
        return fetch_ohlcv(
            symbol, date.today() - timedelta(days=days), date.today()
        )
    except Exception as e:
        st.warning(f"{symbol} 데이터 실패: {e}")
        return pd.DataFrame()


# ── 워치리스트 관리 ──────────────────────────────────────────
with st.expander("➕ 워치리스트 종목 추가/관리", expanded=False):
    c1, c2 = st.columns([2, 1])
    with c1:
        q = st.text_input("종목 검색", placeholder="삼성, AAPL ...", key="watch_q")
        if q:
            hits = search_symbols(q, limit=5)
            for h in hits:
                if st.button(
                    f"➕ {h.symbol} · {h.name_kr or h.name}", key=f"add_{h.symbol}"
                ):
                    add(h.symbol)
                    st.success(f"{h.symbol} 추가")
                    st.rerun()
    with c2:
        st.caption("현재 워치리스트")
        for s in list_all():
            cc1, cc2 = st.columns([3, 1])
            cc1.write(s)
            if cc2.button("❌", key=f"rm_{s}"):
                remove(s)
                st.rerun()


# ── 시그널 평가 ──────────────────────────────────────────
watched = list_all()
if not watched:
    st.info(
        "👀 워치리스트가 비어있습니다. 위에서 종목을 추가하면 자동으로 시그널이 계산됩니다."
    )
    render_disclaimer()
    st.stop()

st.markdown(f"### 📊 워치리스트 ({len(watched)}개)")

if st.button("🔄 지금 다시 평가", type="primary"):
    _fetch.clear()
    st.rerun()

results: list[dict] = []
progress = st.progress(0.0, text="시그널 평가 중...")
for i, sym in enumerate(watched, start=1):
    df = _fetch(sym)
    if df.empty or len(df) < 60:
        results.append({
            "종목": sym, "점수": None, "액션": "—",
            "이유": "데이터 부족",
        })
    else:
        try:
            sig = evaluate_and_persist(sym, df)
            results.append({
                "종목": sym,
                "점수": sig.score,
                "액션": sig.action,
                "이유": "; ".join(
                    f"{n}({c['score']:+d}: {c['reason']})"
                    for n, c in sig.components.items() if c["score"] != 0
                ) or "(전 항목 중립)",
            })
        except Exception as e:
            results.append({
                "종목": sym, "점수": None, "액션": "—",
                "이유": f"오류: {e}",
            })
    progress.progress(i / len(watched), text=f"{sym} ({i}/{len(watched)})")
progress.empty()

# 점수 기준 정렬: 매수 후보 위 → 중립 → 매도 후보
df_r = pd.DataFrame(results)
df_r["_sort"] = df_r["점수"].fillna(-999)
df_r = df_r.sort_values("_sort", ascending=False).drop(columns=["_sort"])


def _color(action: str) -> str:
    return {
        "BUY": "background-color: #dcfce7; color: #16a34a; font-weight: bold;",
        "SELL": "background-color: #fee2e2; color: #dc2626; font-weight: bold;",
        "HOLD": "color: #6b7280;",
        "—": "color: #94a3b8;",
    }.get(action, "")


styled = df_r.style.map(_color, subset=["액션"])
st.dataframe(styled, use_container_width=True, hide_index=True)

# ── KPI ─────────────────────────────────────────────────
buy_n = sum(1 for r in results if r["액션"] == "BUY")
sell_n = sum(1 for r in results if r["액션"] == "SELL")
hold_n = sum(1 for r in results if r["액션"] == "HOLD")
c1, c2, c3 = st.columns(3)
c1.metric("🟢 매수 후보 (≥+8)", buy_n)
c2.metric("🔴 매도 후보 (≤-3)", sell_n)
c3.metric("⚪ 관망 (HOLD)", hold_n)

st.caption(
    "📐 점수 산식: RSI(±2) + MACD 크로스(±3) + 이동평균 위(+1×3) + "
    "5일 과열(-1) + 거래량 평균 2x+(+2) + OBV 매집(+1)."
)

# ── LLM 코멘트 (옵션) ─────────────────────────────────
if llm_available() and (buy_n + sell_n) > 0:
    st.markdown("### 🤖 LLM 보조 코멘트")
    st.caption("매수/매도 후보 종목에 대한 자동 생성 코멘트입니다. **참고용**.")
    interesting = [r for r in results if r["액션"] in ("BUY", "SELL")][:5]
    for r in interesting:
        sym = r["종목"]
        hits = search_symbols(sym, limit=1)
        name_kr = hits[0].name_kr if hits else sym
        df_x = _fetch(sym)
        if df_x.empty:
            continue
        try:
            sig = eval_signal_only(sym, df_x)
            comment = generate_signal_comment(
                sym, name_kr or sym, sig.action, sig.score, sig.components
            )
        except Exception:
            comment = None
        if comment:
            emoji = "🟢" if r["액션"] == "BUY" else "🔴"
            with st.expander(f"{emoji} {sym} ({name_kr or '—'}) — 점수 {r['점수']:+d}"):
                st.write(comment)

render_disclaimer()
