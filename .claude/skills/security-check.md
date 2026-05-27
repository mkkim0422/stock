---
name: security-check
description: 커밋 전 API 키/비밀 누출 점검
---

# security-check skill

## 언제 사용
- 매 commit 직전
- PR 직전
- 누출 의심 시

## 점검 항목
1. `.env` staging 여부 (`git status` 에 표시되면 즉시 unstage)
2. `secrets.toml` staging 여부
3. 키 패턴 grep:
   - `AIza` (Google)
   - `sk-` (OpenAI/Anthropic)
   - `ghp_` (GitHub PAT)
   - `xoxb-` (Slack)
   - `bot[0-9]+:` (Telegram)

## 명령
```powershell
git diff --staged | Select-String "AIza|sk-|ghp_|xoxb-|bot\d+:"
git ls-files | Select-String "^\.env$|secrets\.toml$"
```

## 누출 발생 시
1. 키 즉시 revoke (발급처 대시보드)
2. `git reset HEAD <file>` 후 .gitignore 추가
3. 이미 commit 됐다면 `git filter-repo` 로 히스토리 정리
4. 새 키 발급 후 `.env` 갱신
