# swing-advisor — Claude 작업 가이드

## 프로젝트 개요
- **이름**: swing-advisor
- **목적**: 한국+미국 스윙 트레이딩 보조 (개인용)
- **모드**: **페이퍼 트레이딩 전용** (실주문 코드 없음)
- **언어**: Python 3.11+
- **UI**: Streamlit
- **DB**: 로컬 SQLite (WAL 모드). Turso는 Phase 2 검토.
- **알림**: 텔레그램 (Phase 6에서 활성)
- **사용자**: 비개발자, 한국어로만 응답한다.

## 페이즈 로드맵
| Phase | 내용 | 상태 |
|---|---|---|
| 1 | 골격 + 작동 가상투자 (fixtures) | **현재** |
| 2 | 실제 데이터 수집 (pykrx, yfinance, FDR) + Turso 검토 | 예정 |
| 3 | 지표/시그널 엔진 (RSI, MACD, MA, 거래량) | 예정 |
| 4 | 백테스트 엔진 (워크포워드, OOS) | 예정 |
| 5 | LLM 보조 (Gemini/Groq 무료) | 예정 |
| 6 | 텔레그램 브리핑 (7회/일) | 예정 |
| 7 | GitHub Actions 활성 + 무중단 운영 | 예정 |

## 핵심 원칙
1. **추측 금지** — 모르면 합리적 기본값 + 보고서 기록.
2. **외부 API 호출은 Phase 2부터** — Phase 1은 `tests/fixtures/` 만 사용.
3. **pandas-ta 의존 금지** — RSI/MACD/MA는 numpy+pandas로 **직접 구현**.
4. **페이퍼 트레이딩만** — 실주문 API/키 코드 절대 작성 금지.
5. **API 키 누출 0건** — `.env`, `secrets.toml` 절대 커밋 금지.
6. **한국어 응답 필수** — 사용자는 비개발자 한국인.

## 폴더 규약
```
src/
  config/      설정/상수
  utils/       logger, timezone, calendar
  storage/     SQLite, migrations
  collectors/  데이터 수집 (Phase 1: mock만)
  symbols/     종목 마스터
  paper/       가상매매 (fx, slippage, fees, trader, portfolio)
  indicators/  지표 (직접 구현)
  signals/     시그널 (Phase 3 활성)
  llm/         LLM 보조 (Phase 5 활성)
  notifications/ 알림 (Phase 6 활성)
  backtest/    백테스트 무결성
  ui/          Streamlit (app.py + pages/)
docs/          16개 도메인 문서
tests/         pytest + fixtures
.claude/       skills, agents, hooks, settings
.github/workflows/ 11개 워크플로 (Phase 7 활성)
data/db/       로컬 SQLite
logs/          로그
```

## 핵심 수치 (변경 시 일관성 유지)
- 한국 거래세: **0.20%** (2026-01-01 시행. KOSPI 0.05%+농특세 0.15%, KOSDAQ 0.20%)
- 한국 수수료: **0.015%** (모의)
- 미국 수수료: **$0** (모의)
- 환전 수수료: **0.1%**
- 슬리피지: **0.07%** (스윙 기준)
- mock FX: **1,350 KRW/USD**
- 시그널 가중치: **+8 / -3** (매수/매도 기준점)
- 가상 초기 자본: KRW 10,000,000 + USD 10,000

## Streamlit 페이지 명명 규약
**파일명은 영문 + 번호 prefix만 사용** (한글 파일명은 URL 인코딩 문제 발생).
페이지 내부 `st.title()` 에서만 한글 표시.
```
1_Home.py        🏠 홈
2_Market.py      📈 시장
3_Stocks.py      🔍 종목
4_PaperTrading.py 💼 가상투자
5_Results.py     📊 투자결과
6_Backtest.py    🧪 백테스트
7_Settings.py    ⚙️ 설정
8_Help.py        ❓ 도움말
```

## 알려진 함정 (반드시 회피)
- **yfinance 차단/장애 빈번** → FinanceDataReader 폴백 (Phase 2)
- **GitHub Actions cron 15~30분 지연** → 정시 보장 안 됨, 마진 두기
- **Streamlit Cloud 12시간 후 sleep** → keepalive 워크플로 (Phase 7)
- **Streamlit 한글 파일명 URL 문제** → 영문 prefix만 사용
- **pandas-ta 의존 금지** → RSI/MACD/MA는 직접 구현 (수식 docs/INDICATORS.md)
- **Phase 1 외부 API 호출 금지** → fixtures만 사용
- **look-ahead bias 위험** → backtest/lookahead_guard.py 가 항상 검사
- **survivorship bias** → 상폐 종목 포함 필수 (Phase 4)
- **거래일 ≠ 영업일** → utils/calendar.py 사용
- **시간대** → KST = Asia/Seoul, US = America/New_York
- **SQLite 동시쓰기 약함** → WAL 모드 필수
- **Streamlit Cloud secrets.toml** → 직접 입력, .env 와 분리

## 검증 체크리스트 (모든 STEP 종료 시)
- [ ] `ruff check src/ tests/` 통과
- [ ] `mypy src/` 큰 에러 없음
- [ ] `pytest tests/ --cov=src` 통과, 커버리지 ≥ 70%
- [ ] CLAUDE.md ≤ 250줄
- [ ] `.env` 미커밋, `secrets.toml` 미커밋
- [ ] 핵심 수치 일관 (수수료, 슬리피지, 가중치)
- [ ] 한국어 응답 유지

## 절대 금지
- 실제 API 키 입력 (placeholder만)
- 실제 주문/체결 API 코드
- 외부 API 실제 호출 코드 (Phase 1)
- 위험 명령 (`rm -rf`, `dd`, `mkfs`, `sudo`)
- 한국어 외 보고서
- 250줄 초과 CLAUDE.md
- "죄송합니다 놓쳤습니다" 사후 사과

## 사용자 페르소나 보호
- 사용자는 비개발자. 코드 설명 시 비유 사용.
- 결정은 옵션 제시 + 추천 + 이유.
- 실패 시 원인+영향+다음 조치 명시.
- 면책: 매번 "투자 책임은 사용자 본인" 명시.

## 의존성 가드레일
허용:
- pandas, numpy, sqlalchemy, streamlit, plotly, httpx, pydantic, pydantic-settings, python-dotenv, pytz, tenacity
- (Phase 2 추가) pykrx, yfinance, FinanceDataReader
개발:
- pytest, pytest-cov, pytest-mock, ruff, mypy
금지:
- pandas-ta, ta-lib (직접 구현)
- 유료 데이터 SDK
- 실주문 SDK (kis-auto-trading 등)

## Streamlit secrets 사용 규칙
- 로컬: `.streamlit/secrets.toml` (gitignore)
- Cloud: Streamlit Cloud 대시보드에 직접 입력
- 예제: `.streamlit/secrets.toml.example` 만 커밋

## DB 사용 규칙
- 로컬 파일: `data/db/swing.db`
- WAL 모드 필수 (`PRAGMA journal_mode=WAL`)
- 마이그레이션: `src/storage/migrations/000N_*.sql` 멱등성 유지
- 백업: 주 1회 SQLite VACUUM + 복사 (Phase 7)

## 모드별 작동
- `MODE=paper` (기본) — 가상매매만
- 그 외 모드 (실주문) — **금지, 추가 금지**

## 면책
이 도구는 매수/매도 결정을 사용자에게 제안하지 않으며,
모든 투자 책임은 사용자 본인에게 있다.
페이퍼 트레이딩 결과는 실거래 결과를 보장하지 않는다.
