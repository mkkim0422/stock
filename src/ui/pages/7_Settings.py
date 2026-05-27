"""⚙️ 설정 — 모드, DB 상태."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config import get_settings
from src.storage import get_db_path
from src.ui.components import render_disclaimer, render_sidebar

st.set_page_config(page_title="설정 · swing-advisor", page_icon="⚙️", layout="wide")
render_sidebar()

st.title("⚙️ 설정")
st.caption("Phase 1 에서는 읽기 전용입니다. 변경은 `.env` 파일에서.")

settings = get_settings()

st.markdown("### 🔧 운영")
c1, c2 = st.columns(2)
c1.text_input("MODE", value=settings.mode, disabled=True)
c2.text_input("LOG_LEVEL", value=settings.log_level, disabled=True)

st.markdown("### 💾 데이터베이스")
db = Path(get_db_path())
exists = db.exists()
size_kb = db.stat().st_size / 1024 if exists else 0
c1, c2, c3 = st.columns(3)
c1.metric("DB 파일", "있음" if exists else "없음")
c2.metric("크기", f"{size_kb:,.1f} KB")
c3.metric("경로", str(db))

st.markdown("### 🔑 환경변수 상태")
def mask(v: str | None) -> str:
    if v is None:
        return "❌ 미설정"
    return "✅ 설정됨 (****" + v[-4:] + ")"

c1, c2 = st.columns(2)
with c1:
    st.write(f"GEMINI_API_KEY: {mask(settings.gemini_api_key)}")
    st.write(f"GROQ_API_KEY: {mask(settings.groq_api_key)}")
    st.write(f"TELEGRAM_BOT_TOKEN: {mask(settings.telegram_bot_token)}")
with c2:
    st.write(f"TELEGRAM_CHAT_ID: {mask(settings.telegram_chat_id)}")
    st.write(f"TURSO_DATABASE_URL: {mask(settings.turso_database_url)}")
    st.write(f"FX_API_KEY: {mask(settings.fx_api_key)}")

st.info(
    "📌 환경변수는 `.env` 또는 `.streamlit/secrets.toml` 에 설정합니다. "
    "Phase 1 에서는 모두 비어 있어도 정상 작동합니다."
)

render_disclaimer()
