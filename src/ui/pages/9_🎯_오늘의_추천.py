"""🎯 오늘의 추천 — 워치리스트 종목의 매수/매도 점수 + AI 코멘트 (토스 스타일)."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[3]
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

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
from src.ui.components import (
    badge,
    inject_css,
    recommendation_card,
    render_disclaimer,
    render_sidebar,
)

st.set_page_config(page_title="오늘의 추천 · swing-advisor", page_icon="🎯", layout="wide")

inject_css()
apply_migrations()
render_sidebar()

st.markdown("## 🎯 오늘의 추천")
st.caption(
    "관심 종목들을 10가지 지표로 분석해 점수를 매겼어요. "
    "+8 이상은 매수 후보, -3 이하는 매도 후보. **참고용**이며 매매 권유가 아닙니다."
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


# ── 워치리스트 관리 ────────────────────────────────────────
with st.expander("➕ 관심 종목 추가·관리", expanded=False):
    c1, c2 = st.columns([2, 1])
    with c1:
        q = st.text_input(
            "종목 이름 또는 코드로 검색",
            placeholder="예) 삼성전자, 005930, AAPL",
            key="watch_q",
        )
        if q:
            hits = search_symbols(q, limit=5)
            for h in hits:
                if st.button(
                    f"➕ {h.symbol} · {h.name_kr or h.name}",
                    key=f"add_{h.symbol}",
                    type="secondary",
                ):
                    add(h.symbol)
                    st.success(f"{h.symbol} 추가됨")
                    st.rerun()
    with c2:
        st.caption(f"현재 관심 종목 {len(list_all())}개")
        for s in list_all():
            cc1, cc2 = st.columns([3, 1])
            cc1.write(s)
            if cc2.button("❌", key=f"rm_{s}"):
                remove(s)
                st.rerun()


watched = list_all()
if not watched:
    st.markdown(
        """
<div class="toss-card" style="background:#F1F7FF; border-color:#D6E6FF;">
  <p class="toss-value-md" style="color:#1B64DA;">👀 관심 종목이 비어 있어요</p>
  <p class="toss-sub" style="margin-top:6px;">
    위 <b>➕ 관심 종목 추가</b> 에서 분석할 종목을 추가해 보세요.
    삼성전자, AAPL 같이 이름으로 검색할 수 있습니다.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )
    render_disclaimer()
    st.stop()


col_left, col_right = st.columns([3, 1])
col_left.markdown(f"### 분석 대상 {len(watched)}개 종목")
with col_right:
    refresh = st.button("🔄 다시 계산", type="secondary", use_container_width=True)
if refresh:
    _fetch.clear()
    st.rerun()

# ── 시그널 평가 ──────────────────────────────────────────
results: list[dict] = []
progress = st.progress(0.0, text="시그널 평가 중...")
for i, sym in enumerate(watched, start=1):
    df = _fetch(sym)
    hits = search_symbols(sym, limit=1)
    name_kr = (hits[0].name_kr or hits[0].name) if hits else sym
    if df.empty or len(df) < 60:
        results.append({
            "code": sym, "name": name_kr, "score": None,
            "action": "—", "reason": "데이터가 부족해요 (60일 미만)",
            "df": df,
        })
    else:
        try:
            sig = evaluate_and_persist(sym, df)
            top = sorted(
                ((n, c["score"], c["reason"]) for n, c in sig.components.items() if c["score"] != 0),
                key=lambda x: abs(x[1]),
                reverse=True,
            )[:3]
            reason = " · ".join(f"{n} {s:+d}" for n, s, _ in top) or "전 항목 중립"
            results.append({
                "code": sym, "name": name_kr, "score": sig.score,
                "action": sig.action, "reason": reason, "df": df,
            })
        except Exception as e:
            results.append({
                "code": sym, "name": name_kr, "score": None,
                "action": "—", "reason": f"오류: {e}", "df": df,
            })
    progress.progress(i / len(watched), text=f"{name_kr} ({i}/{len(watched)})")
progress.empty()

# ── 카운트 카드 ──────────────────────────────────────────
buy_n = sum(1 for r in results if r["action"] == "BUY")
sell_n = sum(1 for r in results if r["action"] == "SELL")
hold_n = sum(1 for r in results if r["action"] == "HOLD")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f"""
<div class="toss-card-tight">
  <p class="toss-label">매수 후보 (+8 이상)</p>
  <p class="toss-value-md toss-up">{buy_n}개</p>
</div>
""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
<div class="toss-card-tight">
  <p class="toss-label">매도 후보 (-3 이하)</p>
  <p class="toss-value-md toss-down">{sell_n}개</p>
</div>
""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""
<div class="toss-card-tight">
  <p class="toss-label">보류</p>
  <p class="toss-value-md toss-neutral">{hold_n}개</p>
</div>
""",
        unsafe_allow_html=True,
    )


# ── LLM 코멘트 캐시 ──────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _llm_comment(sym: str, name: str, action: str, score: int) -> str | None:
    df_x = _fetch(sym)
    if df_x.empty:
        return None
    try:
        sig = eval_signal_only(sym, df_x)
        return generate_signal_comment(sym, name, sig.action, sig.score, sig.components)
    except Exception:
        return None


_llm_on = llm_available()

# ── 매수 후보 카드 ───────────────────────────────────────
buys = sorted(
    [r for r in results if r["action"] == "BUY"],
    key=lambda r: r["score"],
    reverse=True,
)
if buys:
    st.markdown("### 🟢 매수 후보")
    for r in buys:
        comment = None
        if _llm_on:
            comment = _llm_comment(r["code"], r["name"], r["action"], r["score"])
        if not comment:
            comment = f"📐 점수 근거: {r['reason']}"
        recommendation_card(
            name=r["name"], code=r["code"], score=r["score"],
            comment=comment, action="buy", extra=f"종목코드 {r['code']}",
        )

# ── 매도 후보 카드 ───────────────────────────────────────
sells = sorted(
    [r for r in results if r["action"] == "SELL"],
    key=lambda r: r["score"],
)
if sells:
    st.markdown("### 🔴 매도 후보")
    for r in sells:
        comment = None
        if _llm_on:
            comment = _llm_comment(r["code"], r["name"], r["action"], r["score"])
        if not comment:
            comment = f"📐 점수 근거: {r['reason']}"
        recommendation_card(
            name=r["name"], code=r["code"], score=r["score"],
            comment=comment, action="sell", extra=f"종목코드 {r['code']}",
        )

# ── 보류 / 데이터 부족 ────────────────────────────────────
others = [r for r in results if r["action"] in ("HOLD", "—")]
if others:
    with st.expander(f"⚪ 보류·데이터 부족 ({len(others)}개)", expanded=False):
        rows = [
            {
                "종목": f"{r['name']} ({r['code']})",
                "점수": f"{r['score']:+d}" if r['score'] is not None else "—",
                "이유": r["reason"],
            }
            for r in others
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.caption(
    "📐 10가지 지표 종합 점수 — RSI · MACD · 이동평균(20/60/200) · 5일 과열 · 거래량 · OBV. "
    "AI 코멘트는 Gemini 가 자동 생성."
)

render_disclaimer()
