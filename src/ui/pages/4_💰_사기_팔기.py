"""💰 사기 팔기 — 실시간 시세 기반 가상 매수/매도 (토스 스타일)."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[3]
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

from decimal import Decimal

import pandas as pd
import streamlit as st

from src.collectors import fetch_realtime
from src.paper.fees import calc_fee, calc_tax
from src.paper.portfolio import get_position
from src.paper.slippage import apply_slippage
from src.paper.trader import MarketClosedError, execute_order
from src.storage import apply_migrations, connect
from src.symbols import search_symbols
from src.ui.components import inject_css, render_disclaimer, render_sidebar
from src.ui.components.kpi_card import fmt_krw, fmt_usd
from src.utils.market_hours import (
    market_status,
    next_market_open,
    status_label,
)
from src.utils.timezone import now_kst

st.set_page_config(page_title="사기 팔기 · swing-advisor", page_icon="💰", layout="wide")

inject_css()
apply_migrations()
render_sidebar()

st.markdown("## 💰 사기 팔기")
st.caption(
    "가상의 돈으로 매수·매도 연습. 실거래 아니지만 **실시간 시세**로 체결돼요. "
    "실제 증권사와 똑같이 **정규장**에만 주문 가능."
)


@st.cache_data(ttl=60, show_spinner=False)
def _quote(symbol: str) -> float:
    return fetch_realtime(symbol)


left, right = st.columns([1.1, 1])

selected = None
price = None
side = "BUY"
qty = 1

with left:
    st.markdown("#### ① 어떤 종목으로 할까요?")
    q = st.text_input(
        "종목 이름 또는 코드",
        placeholder="예) 삼성전자, 005930, AAPL",
        key="trade_search",
        label_visibility="collapsed",
    )
    if q:
        with st.spinner("검색 중..."):
            hits = search_symbols(q, limit=10)
        if hits:
            labels = [
                f"{h.symbol} · {h.name_kr or h.name} ({h.market})" for h in hits
            ]
            idx = st.radio(
                "결과",
                range(len(hits)),
                format_func=lambda i: labels[i],
                label_visibility="collapsed",
            )
            selected = hits[idx]
        else:
            st.warning(f'"{q}" 결과 없음')
    else:
        st.caption("위 칸에 종목명을 입력해 보세요.")

    if selected is not None:
        try:
            with st.spinner("실시간 시세 조회..."):
                price = _quote(selected.symbol)
            unit_fmt = fmt_krw if selected.market == "KR" else fmt_usd
            st.markdown(
                f"""
<div class="toss-card-tight">
  <p class="toss-label">{selected.name_kr or selected.name} · {selected.symbol}</p>
  <p class="toss-value-md">현재가 {unit_fmt(price)}</p>
</div>
""",
                unsafe_allow_html=True,
            )
        except Exception as ex:
            st.error(f"시세 조회 실패: {ex}")
            selected = None

    if selected is not None:
        st.markdown("#### ② 사기 / 팔기 · 수량")
        side = st.radio(
            "주문 종류",
            ["BUY", "SELL"],
            horizontal=True,
            format_func=lambda s: "🟢 사기 (매수)" if s == "BUY" else "🔴 팔기 (매도)",
            label_visibility="collapsed",
        )
        qty = int(st.number_input("몇 주?", min_value=1, value=1, step=1))

with right:
    if selected is None or price is None:
        st.markdown(
            """
<div class="toss-card" style="text-align:center; padding:32px;">
  <p class="toss-label" style="font-size:14px;">👈 왼쪽에서 종목과 수량을 입력해 주세요</p>
  <p class="toss-sub" style="margin-top:8px;">주문 미리보기가 여기 나타납니다.</p>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("#### ③ 주문 미리보기")
        quote = Decimal(str(price))
        fill = apply_slippage(quote, side)
        notional = fill * Decimal(qty)
        fee = calc_fee(selected.market, notional)
        tax = calc_tax(selected.market, side, notional)
        total = notional + fee + tax if side == "BUY" else notional - fee - tax

        unit_fmt = fmt_krw if selected.market == "KR" else fmt_usd
        kind_label = "사기" if side == "BUY" else "팔기"
        total_label = "지불 금액" if side == "BUY" else "수령 금액"
        total_cls = "toss-down" if side == "BUY" else "toss-up"

        st.markdown(
            f"""
<div class="toss-card">
  <p class="toss-label">{selected.name_kr or selected.name} · {kind_label} {qty:,}주</p>
  <p class="toss-value">{unit_fmt(float(total))}</p>
  <p class="toss-sub {total_cls}">{total_label}</p>
  <hr style="border:none; border-top:1px solid #F2F4F6; margin:14px 0;"/>
  <div style="font-size:13px; color:#6B7684; line-height:1.9;">
    체결가 (슬리피지 반영) · <b style="color:#191F28;">{unit_fmt(float(fill))}</b><br/>
    거래대금 · <b style="color:#191F28;">{unit_fmt(float(notional))}</b><br/>
    수수료 · <b style="color:#191F28;">{unit_fmt(float(fee))}</b><br/>
    거래세 · <b style="color:#191F28;">{unit_fmt(float(tax))}</b>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        pos = get_position(selected.symbol)
        held = pos[0] if pos else 0
        st.caption(f"현재 보유: {held:,}주")

        now = now_kst()
        cur_status = market_status(selected.market, now)
        market_open = cur_status == "OPEN"

        if not market_open:
            nxt = next_market_open(selected.market, now)
            st.markdown(
                f"""
<div class="toss-card-tight" style="background:#FFF7ED; border-color:#FED7AA;">
  <p class="toss-label" style="color:#C2410C;">🚫 지금은 주문할 수 없어요</p>
  <p class="toss-sub" style="margin-top:4px;">
    {selected.market} 시장: <b>{status_label(cur_status)}</b><br/>
    다음 개장: <b>{nxt.strftime('%Y-%m-%d %H:%M')}</b>
  </p>
</div>
""",
                unsafe_allow_html=True,
            )

        disabled = not market_open
        if side == "SELL" and held < qty:
            st.error(f"보유 수량({held:,}주)이 부족해요.")
            disabled = True

        confirm = st.checkbox("위 내용으로 진행할게요.", value=False)
        btn = f"🟢 {qty:,}주 사기" if side == "BUY" else f"🔴 {qty:,}주 팔기"
        if st.button(
            btn, type="primary", use_container_width=True,
            disabled=disabled or not confirm,
        ):
            try:
                r = execute_order(selected.symbol, side, qty, quote, ts=now_kst())
                st.success(
                    f"체결 완료! 체결가 {unit_fmt(float(r['fill_price']))} · "
                    f"주문 ID #{r['trade_id']}"
                )
                if r["realized_pnl"] is not None:
                    pnl = float(r["realized_pnl"])
                    label = "이익" if pnl >= 0 else "손실"
                    st.info(f"실현 {label}: {unit_fmt(pnl)}")
                st.balloons()
                st.rerun()
            except MarketClosedError as ex:
                st.error(f"체결 실패 (시장 닫힘): {ex}")
            except ValueError as ex:
                st.error(f"체결 실패: {ex}")


st.markdown("### 📜 최근 거래")
with connect() as conn:
    rows = conn.execute(
        """
        SELECT ts, symbol, market, side, qty, fill_price, fee_amt, tax_amt,
               realized_pnl
        FROM trades ORDER BY id DESC LIMIT 10
        """
    ).fetchall()

if rows:
    rec = pd.DataFrame([dict(r) for r in rows])
    rec.columns = ["시각", "종목", "시장", "주문", "수량", "체결가", "수수료", "거래세", "실현손익"]
    st.dataframe(rec, use_container_width=True, hide_index=True)
else:
    st.caption("아직 거래 기록이 없어요.")

render_disclaimer()
