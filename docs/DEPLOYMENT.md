# DEPLOYMENT — 배포 (Phase 7 활성)

## Phase 1 현황
GitHub Actions yml 파일은 있으나 비활성 (placeholder).

## 환경
- 로컬 PC (Windows 11) — 개발/테스트
- Streamlit Cloud — UI (Phase 7)
- GitHub Actions — cron 브리핑 (Phase 7)

## Streamlit Cloud
- 무료 1앱 / 1GB RAM
- 12시간 비활성 시 sleep
- keepalive: 일요일 commit (no-op)으로 깨우기
- 한국어 파일명 URL 문제 → 영문 파일명만

## GitHub Actions
- 무료 2,000분/월 (private repo)
- cron 지연 15~30분 정상
- secrets: GEMINI_API_KEY, GROQ_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

## 비활성/활성 토글
- `.github/workflows/*.yml` 에서 `on.schedule` 주석 처리로 비활성
- Phase 7 에 일괄 활성

## 운영 시간
- 한국 09:00~15:30 KST
- 미국 09:30~16:00 ET (서머타임 주의)
