# SECURITY — 보안 정책

## 절대 규칙
1. **실제 API 키는 절대 커밋하지 않는다**.
   - `.env`, `.streamlit/secrets.toml`, `secrets/` 모두 `.gitignore` 되어 있다.
   - 커밋 전 `git status` 로 staging 확인 필수.
2. **실주문 코드 작성 금지**.
   - 본 프로젝트는 페이퍼 트레이딩 전용. 실증권사 API 코드는 금지.
3. **사용자 PC 외 데이터 송신 금지**.
   - DB는 로컬 SQLite. Cloud DB는 사용자 동의 + Phase 2 검토 후.
4. **위험 명령 금지**.
   - `rm -rf`, `dd`, `mkfs`, `sudo`, `force-push to main` 자동 실행 금지.

## 키 누출 점검 (매 STEP)
- `git diff` 로 staged 파일 확인
- 키 패턴 grep:
  - `AIza` (Google)
  - `sk-` (OpenAI/Anthropic)
  - `ghp_` (GitHub PAT)
  - `xoxb-` (Slack)
  - `bot[0-9]+:` (Telegram)

## 누출 발생 시 즉시 조치
1. 해당 키 발급처에서 **revoke** (Gemini/Groq/Telegram/Turso 대시보드).
2. `git filter-branch` 또는 `git filter-repo` 로 히스토리 정리.
3. 새 키 발급 후 `.env` 갱신.

## 의존성 보안
- `pip-audit` 또는 `safety` 로 주기 점검 (Phase 7).
- 신규 의존성 추가 시 PyPI 다운로드 수, 마지막 업데이트 확인.

## 데이터 보호
- DB 백업은 로컬만 (data/backups/).
- 백업 파일도 `.gitignore`.

## 면책
- 본 도구는 투자 자문이 아니며, 모든 거래 결과 책임은 사용자에게 있다.
- 페이퍼 트레이딩 결과가 실거래 성과를 보장하지 않는다.
