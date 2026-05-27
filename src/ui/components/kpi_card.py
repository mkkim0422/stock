"""KPI 카드 — 정보 위계 1번 자리에 표시."""
from __future__ import annotations

import streamlit as st


def kpi_row(items: list[dict]) -> None:
    """items: [{'label': str, 'value': str, 'delta': str|None, 'help': str|None}]"""
    cols = st.columns(len(items))
    for col, item in zip(cols, items, strict=True):
        with col:
            st.metric(
                label=item["label"],
                value=item["value"],
                delta=item.get("delta"),
                help=item.get("help"),
            )


def fmt_krw(amount: float) -> str:
    return f"₩{amount:,.0f}"


def fmt_usd(amount: float) -> str:
    return f"${amount:,.2f}"


def fmt_pct(pct: float, signed: bool = True) -> str:
    if signed and pct > 0:
        return f"+{pct:.2f}%"
    return f"{pct:.2f}%"


def color_pnl(value: float) -> str:
    if value > 0:
        return "🟢"
    if value < 0:
        return "🔴"
    return "⚪"
