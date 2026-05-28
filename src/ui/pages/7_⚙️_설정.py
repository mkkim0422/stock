"""⚙️ 설정 — 모드, DB 상태, 종목 마스터 갱신."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[3]
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

from src.config import get_settings
from src.llm import get_llm as _get_llm
from src.llm import is_available as _llm_av
from src.notifications import is_telegram_configured as _tg_cfg
from src.notifications import send_message as _tg_send
from src.storage import get_db_path
from src.storage.cloud import get_status as get_cloud_status
from src.symbols import get_last_refresh, refresh_kr_from_krx, set_last_refresh
from src.ui.components import inject_css, render_disclaimer, render_sidebar
from src.utils.timezone import to_kst

st.set_page_config(page_title="설정 · swing-advisor", page_icon="⚙️", layout="wide")
inject_css()
render_sidebar()

st.markdown("## ⚙️ 설정")
st.caption("환경·연결·외부 키 상태를 확인하고 종목 마스터를 갱신할 수 있어요.")

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

cs = get_cloud_status()
if cs["active"]:
    st.success(f"☁️ Turso 클라우드 DB 연결됨 ({cs['url_host']}) — 폰에서 동일 데이터 접근 가능")
elif cs["configured"] and not cs["library_available"]:
    st.warning(
        "⚠️ Turso 환경변수는 있지만 `libsql_client` 미설치. "
        "Streamlit Cloud (Python 3.11/3.12) 에서는 자동 활성됩니다. "
        "로컬 Python 3.14 는 호환 wheel 미배포라 로컬 SQLite 사용."
    )
else:
    st.info(
        "📁 로컬 SQLite 사용 중. 폰에서도 보려면 `docs/DEPLOYMENT.md` 의 "
        "4단계 가이드 참고 (GitHub → Turso → Streamlit Cloud)."
    )

st.markdown("### 🔄 종목 마스터 (KRX)")
last = get_last_refresh()
c1, c2 = st.columns([1, 2])
with c1:
    if last is None:
        st.metric("마지막 갱신", "—")
    else:
        st.metric("마지막 갱신", to_kst(last).strftime("%m-%d %H:%M"))
with c2:
    st.caption(
        "3시간마다 자동 갱신됩니다 (신규 상장/이름 변경 반영). "
        "아래 버튼으로 즉시 갱신할 수도 있습니다."
    )
    if st.button("🔄 지금 갱신", type="secondary"):
        with st.spinner("KRX 전종목 가져오는 중... (20~30초)"):
            try:
                n = refresh_kr_from_krx()
                set_last_refresh(datetime.now(UTC))
                st.success(f"갱신 완료: {n}개 종목")
                st.rerun()
            except Exception as ex:
                st.error(f"갱신 실패: {ex}")

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
    st.write(f"TURSO_AUTH_TOKEN: {mask(settings.turso_auth_token)}")

st.info(
    "📌 환경변수는 `.env` (로컬) 또는 Streamlit Cloud > Settings > Secrets (배포) 에 설정. "
    "API 키가 없어도 핵심 기능은 작동합니다."
)

# 텔레그램 연결 테스트
st.markdown("### 📨 텔레그램 연결 테스트")

if _tg_cfg():
    st.success("✅ 텔레그램 봇 설정 확인됨")
    if st.button("📤 테스트 메시지 보내기"):
        with st.spinner("전송 중..."):
            ok = _tg_send(
                "*[swing-advisor]* 연결 테스트 ✅\n"
                "텔레그램 봇이 정상 작동합니다."
            )
        if ok:
            st.success("전송 성공! 텔레그램을 확인하세요.")
        else:
            st.error(
                "전송 실패. TOKEN/CHAT_ID 가 올바른지, "
                "봇과 대화를 한 번 시작했는지 확인하세요."
            )
else:
    st.warning(
        "텔레그램 봇이 설정되지 않았습니다. `TELEGRAM_BOT_TOKEN` / "
        "`TELEGRAM_CHAT_ID` 를 설정하세요. "
        "(@BotFather 로 봇 생성 후 토큰 / api.telegram.org/bot<TOKEN>/getUpdates 로 chat_id)"
    )

# LLM 연결 테스트
st.markdown("### 🤖 LLM 연결 테스트")

if _llm_av():
    _llm = _get_llm()
    assert _llm is not None
    st.success(f"✅ {_llm.name} 사용 가능")
    if st.button("🧪 한 줄 생성 테스트"):
        try:
            with st.spinner("LLM 호출 중..."):
                out = _llm.generate("한 문장으로 자기소개해 주세요.", max_tokens=80)
            st.info(out)
        except Exception as ex:
            st.error(f"LLM 호출 실패: {ex}")
else:
    st.warning(
        "LLM 키가 설정되지 않았습니다. `GEMINI_API_KEY` 또는 `GROQ_API_KEY` 를 설정하세요."
    )

render_disclaimer()
