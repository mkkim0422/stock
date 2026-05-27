# DEPLOYMENT — 폰에서 보기까지 (단계별 가이드)

## 목표
PC가 꺼져 있어도 핸드폰 브라우저로 swing-advisor 가상매매를 사용.

## 구조
```
[당신의 폰/PC 브라우저]
        ↓ HTTPS
[Streamlit Cloud (무료)]  ← 코드 자동 배포
        ↓ libsql
[Turso 클라우드 DB (무료)]  ← 거래/포지션 영속 저장
```

---

## 1단계 — GitHub에 코드 올리기 (5분)

1. https://github.com 가입/로그인
2. New repository → **Private**, 이름 `swing-advisor` → Create
3. 로컬에서:
```powershell
git remote add origin https://github.com/<본인아이디>/swing-advisor.git
git push -u origin master
```

---

## 2단계 — Turso 클라우드 DB 만들기 (10분, 무료)

1. https://turso.tech 가입 (GitHub 로그인 가능)
2. 대시보드 → Create Database → 이름 `swing-advisor` → Create
3. 생성된 DB 페이지에서:
   - **Database URL** 복사 (예: `libsql://swing-advisor-xxx.turso.io`)
   - **Generate Token** → 토큰 복사
4. 두 값을 메모장에 보관 (다음 단계에서 사용)

무료 한도 (2026-05 기준): 9GB 저장, 월 10억 reads, 5억 writes. 개인 사용에 차고 넘침.

---

## 3단계 — Streamlit Cloud 에 배포 (5분, 무료)

1. https://share.streamlit.io 접속 → GitHub 계정으로 로그인
2. **New app** → 1단계의 repo 선택
3. **Main file path**: `src/ui/app.py`
4. **Advanced settings** → Python version `3.11` 선택
5. **Secrets** 클릭 → 아래 형식으로 입력 (2단계에서 메모한 값):
```toml
TURSO_DATABASE_URL = "libsql://swing-advisor-xxx.turso.io"
TURSO_AUTH_TOKEN = "eyJhbGc..."
MODE = "paper"
```
6. **Deploy** 클릭. 2~3분 대기.

배포 완료되면 발급된 URL (예: `https://swing-advisor-xxx.streamlit.app`) 을 폰 브라우저 즐겨찾기에 추가.

---

## 4단계 — 폰에서 접속

위 URL을 폰 사파리/크롬에서 열기. 끝.
- 평소: 이 URL 즐겨찾기로 접속
- 데이터: Turso 에 저장되어 어느 기기에서 접속해도 동일

---

## 자동 sleep 회피 (선택)

Streamlit Cloud 무료 앱은 **12시간 비활성 시 sleep**. 다시 접속하면 30초 정도 깨우기.

자동 ping 활성:
1. GitHub repo → Settings → Secrets and variables → Actions → New secret
2. Name: `STREAMLIT_APP_URL`, Value: 본인 앱 URL (예: `https://swing-advisor-xxx.streamlit.app`)
3. `.github/workflows/keepalive-weekly.yml` 가 일요일 03:00 UTC 에 자동 ping (이미 활성)

---

## 로컬에서 Turso 사용하고 싶다면 (옵션)

Python 3.11 또는 3.12 사용 시 `pip install -r requirements-cloud.txt` 로 libsql 설치 가능. Python 3.14 는 현재 libsql wheel 미배포라 자동으로 로컬 SQLite 폴백.

`.env`:
```
TURSO_DATABASE_URL=libsql://swing-advisor-xxx.turso.io
TURSO_AUTH_TOKEN=eyJhbGc...
```

---

## 보안

- 토큰은 절대 GitHub에 직접 commit 하지 말 것 (`.gitignore` 가 막아주지만 재확인)
- Streamlit Cloud Secrets 또는 `.env` (gitignore) 에만 저장
- 누출 의심 시 Turso 대시보드 → Token 페이지 → **Revoke** 즉시

---

## 비용

- GitHub Private repo: 무료
- Turso 무료 티어: 무료
- Streamlit Cloud Community: 무료
- **합계: ₩0**

---

## 트러블슈팅

### "Streamlit Cloud 에 'libsql_client' import error"
→ Settings → Python version 3.11 또는 3.12 인지 확인. 3.13 이상은 wheel 미배포.

### "Turso 연결 timeout"
→ Turso URL 이 `libsql://` 로 시작하는지 확인 (`https://` 아님).

### "폰에서 화면 깨짐"
→ 우측 상단 ⋯ → "Wide mode" 옵션 끄기. Streamlit 기본은 데스크톱 기준.

### "거래 기록이 사라짐"
→ Turso 미설정 시 Streamlit Cloud 재시작마다 데이터 휘발. 위 2-3단계 다시 확인.
