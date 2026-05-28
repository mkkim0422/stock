"""💼 가상투자 — 실시간 시세 기반 모의 매수/매도. 정규장 시간에만 거래."""
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
from src.ui.components import render_disclaimer, render_market_status, render_sidebar
from src.ui.components.kpi_card import fmt_krw, fmt_usd
from src.utils.market_hours import (
    market_status,
    next_market_open,
    status_label,
)
from src.utils.timezone import now_kst

st.set_page_config(page_title="가상투자 · swing-advisor", page_icon="💼", layout="wide")
apply_migrations()
render_sidebar()

st.title("💼 가상투자")
st.caption("실거래가 아닙니다. **실시간 시세**로 가상 체결되며, **정규장 시간**에만 주문 가능합니다.")

with st.expander("🕒 시장 상태", expanded=True):
    render_market_status()
    st.caption("정규장이 닫혀 있으면 주문 버튼이 비활성화됩니다 (실 증권사와 동일).")


@st.cache_data(ttl=60, show_spinner=False)
def _quote(symbol: str) -> float:
    """실시간 시세 (60초 캐시)."""
    return fetch_realtime(symbol)


# 좌/우 2단 레이아웃
left, right = st.columns([1.1, 1])

selected = None
price = None
side = "BUY"
qty = 1

# ─── 좌측: 종목 선택 + 주문폼 ───────────────────────────────
with left:
    st.markdown("#### 1️⃣ 종목 선택")
    q = st.text_input(
        "검색", placeholder="삼성, 005930, AAPL ...", key="trade_search"
    )
    if q:
        with st.spinner("검색 중..."):
            hits = search_symbols(q, limit=10)
        if hits:
            labels = [
                f"{h.symbol} · {h.name_kr or h.name} ({h.market})" for h in hits
            ]
            idx = st.radio(
                "결과 선택",
                range(len(hits)),
                format_func=lambda i: labels[i],
                label_visibility="collapsed",
            )
            selected = hits[idx]
        else:
            st.warning(f'"{q}" 에 대한 결과 없음')
    else:
        st.caption("종목을 검색하면 여기에 결과가 표시됩니다.")

    if selected is not None:
        try:
            with st.spinner("실시간 시세 조회..."):
                price = _quote(selected.symbol)
            unit_fmt = fmt_krw if selected.market == "KR" else fmt_usd
            st.success(
                f"**{selected.name_kr or selected.name}** "
                f"({selected.symbol}) 현재가: {unit_fmt(price)}"
            )
        except Exception as ex:
            st.error(
                f"시세 조회 실패: {ex}\n\n"
                "잠시 후 다시 시도하거나 다른 종목을 선택하세요."
            )
            selected = None

    if selected is not None:
        st.markdown("#### 2️⃣ 주문")
        side = st.radio(
            "주문 종류",
            ["BUY", "SELL"],
            horizontal=True,
            format_func=lambda s: "🟢 매수" if s == "BUY" else "🔴 매도",
        )
        qty = int(st.number_input("수량 (정수)", min_value=1, value=1, step=1))

# ─── 우측: 주문 미리보기 + 확정 ─────────────────────────────
with right:
    if selected is None or price is None:
        st.info("👈 좌측에서 종목을 선택하고 수량을 입력하세요.")
    else:
        st.markdown("#### 3️⃣ 주문 미리보기")
        quote = Decimal(str(price))
        fill = apply_slippage(quote, side)
        notional = fill * Decimal(qty)
        fee = calc_fee(selected.market, notional)
        tax = calc_tax(selected.market, side, notional)
        total = notional + fee + tax if side == "BUY" else notional - fee - tax

        unit_fmt = fmt_krw if selected.market == "KR" else fmt_usd
        preview = pd.DataFrame(
            [
                ["종목", f"{selected.symbol} · {selected.name_kr or selected.name}"],
                ["주문", "🟢 매수" if side == "BUY" else "🔴 매도"],
                ["수량", f"{qty:,} 주"],
                ["체결가 (슬리피지 0.07% 반영)", unit_fmt(float(fill))],
                ["거래대금", unit_fmt(float(notional))],
                ["수수료", unit_fmt(float(fee))],
                ["거래세", unit_fmt(float(tax))],
                ["합계 (지불/수령)", unit_fmt(float(total))],
            ],
            columns=["항목", "값"],
        )
        st.dataframe(preview, hide_index=True, use_container_width=True)

        pos = get_position(selected.symbol)
        held = pos[0] if pos else 0
        st.caption(f"현재 보유 수량: {held:,} 주")

        # 시장 상태에 따라 매매 가능 여부 결정
        now = now_kst()
        cur_status = market_status(selected.market, now)
        market_open = cur_status == "OPEN"

        if not market_open:
            nxt = next_market_open(selected.market, now)
            st.error(
                f"🚫 현재 {selected.market} 시장 상태: **{status_label(cur_status)}**\n\n"
                f"다음 개장 시각: **{nxt.strftime('%Y-%m-%d %H:%M KST')}**\n\n"
                f"실제 증권사와 동일하게, 정규장 시간에만 주문할 수 있습니다."
            )

        disabled = not market_open
        if side == "SELL" and held < qty:
            st.error(f"보유 수량({held:,})이 부족합니다.")
            disabled = True

        st.markdown("#### 4️⃣ 확정")
        confirm = st.checkbox("위 내용으로 주문을 진행합니다.", value=False)
        btn_label = "🟢 매수 확정" if side == "BUY" else "🔴 매도 확정"
        if st.button(
            btn_label,
            type="primary",
            use_container_width=True,
            disabled=disabled or not confirm,
        ):
            try:
                r = execute_order(selected.symbol, side, qty, quote, ts=now_kst())
                st.success(
                    f"체결 완료! 주문 ID #{r['trade_id']}, "
                    f"체결가 {unit_fmt(float(r['fill_price']))}"
                )
                if r["realized_pnl"] is not None:
                    pnl = float(r["realized_pnl"])
                    emoji = "🟢" if pnl >= 0 else "🔴"
                    st.info(f"{emoji} 실현손익: {unit_fmt(pnl)}")
                st.balloons()
                st.rerun()
            except MarketClosedError as ex:
                st.error(f"체결 실패 (시장 닫힘): {ex}")
            except ValueError as ex:
                st.error(f"체결 실패: {ex}")

# ─── 하단: 최근 거래 10건 ─────────────────────────────────
st.markdown("---")
st.markdown("#### 📜 최근 거래 (10건)")
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
    st.caption("아직 거래 기록이 없습니다.")

render_disclaimer()
