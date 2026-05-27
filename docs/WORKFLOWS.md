# WORKFLOWS — GitHub Actions 워크플로

## Phase 1 현황
yml 파일은 있으나 schedule 비활성 (주석).
test.yml, lint.yml 만 push 시 활성.

## 워크플로 목록
| 파일 | 트리거 | 활성 |
|---|---|---|
| test.yml | push | ✓ |
| lint.yml | push | ✓ |
| briefing-0700.yml | cron 22:00 UTC | ✗ (Phase 6) |
| briefing-0930.yml | cron 00:30 UTC | ✗ (Phase 6) |
| briefing-1200.yml | cron 03:00 UTC | ✗ (Phase 6) |
| briefing-1430.yml | cron 05:30 UTC | ✗ (Phase 6) |
| briefing-1600.yml | cron 07:00 UTC | ✗ (Phase 6) |
| briefing-1800.yml | cron 09:00 UTC | ✗ (Phase 6) |
| briefing-2330.yml | cron 14:30 UTC | ✗ (Phase 6) |
| keepalive-weekly.yml | cron 일 03:00 UTC | ✗ (Phase 7) |
| db-backup-weekly.yml | cron 일 04:00 UTC | ✗ (Phase 7) |

## KST → UTC 변환
KST는 UTC+9. KST 07:00 = UTC 22:00 (전날).

## cron 지연
GitHub Actions cron은 **15~30분 지연 빈번**. 정시 보장 안 됨.
브리핑 메시지에 발화 시각 명시 필수.

## 비밀
- GEMINI_API_KEY
- GROQ_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

## keepalive 주의
- Streamlit Cloud 12h sleep 회피용
- 단순 echo (commit 없음, 무한 루프 방지)
- Phase 7 에서 검토 후 활성
