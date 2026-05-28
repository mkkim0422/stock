"""🎯 오늘의 추천 — 시장 전체 스캔 + 뉴스 이슈 + 포지션 사이징 (토스 스타일)."""
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
from src.collectors.kr import top_market_cap_kr
from src.collectors.mock import MockCollector
from src.collectors.news import fetch_headlines
from src.llm import analyze_news_for_stock, generate_signal_comment
from src.llm import is_available as llm_available
from src.paper.performance import evaluate as _eval_portfolio
from src.paper.portfolio import get_position
from src.paper.sizing import suggest_buy, suggest_sell
from src.signals import evaluate as eval_signal_only
from src.signals import evaluate_and_persist
from src.storage import apply_migrations
from src.symbols import search_symbols
from src.symbols.watchlist import add, list_all, remove
from src.ui.components import (
    inject_css,
    render_disclaimer,
    render_sidebar,
)

st.set_page_config(page_title="오늘의 추천 · swing-advisor", page_icon="🎯", layout="wide")

inject_css()
apply_migrations()
render_sidebar()

st.markdown("## 🎯 오늘의 추천")
st.caption(
    "한국 시가총액 상위 종목을 10가지 기술 지표로 자동 분석하고, "
    "상위 후보에는 **오늘자 뉴스 이슈**까지 LLM 으로 종합 평가해드려요. "
    "참고용이며 매매 권유가 아닙니다."
)


# ─── 데이터 helpers ──────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _fetch_one(symbol: str, days: int = 250) -> pd.DataFrame:
    if os.environ.get("USE_MOCK") == "1":
        try:
            return MockCollector().fetch_ohlcv(
                symbol, date.today() - timedelta(days=days), date.today()
            )
        except Exception:
            return pd.DataFrame()
    try:
        return fetch_ohlcv(symbol, date.today() - timedelta(days=days), date.today())
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def _top_kr(n: int) -> list[dict]:
    return top_market_cap_kr(n)


@st.cache_data(ttl=900, show_spinner=False)
def _news(query: str, limit: int = 5) -> list[dict]:
    return fetch_headlines(query, limit=limit)


@st.cache_data(ttl=900, show_spinner=False)
def _llm_signal(sym: str, name: str, action: str, score: int) -> str | None:
    df = _fetch_one(sym)
    if df.empty:
        return None
    try:
        sig = eval_signal_only(sym, df)
        return generate_signal_comment(sym, name, sig.action, sig.score, sig.components)
    except Exception:
        return None


@st.cache_data(ttl=900, show_spinner=False)
def _llm_issue(sym: str, name: str, action: str, score: int) -> tuple[str | None, list[dict]]:
    heads = _news(name, limit=5)
    if not heads:
        return None, []
    return analyze_news_for_stock(name, sym, action, score, heads), heads


def _evaluate_one(sym: str, name: str) -> dict:
    df = _fetch_one(sym)
    if df.empty:
        return {"code": sym, "name": name, "score": None, "action": "—",
                "price": None, "reason": "데이터 못 가져옴"}
    if len(df) < 60:
        return {"code": sym, "name": name, "score": None, "action": "—",
                "price": float(df.iloc[-1]["close"]),
                "reason": f"히스토리 부족 ({len(df)}일)"}
    try:
        sig = evaluate_and_persist(sym, df)
        top = sorted(
            ((n_, c["score"], c["reason"]) for n_, c in sig.components.items() if c["score"] != 0),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:3]
        reason = " · ".join(f"{n_} {s:+d}" for n_, s, _ in top) or "전 항목 중립"
        return {
            "code": sym, "name": name, "score": sig.score, "action": sig.action,
            "price": float(df.iloc[-1]["close"]), "reason": reason,
        }
    except Exception as e:
        return {"code": sym, "name": name, "score": None, "action": "—",
                "price": None, "reason": f"분석 오류: {e}"}


# ─── 카드 렌더링 ─────────────────────────────────────────
def _market_label(code: str) -> str:
    return "KR" if code.isdigit() and len(code) == 6 else "US"


def _render_card(r: dict, kind: str, llm_pack: tuple | None) -> None:
    """kind: 'buy' | 'sell'"""
    is_buy = kind == "buy"
    score = r["score"]
    name = r["name"] or r["code"]
    code = r["code"]
    market = _market_label(code)
    price = r.get("price")

    badge_text = "매수 후보" if is_buy else "매도 후보"
    badge_cls = "toss-badge-buy" if is_buy else "toss-badge-sell"
    score_cls = "toss-up" if is_buy else "toss-down"
    score_str = f"+{score}" if score and score > 0 else str(score)

    # 포지션 사이징
    sizing_html = ""
    if is_buy and price:
        e = _eval_portfolio()
        cash = float(e["cash_krw"])
        sug = suggest_buy(
            score=score, price=price, cash_available_krw=cash,
            fx_rate_krw_per_usd=float(e["fx_rate"]), market=market,
        )
        if sug:
            sizing_html = (
                f'<div class="toss-card-tight" style="background:#F1F7FF; border-color:#D6E6FF; margin-top:10px;">'
                f'<p class="toss-label" style="color:#1B64DA;">💰 추천 수량</p>'
                f'<p class="toss-value-md" style="color:#1B64DA;">{sug["qty"]:,} 주</p>'
                f'<p class="toss-sub" style="margin-top:4px;">'
                f'약 ₩{sug["notional_krw"]:,.0f} · 가용 현금의 {sug["pct_of_cash"]:.0f}%'
                f'</p></div>'
            )
    elif (not is_buy) and price:
        pos = get_position(code)
        held = pos[0] if pos else 0
        if held > 0:
            sug = suggest_sell(score=score, holding_qty=held)
            if sug:
                sizing_html = (
                    f'<div class="toss-card-tight" style="background:#FEF2F2; border-color:#FECACA; margin-top:10px;">'
                    f'<p class="toss-label" style="color:#DC2626;">💸 추천 매도 수량</p>'
                    f'<p class="toss-value-md" style="color:#DC2626;">{sug["qty"]:,} 주</p>'
                    f'<p class="toss-sub" style="margin-top:4px;">'
                    f'보유 {held:,}주 중 {sug["pct_of_holding"]:.0f}%'
                    f'</p></div>'
                )
        else:
            sizing_html = (
                '<p class="toss-sub" style="margin-top:8px;">현재 보유 없음 — 매도 대상 없음.</p>'
            )

    # 시그널 코멘트
    signal_comment = None
    issue_comment = None
    headlines: list[dict] = []
    if llm_pack:
        signal_comment, (issue_comment, headlines) = llm_pack
    comment = signal_comment or f"📐 점수 근거: {r['reason']}"
    issue_block = ""
    if issue_comment:
        head_lines = ""
        if headlines:
            head_lines = '<ul style="margin:6px 0 0 16px; padding:0; font-size:12px; color:#6B7684;">'
            for h in headlines[:3]:
                head_lines += f'<li>{h["title"]}</li>'
            head_lines += "</ul>"
        issue_block = (
            f'<div style="margin-top:10px; padding:10px 12px; background:#FFFBEB; '
            f'border:1px solid #FDE68A; border-radius:10px;">'
            f'<p style="font-size:12px; color:#92400E; font-weight:600; margin:0;">📰 오늘자 이슈 분석</p>'
            f'<p style="font-size:13px; color:#191F28; margin-top:4px; line-height:1.5;">{issue_comment}</p>'
            f'{head_lines}'
            f'</div>'
        )

    price_str = f"₩{price:,.0f}" if price and market == "KR" else (f"${price:,.2f}" if price else "—")
    html = f"""
<div class="toss-rec-card">
  <div class="toss-rec-head">
    <div>
      <span class="toss-rec-name">{name}</span>
      <span class="toss-rec-code">{code} · 현재가 {price_str}</span>
    </div>
    <div>
      <span class="toss-rec-score {score_cls}">{score_str}점</span>
    </div>
  </div>
  <div><span class="toss-badge {badge_cls}">{badge_text}</span></div>
  <p class="toss-rec-comment">{comment}</p>
  {issue_block}
  {sizing_html}
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


def _render_results(results: list[dict], title: str, llm_top_n: int = 10) -> None:
    buy_n = sum(1 for r in results if r["action"] == "BUY")
    sell_n = sum(1 for r in results if r["action"] == "SELL")
    hold_n = sum(1 for r in results if r["action"] == "HOLD")
    fail_n = sum(1 for r in results if r["action"] == "—")

    st.markdown(f"### {title}")
    c1, c2, c3, c4 = st.columns(4)
    for col, (lab, val, cls) in zip(
        (c1, c2, c3, c4),
        (("매수 후보", buy_n, "toss-up"),
         ("매도 후보", sell_n, "toss-down"),
         ("보류", hold_n, "toss-neutral"),
         ("분석 실패", fail_n, "")),
        strict=True,
    ):
        with col:
            st.markdown(
                f"<div class='toss-card-tight'><p class='toss-label'>{lab}</p>"
                f"<p class='toss-value-md {cls}'>{val}개</p></div>",
                unsafe_allow_html=True,
            )

    llm_on = llm_available()
    buys = sorted([r for r in results if r["action"] == "BUY"],
                  key=lambda r: r["score"], reverse=True)
    sells = sorted([r for r in results if r["action"] == "SELL"],
                   key=lambda r: r["score"])

    if buys:
        st.markdown(f"#### 🟢 매수 후보 {len(buys)}개 (점수 높은 순)")
        with st.spinner("상위 종목 뉴스 + LLM 이슈 분석 중..." if llm_on else "표시 중..."):
            for i, r in enumerate(buys):
                pack = None
                if llm_on and i < llm_top_n:
                    sc = _llm_signal(r["code"], r["name"], r["action"], r["score"])
                    iss = _llm_issue(r["code"], r["name"], r["action"], r["score"])
                    pack = (sc, iss)
                _render_card(r, "buy", pack)

    if sells:
        st.markdown(f"#### 🔴 매도 후보 {len(sells)}개 (점수 낮은 순)")
        with st.spinner("상위 종목 뉴스 + LLM 이슈 분석 중..." if llm_on else "표시 중..."):
            for i, r in enumerate(sells):
                pack = None
                if llm_on and i < llm_top_n:
                    sc = _llm_signal(r["code"], r["name"], r["action"], r["score"])
                    iss = _llm_issue(r["code"], r["name"], r["action"], r["score"])
                    pack = (sc, iss)
                _render_card(r, "sell", pack)

    others = [r for r in results if r["action"] in ("HOLD", "—")]
    if others:
        with st.expander(f"⚪ 보류·실패 ({len(others)}개)", expanded=False):
            rows = [{
                "종목": f"{r['name']} ({r['code']})",
                "점수": f"{r['score']:+d}" if r["score"] is not None else "—",
                "이유": r["reason"],
            } for r in others]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ─── ① 시장 전체 스캔 ────────────────────────────────────
st.markdown("### 🔥 시장 전체에서 골라보기")
c_left, c_right = st.columns([2, 1])
with c_left:
    st.caption(
        "한국 시가총액 상위 종목을 자동 분석. 매수/매도 후보 **상위 10개**에 대해서는 "
        "오늘자 뉴스를 검색해 LLM 이 이슈를 종합 평가하고, **추천 매수/매도 수량**도 표시해드려요."
    )
with c_right:
    top_n = st.selectbox(
        "분석 범위",
        options=[30, 50, 100, 200, 500],
        index=2,
        format_func=lambda n: f"시총 TOP {n}",
        label_visibility="collapsed",
    )

run_scan = st.button("🔄 시장 분석 실행", type="primary", use_container_width=True)

if run_scan:
    with st.spinner("시가총액 상위 종목 목록 가져오는 중..."):
        candidates = _top_kr(top_n)

    if not candidates:
        st.error(
            "시가총액 상위 종목 목록을 가져오지 못했어요. 잠시 후 다시 시도해 주세요. "
            "(데이터 소스 일시 장애일 수 있어요)"
        )
    else:
        st.success(f"{len(candidates)}개 종목 분석 시작 — {top_n}개 기준 약 {len(candidates)*2//60+1}분 예상.")
        scan_results: list[dict] = []
        prog = st.progress(0.0, text="분석 중...")
        for i, c in enumerate(candidates, start=1):
            r = _evaluate_one(c["symbol"], c["name"] or c["symbol"])
            scan_results.append(r)
            if i % 5 == 0 or i == len(candidates):
                prog.progress(i / len(candidates), text=f"{c['name']} ({i}/{len(candidates)})")
        prog.empty()
        st.session_state["scan_results"] = scan_results
        st.session_state["scan_meta"] = {
            "top_n": top_n,
            "count": len(candidates),
        }

if "scan_results" in st.session_state:
    _render_results(
        st.session_state["scan_results"],
        title=f"📊 시장 분석 결과 (TOP {st.session_state.get('scan_meta', {}).get('top_n', '?')})",
        llm_top_n=10,
    )
else:
    st.markdown(
        """
<div class="toss-card" style="background:#F1F7FF; border-color:#D6E6FF;">
  <p class="toss-value-md" style="color:#1B64DA;">아직 분석 안 했어요</p>
  <p class="toss-sub" style="margin-top:6px;">
    위 <b>🔄 시장 분석 실행</b> 버튼을 누르면 시가총액 상위 종목을 자동으로
    훑어 매수·매도 후보를 골라드려요. 상위 10개는 오늘자 뉴스 이슈와 추천 수량도 함께.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )


# ─── ② 내 관심 종목 ──────────────────────────────────────
st.markdown("---")
st.markdown("### ⭐ 내 관심 종목")
st.caption("특정 종목만 별도로 추적하고 싶을 때.")

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
if watched:
    if st.button("🔄 관심 종목 다시 계산", type="secondary"):
        _fetch_one.clear()

    watch_results: list[dict] = []
    prog = st.progress(0.0, text="관심 종목 분석 중...")
    for i, sym in enumerate(watched, start=1):
        hits = search_symbols(sym, limit=1)
        name = (hits[0].name_kr or hits[0].name) if hits else sym
        watch_results.append(_evaluate_one(sym, name))
        prog.progress(i / len(watched), text=f"{name} ({i}/{len(watched)})")
    prog.empty()
    _render_results(watch_results, title="📋 관심 종목 분석", llm_top_n=20)

st.caption(
    "📐 10가지 지표 종합 점수 · 📰 Google News RSS (무료) · 🤖 Gemini LLM. "
    "추천 수량은 가용 현금/보유 수량을 점수 강도(매수 +8↑ 4–10%, 매도 -3↓ 30–100%)에 따라 배분."
)

render_disclaimer()
