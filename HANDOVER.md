# 인수인계서 — swing-advisor

작성일: 2026-05-28
GitHub: https://github.com/mkkim0422/stock
모드: 페이퍼 트레이딩 (가상매매) 전용

---

## 1. 한 줄 소개

한국+미국 주식 **가상매매**와 **시그널 모니터링**을 도와주는 개인용 도구.
실제 돈은 한 푼도 안 나갑니다. 모든 거래는 가짜.

---

## 2. 지금까지 만든 것 (Phase 1~7 완료)

### 📊 작동하는 기능

| 화면 | 기능 |
|---|---|
| 🏠 홈 | 오늘 평가액, 보유 종목 수, 시장 상태 |
| 📈 시장 | KOSPI/KOSDAQ/S&P500/NASDAQ 실시간 + 6개월 차트 |
| 🔍 종목 | 종목 검색 + 캔들/MA/RSI/MACD 차트 |
| 💼 가상투자 | 실시간 시세로 매수/매도. 정규장 시간에만 작동 (실제 증권사와 동일) |
| 📊 투자결과 | 평가액 KPI + 자산곡선 + 보유 포지션 + 거래이력 CSV |
| 🧪 백테스트 | 시그널 전략 과거 성과 (CAGR/Sharpe/MDD/승률) + OOS 검증 |
| ⚙️ 설정 | DB 상태, 환경변수, 텔레그램/LLM 테스트, 종목 마스터 갱신 |
| ❓ 도움말 | FAQ + 면책 |
| 🎯 시그널 | 워치리스트 종목 매수/매도 점수 모니터링 + LLM 코멘트 |

### 🔧 기술 스택
- Python 3.11+ (로컬 3.14 / Streamlit Cloud 3.11)
- Streamlit UI
- SQLite + WAL (로컬) / Turso libSQL (클라우드)
- pykrx, yfinance, FinanceDataReader (실데이터)
- exchangerate.host (환율)
- Gemini 2.5 Flash / Groq Llama (LLM, 선택)
- Telegram Bot API (알림, 선택)
- GitHub Actions (7회/일 자동 브리핑)

### 📐 핵심 수치 (모두 코드+문서 일치)
- 한국 거래세: **0.20%** (2026-01-01 시행)
- 한국 수수료: 0.015% (매수/매도)
- 미국 수수료: $0
- 환전 수수료: 0.1%
- 슬리피지: 0.07%
- 시그널: **매수 +8 이상 / 매도 -3 이하**
- 가상 초기 자본: KRW 1,000만 + USD 1만

### 🎯 시그널 컴포넌트 10개
| 컴포넌트 | 조건 | 점수 |
|---|---|---|
| RSI 과매도 | < 30 | +2 |
| RSI 과매수 | > 70 | -2 |
| MACD 골든 | 히스토 - → + | +3 |
| MACD 데드 | 히스토 + → - | -3 |
| MA20/60/200 | 종가 위 | +1 각 |
| 5일 +5%↑ | 과열 | -1 |
| 거래량 2x↑ | 평균 대비 | +2 |
| OBV | 매집 추세 | +1 |

### ✅ 검증 상태
- 테스트: 168/168 통과
- 커버리지: 79%
- 린트(ruff): 0건
- 타입체크(mypy): 0건
- API 키 누출: 0건
- Streamlit 작동: HTTP 200

### 📚 문서 (docs/)
- ARCHITECTURE.md, API_GUIDE.md, BACKTEST.md
- COSTS.md, DATA_FALLBACK.md, DB_PERSISTENCE.md
- **DEPLOYMENT.md** ← 폰에서 보기 4단계
- DISCLAIMER.md, GLOSSARY.md, INDICATORS.md
- NOTIFICATIONS.md, PAPER_TRADING.md, ROADMAP.md
- SECURITY.md, SIGNALS.md, TESTING.md
- TROUBLESHOOTING.md, UI_GUIDE.md, WORKFLOWS.md

---

## 3. 사용자가 직접 해야 할 일 (자동화 불가)

### A. 폰에서 보기 (필수, 약 25분)

#### 1단계 — Turso 가입 + DB 생성 (10분)
1. https://turso.tech 접속 → GitHub 계정으로 로그인
2. Dashboard → **Create Database** → 이름 `swing-advisor` → Create
3. 생성된 DB 페이지에서:
   - **Database URL** 복사 (`libsql://swing-advisor-xxx.turso.io`)
   - **Generate Token** → 토큰 복사
4. 두 값을 메모장에 잘 보관

#### 2단계 — Streamlit Cloud 배포 (10분)
1. https://share.streamlit.io 접속 → GitHub 로그인
2. **New app**
   - Repository: `mkkim0422/stock`
   - Branch: `master`
   - Main file path: `src/ui/app.py`
3. **Advanced settings** → Python version: **3.11**
4. **Secrets** 클릭 → 아래 형식으로 입력:
   ```toml
   TURSO_DATABASE_URL = "libsql://swing-advisor-xxx.turso.io"
   TURSO_AUTH_TOKEN = "eyJhbGc..."
   MODE = "paper"
   ```
5. **Deploy** 클릭. 2~3분 대기.

#### 3단계 — 폰 접속
배포 완료되면 `https://swing-advisor-xxx.streamlit.app` 같은 URL 발급됨.
폰 사파리/크롬에서 열고 즐겨찾기 추가. 끝.

### B. 텔레그램 알림 (선택, 약 10분)
1. 폰에서 **@BotFather** 검색 → 채팅
2. `/newbot` → 봇 이름 입력 → 토큰 받기 (`123456:ABC-DEF...`)
3. 자기 봇과 한 번 채팅 시작 ("Hi" 같은 거)
4. PC 브라우저에서 `https://api.telegram.org/bot<토큰>/getUpdates` 열기
5. 응답에서 `"chat":{"id":12345}` 찾아 **chat_id** 메모
6. GitHub repo → Settings → Secrets and variables → Actions → New secret
   - `TELEGRAM_BOT_TOKEN`: 토큰
   - `TELEGRAM_CHAT_ID`: chat_id
7. Streamlit Cloud Secrets 에도 동일하게 추가

### C. LLM 코멘트 (선택, 약 5분)
- **Gemini** (추천, 무료): https://aistudio.google.com/app/apikey → Create API key
- **Groq** (대안, 무료): https://console.groq.com/keys → Create API key
- GitHub Secrets + Streamlit Cloud Secrets 에 `GEMINI_API_KEY` 또는 `GROQ_API_KEY` 추가

### D. Streamlit Cloud Sleep 방지 (선택)
- GitHub Secrets에 `STREAMLIT_APP_URL` = 배포된 앱 URL 추가
- 일요일 03:00 UTC 자동 ping (`.github/workflows/keepalive-weekly.yml`)

---

## 4. 매일 어떻게 쓰는지 (사용 흐름)

### 평소 (한국 장중 09:00~15:30)
1. 폰으로 Streamlit Cloud URL 접속
2. 🎯 시그널 페이지 확인 — 매수 후보/매도 후보
3. 마음에 드는 종목 있으면 💼 가상투자에서 모의 매수
4. 📊 투자결과로 평가 손익 확인

### 매일 자동 알림 (텔레그램 설정 시)
- 07:00 (개장 전) / 09:30 (개장 후) / 12:00 (점심) / 14:30 (마감 전)
- 16:00 (마감 후) / 18:00 (저녁) / 23:30 (미국 개장)
- 각 시각에 보유 현황 + 시그널 후보 텔레그램 전송

### 매주 자동
- 일요일 03:00 UTC: keepalive ping
- 일요일 04:00 UTC: DB 백업 상태 점검 (Turso 자체 백업)

### 종목 마스터 갱신
- 앱 열 때마다 마지막 갱신 후 3시간 지났으면 자동 갱신
- 수동 갱신: ⚙️ 설정 → "🔄 지금 갱신"

---

## 5. 앞으로 보강할 수 있는 것 (선택)

### 즉시 가능 (사용자 작업 후 활성)
- ☐ Turso 가입 → 폰에서 데이터 영속화
- ☐ 텔레그램 봇 → 자동 브리핑
- ☐ Gemini 키 → LLM 코멘트
- ☐ Streamlit Cloud 배포 → 폰 접속

### Phase 8 후보 (코드 보강 필요, 약 1주 분량)
- ☐ 분봉 데이터 (5분/30분/1시간)
- ☐ 지정가 주문 (시장가 외)
- ☐ 옵션/선물 시뮬레이션
- ☐ 포트폴리오 최적화 (마코위츠/리스크 패리티)
- ☐ 머신러닝 시그널 (LightGBM)
- ☐ 알림 채널 확장 (이메일, Discord)

### Phase 9 후보 (장기)
- ☐ 실주문 연동 — **본 도구 정책상 금지**. 별도 프로젝트로 분리 필요.
- ☐ 다중 사용자 (로그인 + 멀티테넌트)

### 잔여 개선 사항 (선택, 우선순위 낮음)
- ☐ 백테스트 결과 DB 영속화 후 과거 결과 비교 UI
- ☐ 시그널 가중치 튜닝 UI (현재는 코드 상수)
- ☐ 한국 종목 마스터 100→2000개 자동 확장 (현재 96개 정적)
- ☐ 분기별 무료 API 한도 재확인 자동화

---

## 6. 자주 쓰는 명령어 (로컬)

```powershell
# 가상환경 활성화
.venv\Scripts\activate

# 앱 실행
streamlit run src/ui/app.py

# 테스트
pytest -v --cov=src

# 린트
ruff check src/ tests/
mypy src/

# 종목 마스터 동기화 (CLI)
python -c "from src.symbols import refresh_kr_from_krx; print(refresh_kr_from_krx())"

# 브리핑 수동 발송 (CLI, 텔레그램 설정 필요)
python -m scripts.briefing_cli --slot "12:00"
```

---

## 7. 문제 발생 시

### "Streamlit 시작이 안 됨"
- `docs/TROUBLESHOOTING.md` Streamlit 항목 참고
- 포트 충돌이면 `--server.port 8502`

### "거래기록이 사라짐"
- Streamlit Cloud 무료는 디스크 휘발성. **Turso 설정 필수**.
- 로컬은 `data/db/swing.db` 파일이 진실 소스.

### "yfinance 데이터 안 받아짐"
- yfinance는 차단 빈번. 코드가 자동으로 FinanceDataReader로 폴백.
- 두 소스 모두 실패하면 캐시 사용, 그것도 없으면 명시적 에러.

### "거래세 0.18% 인 줄 알았는데"
- 2026-01-01 시행 인상으로 **KOSPI/KOSDAQ 모두 0.20%**.
- 출처: 기획재정부 2025년 세제개편안.

### "Python 3.14 호환 라이브러리 없음"
- libsql_client 등 일부 미배포. 로컬에서는 자동 폴백.
- Streamlit Cloud는 3.11 사용하므로 정상 작동.

### 그 외
- `docs/TROUBLESHOOTING.md` 전체 참고
- GitHub Issues 에 등록

---

## 8. 면책 (재확인)

⚠️ 본 도구는 **페이퍼 트레이딩 전용**이며, 실주문 기능이 없습니다.
⚠️ 모든 시그널/분석은 **참고용**이며 매수/매도 권유가 아닙니다.
⚠️ 모든 투자 결정과 결과의 **책임은 사용자 본인**에게 있습니다.
⚠️ 페이퍼 트레이딩 결과가 **실거래 성과를 보장하지 않습니다**.

---

## 9. 인수인계 체크리스트

다음 한 가지부터 진행하면 됨 (위 순서):

- [ ] (필수) Turso 가입 → DB 생성 → URL/토큰 메모
- [ ] (필수) Streamlit Cloud 배포 → Secrets 입력 → URL 발급
- [ ] (필수) 폰에서 URL 접속 → 즐겨찾기
- [ ] (선택) Telegram @BotFather 봇 생성 → 토큰/chat_id Secrets 등록
- [ ] (선택) Gemini API key 발급 → Secrets 등록
- [ ] (선택) STREAMLIT_APP_URL Secrets 등록 (sleep 방지)
- [ ] (참고) docs/DEPLOYMENT.md 4단계 가이드 정독

---

## 10. 비용 (재확인)

- GitHub Private repo: ₩0
- Turso 무료 티어: ₩0 (9GB / 월 10억 reads)
- Streamlit Cloud Community: ₩0 (1앱 / 12h sleep)
- GitHub Actions: ₩0 (월 2000분, 우리 사용량 약 210분)
- Telegram Bot: ₩0
- Gemini API 무료 티어: ₩0 (일 500회, 우리 사용 7회/일)
- Groq 무료 티어: ₩0 (일 14,400회)
- **합계: ₩0**

분기 1회 무료 한도 재확인 권장.
