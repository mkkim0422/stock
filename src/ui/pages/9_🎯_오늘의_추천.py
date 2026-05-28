"""🎯 오늘의 추천 — 기술 + 펀더멘털 + 거시 + 뉴스 종합 분석 (토스 스타일)."""
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
from src.collectors.fundamentals import get as get_fund
from src.collectors.kr import top_market_cap_kr
from src.collectors.macro import context_snapshot
from src.collectors.mock import MockCollector
from src.collectors.news import fetch_headlines
from src.llm import (
    analyze_news_for_stock,
    is_available as llm_available,
    score_news_sentiment,
)
from src.paper.performance import evaluate as _eval_portfolio
from src.paper.portfolio import get_position
from src.paper.sizing import suggest_buy, suggest_sell
from src.signals import evaluate as eval_signal
from src.signals.comprehensive import evaluate_composite
from src.storage import apply_migrations
from src.symbols import search_symbols
from src.symbols.watchlist import add, list_all, remove
from src.ui.components import inject_css, render_disclaimer, render_sidebar

st.set_page_config(page_title="오늘의 추천 · swing-advisor", page_icon="🎯", layout="wide")

inject_css()
apply_migrations()
render_sidebar()

st.markdown("## 🎯 오늘의 추천")
st.caption(
    "한국 시가총액 상위 종목을 **기술·펀더멘털·거시·뉴스 4축**으로 자동 분석. "
    "참고용이며 매매 권유가 아닙니다."
)


# ─── 거시 환경 한 줄 표시 ───────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def _ctx() -> dict:
    return context_snapshot()


with st.expander("🌐 오늘의 거시 환경", expanded=False):
    ctx = _ctx()
    cols = st.columns(len(ctx))
    for col, (name, c) in zip(cols, ctx.items(), strict=True):
        with col:
            val = f"{c['value']:,.2f}" if c["value"] else "—"
            ret5 = c.get("ret_5d")
            sub = f"{ret5:+.2f}% (5일)" if ret5 is not None else ""
            cls = ""
            if ret5 is not None:
                cls = "toss-up" if ret5 >= 0 else "toss-down"
            st.markdown(
                f"<div class='toss-card-tight'><p class='toss-label'>{name}</p>"
                f"<p class='toss-value-md'>{val}</p>"
                f"<p class='toss-sub {cls}'>{sub}</p></div>",
                unsafe_allow_html=True,
            )


# ─── helpers ──────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _fetch_ohlcv(symbol: str, days: int = 250) -> pd.DataFrame:
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
def _llm_sentiment(name: str, sym: str) -> tuple[int, str] | None:
    heads = _news(name, limit=5)
    if not heads:
        return None
    return score_news_sentiment(name, sym, heads)


@st.cache_data(ttl=900, show_spinner=False)
def _llm_issue_text(sym: str, name: str, action: str, score: int) -> tuple[str | None, list[dict]]:
    heads = _news(name, limit=5)
    if not heads:
        return None, []
    return analyze_news_for_stock(name, sym, action, score, heads), heads


def _technical_only(sym: str, name: str) -> dict:
    """1차 빠른 스크리닝 — 기술 점수만 (펀더/거시/뉴스 X). 500개 스캔용."""
    df = _fetch_ohlcv(sym)
    if df.empty:
        return {"code": sym, "name": name, "ok": False, "reason": "데이터 못 가져옴"}
    if len(df) < 60:
        return {"code": sym, "name": name, "ok": False, "reason": f"히스토리 부족 ({len(df)}일)"}
    try:
        sig = eval_signal(sym, df)
        return {
            "code": sym, "name": name, "ok": True,
            "tech_score": sig.score, "tech_action": sig.action, "tech_sig": sig,
            "price": float(df.iloc[-1]["close"]),
        }
    except Exception as e:
        return {"code": sym, "name": name, "ok": False, "reason": f"분석 오류: {e}"}


def _comprehensive(r: dict, with_llm: bool) -> dict:
    """기술 결과에 펀더멘털 + 거시 + (선택) LLM 센티먼트 추가."""
    sym = r["code"]
    name = r["name"]
    fund = get_fund(sym)
    sent_score, sent_reason = 0, ""
    if with_llm:
        s = _llm_sentiment(name, sym)
        if s:
            sent_score, sent_reason = s
    comp = evaluate_composite(
        symbol=sym,
        technical=r["tech_sig"],
        fundamental=fund,
        sentiment_score=sent_score,
        sentiment_reason=sent_reason,
    )
    return {**r, "fund": fund, "composite": comp}


# ─── 카드 ──────────────────────────────────────────────
def _market_label(code: str) -> str:
    return "KR" if code.isdigit() and len(code) == 6 else "US"


def _comp_badge(action: str, rank: int | None = None, is_buy: bool = True) -> str:
    """순위가 있으면 순위 배지 우선. 강한 시그널은 강조 배지 추가."""
    badges: list[str] = []
    if rank is not None:
        # 섹션 안에서의 순위 — 매수/매도 컨텍스트에 맞게
        side = "매수" if is_buy else "매도"
        klass = "toss-badge-buy" if is_buy else "toss-badge-sell"
        badges.append(f"<span class='toss-badge {klass}'>{rank}순위 {side} 후보</span>")
    if action == "STRONG_BUY":
        badges.append("<span class='toss-badge toss-badge-buy'>🔥 강한 시그널</span>")
    elif action == "STRONG_SELL":
        badges.append("<span class='toss-badge toss-badge-sell'>💥 강한 시그널</span>")
    elif action == "HOLD" and rank is None:
        badges.append("<span class='toss-badge toss-badge-hold'>중립 구간</span>")
    return " ".join(badges)


def _render_card(r: dict, is_buy: bool, rank: int | None = None) -> None:
    comp = r["composite"]
    fund = r.get("fund") or {}
    code = r["code"]
    name = r["name"] or code
    price = r.get("price")
    market = _market_label(code)
    score_cls = "toss-up" if is_buy else "toss-down"
    score_str = f"+{comp.total}" if comp.total > 0 else str(comp.total)

    # 펀더멘털 요약
    per = fund.get("per")
    pbr = fund.get("pbr")
    cap = fund.get("market_cap") or 0
    industry = fund.get("industry") or fund.get("sector") or ""
    fund_line_parts = []
    if industry:
        fund_line_parts.append(industry)
    if cap >= 1e12:
        fund_line_parts.append(f"시총 {cap/1e12:.1f}조")
    elif cap > 0:
        fund_line_parts.append(f"시총 {cap/1e8:,.0f}억")
    if per is not None and per > 0:
        fund_line_parts.append(f"PER {per:.1f}")
    if pbr is not None and pbr > 0:
        fund_line_parts.append(f"PBR {pbr:.2f}")
    fund_line = " · ".join(fund_line_parts) if fund_line_parts else "—"

    # 포지션 사이징
    sizing_html = ""
    if is_buy and price:
        e = _eval_portfolio()
        sug = suggest_buy(
            score=max(8, comp.total),  # composite을 buy 점수로 변환
            price=price, cash_available_krw=float(e["cash_krw"]),
            fx_rate_krw_per_usd=float(e["fx_rate"]), market=market,
        )
        if sug:
            sizing_html = (
                f'<div class="toss-card-tight" style="background:#F1F7FF; border-color:#D6E6FF; margin-top:10px;">'
                f'<p class="toss-label" style="color:#1B64DA;">💰 추천 매수 수량</p>'
                f'<p class="toss-value-md" style="color:#1B64DA;">{sug["qty"]:,} 주</p>'
                f'<p class="toss-sub" style="margin-top:4px;">'
                f'약 ₩{sug["notional_krw"]:,.0f} · 가용 현금의 {sug["pct_of_cash"]:.0f}%'
                f'</p></div>'
            )
    elif not is_buy and price:
        pos = get_position(code)
        held = pos[0] if pos else 0
        if held > 0:
            sug = suggest_sell(score=min(-3, comp.total), holding_qty=held)
            if sug:
                sizing_html = (
                    f'<div class="toss-card-tight" style="background:#FEF2F2; border-color:#FECACA; margin-top:10px;">'
                    f'<p class="toss-label" style="color:#DC2626;">💸 추천 매도 수량</p>'
                    f'<p class="toss-value-md" style="color:#DC2626;">{sug["qty"]:,} 주</p>'
                    f'<p class="toss-sub" style="margin-top:4px;">'
                    f'보유 {held:,}주 중 {sug["pct_of_holding"]:.0f}%</p></div>'
                )
        else:
            sizing_html = '<p class="toss-sub" style="margin-top:8px;">보유 없음 — 매도 대상 아님.</p>'

    # 점수 분해
    breakdown_rows = ""
    for cat, items in comp.breakdown.items():
        if not items:
            continue
        sub = sum(it["score"] for it in items)
        sub_cls = "toss-up" if sub > 0 else ("toss-down" if sub < 0 else "toss-neutral")
        reasons = "<br/>".join(
            f"&nbsp;&nbsp;• {it['name']} <b style='color:{'#FF4040' if it['score']>0 else '#3282F6' if it['score']<0 else '#8B95A1'}'>{it['score']:+d}</b> · {it['reason']}"
            for it in items if it["score"] != 0
        ) or "&nbsp;&nbsp;• 모두 중립"
        breakdown_rows += (
            f"<div style='margin-top:8px;'>"
            f"<b style='font-size:13px;'>{cat}</b> "
            f"<span class='{sub_cls}' style='font-weight:700;'>{sub:+d}</span>"
            f"<div style='font-size:12px; color:#6B7684; margin-top:2px; line-height:1.7;'>{reasons}</div>"
            f"</div>"
        )

    # 뉴스 이슈 텍스트
    issue_html = ""
    issue_text, heads = _llm_issue_text(code, name, comp.action, comp.total)
    if issue_text:
        head_lines = ""
        if heads:
            head_lines = '<ul style="margin:6px 0 0 16px; padding:0; font-size:12px; color:#6B7684;">'
            for h in heads[:3]:
                head_lines += f'<li>{h["title"]}</li>'
            head_lines += "</ul>"
        issue_html = (
            f'<div style="margin-top:10px; padding:10px 12px; background:#FFFBEB; '
            f'border:1px solid #FDE68A; border-radius:10px;">'
            f'<p style="font-size:12px; color:#92400E; font-weight:600; margin:0;">📰 오늘자 뉴스 이슈</p>'
            f'<p style="font-size:13px; color:#191F28; margin-top:4px; line-height:1.5;">{issue_text}</p>'
            f'{head_lines}</div>'
        )

    price_str = f"₩{price:,.0f}" if price and market == "KR" else (f"${price:,.2f}" if price else "—")
    head_html = f"""
<div class="toss-rec-card">
  <div class="toss-rec-head">
    <div>
      <span class="toss-rec-name">{name}</span>
      <span class="toss-rec-code">{code} · {price_str}</span>
    </div>
    <div><span class="toss-rec-score {score_cls}">{score_str}점</span></div>
  </div>
  <div>{_comp_badge(comp.action, rank=rank, is_buy=is_buy)}</div>
  <p class="toss-sub" style="margin-top:6px;">{fund_line}</p>
  <div style="margin-top:8px; padding:10px 12px; background:#F9FAFB; border-radius:10px;">
    {breakdown_rows}
  </div>
  {issue_html}
  {sizing_html}
</div>
"""
    st.markdown(head_html, unsafe_allow_html=True)


# ─── 시장 전체 스캔 ─────────────────────────────────────
st.markdown("### 🔥 시장 전체 분석")
c_left, c_right = st.columns([2, 1])
with c_left:
    st.caption(
        "1단계: 시총 상위 N개 종목 기술 분석으로 1차 스크리닝 → "
        "2단계: 후보 상위 20개에 펀더멘털·거시·뉴스 LLM 종합 평가 추가."
    )
with c_right:
    top_n = st.selectbox(
        "분석 범위",
        options=[30, 50, 100, 200, 500],
        index=2,
        format_func=lambda n: f"시총 TOP {n}",
        label_visibility="collapsed",
    )

run = st.button("🔄 시장 분석 실행", type="primary", use_container_width=True)

if run:
    with st.spinner("시총 상위 목록 가져오는 중..."):
        candidates = _top_kr(top_n)
    if not candidates:
        st.error("시총 목록 수신 실패. 잠시 후 다시 시도해 주세요.")
    else:
        st.success(f"{len(candidates)}개 종목 분석 시작 (예상 {len(candidates)*2//60+1}분).")

        # 1단계: 기술 점수 — 모든 종목
        scored: list[dict] = []
        prog = st.progress(0.0, text="1단계: 기술 분석 중...")
        for i, c in enumerate(candidates, start=1):
            r = _technical_only(c["symbol"], c["name"] or c["symbol"])
            scored.append(r)
            if i % 5 == 0 or i == len(candidates):
                prog.progress(i / len(candidates), text=f"{c['name']} ({i}/{len(candidates)})")
        prog.empty()

        # 데이터 OK 인 종목 모두 — 액션 무관
        ok = [r for r in scored if r.get("ok")]

        # 2단계: 종합 점수 (펀더+거시) — 전체 OK 종목에 적용 (캐시 빠름)
        prog2 = st.progress(0.0, text="2단계: 펀더멘털·거시 평가 중...")
        full_results: list[dict] = []
        for i, r in enumerate(ok, start=1):
            full_results.append(_comprehensive(r, with_llm=False))
            if i % 5 == 0 or i == len(ok):
                prog2.progress(i / len(ok), text=f"{r['name']} ({i}/{len(ok)})")
        prog2.empty()

        # 종합 점수로 정렬
        full_results.sort(key=lambda r: r["composite"].total, reverse=True)

        # 3단계: 상위 10 + 하위 10 (총 20개) 에 LLM 뉴스 분석 추가
        llm_on = llm_available()
        if llm_on:
            top_for_llm = full_results[:10] + full_results[-10:]
            prog3 = st.progress(0.0, text="3단계: 뉴스 + LLM 이슈 분석 (상위·하위 20개)...")
            for i, r in enumerate(top_for_llm, start=1):
                idx = full_results.index(r)
                full_results[idx] = _comprehensive(r, with_llm=True)
                prog3.progress(i / len(top_for_llm), text=f"{r['name']} ({i}/{len(top_for_llm)})")
            prog3.empty()

        not_ok = [r for r in scored if not r.get("ok")]
        st.session_state["scan_full"] = full_results
        st.session_state["scan_others"] = not_ok
        st.session_state["scan_meta"] = {"top_n": top_n, "analyzed": len(full_results)}


if "scan_full" in st.session_state:
    results: list[dict] = st.session_state["scan_full"]  # 이미 composite.total 내림차순
    meta = st.session_state.get("scan_meta", {})
    others = st.session_state.get("scan_others", [])

    # 상위 10개 = 추천 매수 / 하위 10개 = 추천 매도 (점수 부호 무관 — 항상 표시)
    top_buys = [r for r in results[:10] if r["composite"].total > -3]
    top_sells = [r for r in list(reversed(results))[:10] if r["composite"].total < 3]
    middle = [r for r in results if r not in top_buys and r not in top_sells]

    # 라벨 분포 카운트
    sb = sum(1 for r in results if r["composite"].action == "STRONG_BUY")
    b  = sum(1 for r in results if r["composite"].action == "BUY")
    s  = sum(1 for r in results if r["composite"].action == "SELL")
    ss = sum(1 for r in results if r["composite"].action == "STRONG_SELL")

    st.markdown(f"### 📊 종합 분석 결과 — 시총 TOP {meta.get('top_n')}")
    c1, c2, c3, c4 = st.columns(4)
    for col, (lab, val, cls) in zip(
        (c1, c2, c3, c4),
        (("강한 매수", sb, "toss-up"),
         ("매수", b, "toss-up"),
         ("매도", s, "toss-down"),
         ("강한 매도", ss, "toss-down")),
        strict=True,
    ):
        with col:
            st.markdown(
                f"<div class='toss-card-tight'><p class='toss-label'>{lab}</p>"
                f"<p class='toss-value-md {cls}'>{val}개</p></div>",
                unsafe_allow_html=True,
            )

    st.caption(
        f"분석 완료 {len(results)}개 · 데이터 부족 {len(others)}개. "
        "임계값(BUY ≥+6 / SELL ≤-3)에 도달 못한 종목도 **상대 점수 상위**라면 아래 표시."
    )

    if top_buys:
        st.markdown(f"#### 🟢 오늘의 매수 후보 TOP {len(top_buys)} (종합 점수 높은 순)")
        for i, r in enumerate(top_buys, start=1):
            _render_card(r, is_buy=True, rank=i)
    if top_sells:
        st.markdown(f"#### 🔴 오늘의 매도/주의 TOP {len(top_sells)} (종합 점수 낮은 순)")
        for i, r in enumerate(top_sells, start=1):
            _render_card(r, is_buy=False, rank=i)

    with st.expander(f"⚪ 중간 점수 종목 ({len(middle)}개)", expanded=False):
        rows = [{
            "종목": f"{r['name']} ({r['code']})",
            "종합점수": f"{r['composite'].total:+d}",
            "액션": r["composite"].action,
            "기술": f"{r['composite'].technical:+d}",
            "펀더": f"{r['composite'].fundamental:+d}",
            "거시": f"{r['composite'].macro:+d}",
        } for r in middle]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if others:
        with st.expander(f"❌ 데이터 부족·실패 ({len(others)}개)", expanded=False):
            rows2 = [{
                "종목": f"{r['name']} ({r['code']})",
                "사유": r.get("reason", "—"),
            } for r in others]
            st.dataframe(pd.DataFrame(rows2), use_container_width=True, hide_index=True)
else:
    st.markdown(
        """
<div class="toss-card" style="background:#F1F7FF; border-color:#D6E6FF;">
  <p class="toss-value-md" style="color:#1B64DA;">아직 분석 안 했어요</p>
  <p class="toss-sub" style="margin-top:6px;">
    위 <b>🔄 시장 분석 실행</b> 버튼을 누르면 자동 스캐닝이 시작됩니다.<br/>
    1단계 — 시총 N개 종목 기술 스크리닝 (빠름)<br/>
    2단계 — 1차 통과 종목 중 상위 20개에 펀더멘털 + 거시 + 뉴스 LLM 종합 평가
  </p>
</div>
""",
        unsafe_allow_html=True,
    )


# ─── 관심 종목 ──────────────────────────────────────────
st.markdown("---")
st.markdown("### ⭐ 내 관심 종목")
with st.expander("➕ 관심 종목 추가·관리", expanded=False):
    c1, c2 = st.columns([2, 1])
    with c1:
        q = st.text_input("종목 검색", placeholder="삼성전자, 005930, AAPL", key="watch_q")
        if q:
            hits = search_symbols(q, limit=5)
            for h in hits:
                if st.button(f"➕ {h.symbol} · {h.name_kr or h.name}", key=f"add_{h.symbol}", type="secondary"):
                    add(h.symbol)
                    st.success(f"{h.symbol} 추가됨")
                    st.rerun()
    with c2:
        st.caption(f"관심 종목 {len(list_all())}개")
        for s in list_all():
            cc1, cc2 = st.columns([3, 1])
            cc1.write(s)
            if cc2.button("❌", key=f"rm_{s}"):
                remove(s)
                st.rerun()


watched = list_all()
if watched:
    if st.button("🔄 관심 종목 종합 분석", type="secondary"):
        _fetch_ohlcv.clear()

    watch_full: list[dict] = []
    prog = st.progress(0.0, text="관심 종목 분석 중...")
    llm_on = llm_available()
    for i, sym in enumerate(watched, start=1):
        hits = search_symbols(sym, limit=1)
        name = (hits[0].name_kr or hits[0].name) if hits else sym
        r = _technical_only(sym, name)
        if r.get("ok"):
            watch_full.append(_comprehensive(r, with_llm=llm_on))
        prog.progress(i / len(watched), text=f"{name} ({i}/{len(watched)})")
    prog.empty()

    watch_full.sort(key=lambda r: r["composite"].total, reverse=True)
    for r in watch_full:
        is_buy = r["composite"].total >= 0
        _render_card(r, is_buy=is_buy)


st.caption(
    "📐 4축 종합 점수 — 기술 ±11 / 펀더멘털 ±5 / 거시·섹터 ±3 / 뉴스 ±2 (총 ±21). "
    "강한 매수 +14↑ · 매수 +10↑ · 매도 -5↓ · 강한 매도 -10↓. "
    "데이터: FinanceDataReader · Google News RSS · Gemini LLM. 모두 무료."
)

render_disclaimer()
