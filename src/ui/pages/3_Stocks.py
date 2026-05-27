"""🔍 종목 — 종목 검색."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.symbols import search_symbols
from src.ui.components import render_disclaimer, render_sidebar

st.set_page_config(page_title="종목 · swing-advisor", page_icon="🔍", layout="wide")
render_sidebar()

st.title("🔍 종목 검색")
st.caption("티커, 영문명, 한글명으로 검색하세요. 결과 클릭은 Phase 3 에서 활성됩니다.")

q = st.text_input("검색어", placeholder="예: 삼성, 005930, AAPL, Apple", label_visibility="collapsed")
if q:
    hits = search_symbols(q, limit=30)
    if not hits:
        st.warning(f'"{q}" 에 대한 결과가 없습니다.')
    else:
        df = pd.DataFrame(
            [
                {
                    "코드": s.symbol,
                    "시장": s.market,
                    "영문명": s.name,
                    "한글명": s.name_kr or "",
                    "섹터": s.sector or "",
                }
                for s in hits
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(df)}건")
else:
    st.info("🔎 검색어를 입력하세요. 예) `삼성`, `AAPL`, `반도체`")

render_disclaimer()
