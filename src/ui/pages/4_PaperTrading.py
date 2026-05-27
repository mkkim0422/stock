"""💼 가상투자 — 모의 매수/매도 (작동 페이지)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pandas as pd
import streamlit as st

from src.collectors.mock import MockCollector
from src.paper.fees import calc_fee, calc_tax
from src.paper.portfolio import get_position
from src.paper.slippage import apply_slippage
from src.paper.trader import execute_order
from src.storage import apply_migrations, connect
from src.symbols import search_symbols
from src.ui.components import render_disclaimer, render_sidebar
from src.ui.components.kpi_card import fmt_krw, fmt_usd

st.set_page_config(page_title="가상투자 · swing-advisor", page_icon="💼", layout="wide")
apply_migrations()
render_sidebar()

st.title("💼 가상투자")
st.caption("실거래가 아닙니다. 모든 주문은 가상으로 체결됩니다.")

collector = MockCollector()

# 좌/우 2단 레이아웃
left, right = st.columns([1.1, 1])

# ─── 좌측: 종목 선택 + 주문폼 ───────────────────────────────
with left:
    st.markdown("#### 1️⃣ 종목 선택")
    q = st.text_input("검색", placeholder="삼성, 005930, AAPL ...", key="trade_search")
    selected = None
    if q:
        hits = search_symbols(q, limit=10)
        if hits:
            labels = [f"{h.symbol} · {h.name_kr or h.name} ({h.market})" for h in hits]
            idx = st.radio("결과 선택", range(len(hits)), format_func=lambda i: labels[i], label_visibility="collapsed")
            selected = hits[idx]
        else:
            st.warning(f'"{q}" 에 대한 결과 없음')
    else:
        st.caption("종목을 검색하면 여기에 결과가 표시됩니다.")

    if selected is not None:
        try:
            price = collector.fetch_realtime(selected.symbol)
            st.success(f"**{selected.name_kr or selected.name}** ({selected.symbol}) 현재가: " +
                       (fmt_krw(price) if selected.market == "KR" else fmt_usd(price)))
        except ValueError:
            st.error("이 종목은 mock 데이터가 없습니다. 다른 종목을 선택하세요.")
            selected = None

    if selected is not None:
        st.markdown("#### 2️⃣ 주문")
        side = st.radio("주문 종류", ["BUY", "SELL"], horizontal=True, format_func=lambda s: "🟢 매수" if s == "BUY" else "🔴 매도")
        qty = st.number_input("수량 (정수)", min_value=1, value=1, step=1)

# ─── 우측: 주문 미리보기 + 확정 ─────────────────────────────
with right:
    if "selected" not in dir() or selected is None:
        st.info("👈 좌측에서 종목을 선택하고 수량을 입력하세요.")
    else:
        st.markdown("#### 3️⃣ 주문 미리보기")
        try:
            quote = Decimal(str(price))
            fill = apply_slippage(quote, side)
            notional = fill * Decimal(qty)
            fee = calc_fee(selected.market, notional)
            tax = calc_tax(selected.market, side, notional)
            total = notional + fee + tax if side == "BUY" else notional - fee - tax

            unit = fmt_krw if selected.market == "KR" else fmt_usd
            df = pd.DataFrame(
                [
                    ["종목", f"{selected.symbol} · {selected.name_kr or selected.name}"],
                    ["주문", "🟢 매수" if side == "BUY" else "🔴 매도"],
                    ["수량", f"{qty:,} 주"],
                    ["체결가 (예상, 슬리피지 0.07% 반영)", unit(float(fill))],
                    ["거래대금", unit(float(notional))],
                    ["수수료", unit(float(fee))],
                    ["거래세", unit(float(tax))],
                    ["**합계** (지불/수령)", unit(float(total))],
                ],
                columns=["항목", "값"],
            )
            st.dataframe(df, hide_index=True, use_container_width=True)

            pos = get_position(selected.symbol)
            held = pos[0] if pos else 0
            st.caption(f"현재 보유 수량: {held:,} 주")

            if side == "SELL" and held < qty:
                st.error(f"보유 수량({held})이 부족합니다.")
                disabled = True
            else:
                disabled = False

            st.markdown("#### 4️⃣ 확정")
            confirm = st.checkbox("위 내용으로 주문을 진행합니다.", value=False)
            if st.button(("🟢 매수 확정" if side == "BUY" else "🔴 매도 확정"),
                         type="primary", use_container_width=True,
                         disabled=disabled or not confirm):
                try:
                    r = execute_order(selected.symbol, side, qty, quote, ts=datetime.now())
                    st.success(
                        f"체결 완료! ID #{r['trade_id']}, "
                        f"체결가 {unit(float(r['fill_price']))}"
                    )
                    if r["realized_pnl"] is not None:
                        pnl = float(r["realized_pnl"])
                        emoji = "🟢" if pnl >= 0 else "🔴"
                        st.info(f"{emoji} 실현손익: {unit(pnl)}")
                    st.balloons()
                except ValueError as ex:
                    st.error(f"체결 실패: {ex}")
        except Exception as ex:
            st.error(f"오류: {ex}")

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
    df = pd.DataFrame([dict(r) for r in rows])
    df.columns = ["시각", "종목", "시장", "주문", "수량", "체결가", "수수료", "거래세", "실현손익"]
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.caption("아직 거래 기록이 없습니다.")

render_disclaimer()
