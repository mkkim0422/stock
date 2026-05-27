# ROADMAP

## Phase 1 (현재) — 골격 + 작동 가상투자
- 폴더/문서/skills/agents 골격
- 검증 시스템 (ruff/mypy/pytest)
- 작동 가상투자 (fixtures)
- 로컬 SQLite + WAL
- Streamlit UI (4_PaperTrading, 5_Results 작동)
- 보안/면책 시스템

## Phase 2 — 실데이터 수집 (완료)
- pykrx (한국) — `src/collectors/kr.py`
- yfinance + FinanceDataReader 폴백 (미국) — `src/collectors/us.py`
- exchangerate.host → open.er-api.com 폴백 → 캐시 (환율) — `src/collectors/fx.py`
- prices/fx_cache SQLite 캐싱 — `src/collectors/cache.py`
- 종목 마스터 DB-backed + KRX 동적 갱신 — `src/symbols/master.refresh_kr_from_krx()`
- 시장 개장/마감 시간 — `src/utils/market_hours.py` (KR/US 시장 시간 외 주문은 다음 정규장 시가로 자동 조정)
- UI: 2_Market (KOSPI/KOSDAQ/S&P/NASDAQ 6개월 차트), 3_Stocks (캔들+MA+RSI+MACD)
- 환경변수 `USE_MOCK=1` 로 외부 호출 차단 (테스트/오프라인)
- Turso: 다음 Phase 검토 (필요성 낮음 — 로컬 SQLite로 충분)

## Phase 3 — 지표/시그널 엔진 (완료)
- RSI/MACD/MA + VR/OBV 거래량 지표
- 가중치 +8 매수 / -3 매도 결합
- `src/signals/engine.py` + `components.py`
- DB `signals` 테이블 자동 기록
- UI 9_Signals.py — 워치리스트 모니터링 (점수 정렬, 색상)
- 워치리스트: 종목 추가/삭제, DB `watchlist` 테이블

## Phase 4 — 백테스트 엔진 (완료)
- `src/backtest/engine.py` — single-position 시뮬레이터, look-ahead 가드 포함
- `src/backtest/metrics.py` — CAGR, Sharpe, Sortino, MDD, 승률, Profit Factor
- `src/backtest/walk_forward.py` — 슬라이딩 윈도우 (train/test)
- `src/backtest/out_of_sample.py` — 70/30 분할
- 거래비용 자동 적용 (수수료 + 거래세 + 슬리피지)
- UI 6_Backtest.py — 종목 선택 → 백테스트 실행 → 자산곡선/메트릭/거래내역

## Phase 5 — LLM 보조 (완료)
- `src/llm/gemini.py` — Gemini 2.5 Flash REST
- `src/llm/groq.py` — Groq Llama (OpenAI 호환)
- `src/llm/__init__.get_llm()` — 환경변수 분기 (Gemini → Groq → None)
- `generate_signal_comment()` — 시그널 결과를 한국어 2-3문장 요약

## Phase 6 — 텔레그램 브리핑 (완료)
- `src/notifications/telegram.py` — Bot API (Markdown, 4096자 truncate)
- `src/notifications/briefing.py` — 시장상태+보유+시그널 후보 종합
- `scripts/briefing_cli.py` — CLI 진입점 (cron 호출용)
- DB `briefings` 테이블에 모든 발화 기록 (sent/failed/skipped)

## Phase 7 — 자동 운영 (완료)
- 7개 briefing-*.yml cron 활성 (KST 07:00/09:30/12:00/14:30/16:00/18:00/23:30)
- keepalive-weekly.yml — Streamlit Cloud 12h sleep 회피
- db-backup-weekly.yml — Turso 자체 백업 상태 점검
- GitHub Secrets 사용: TELEGRAM_BOT_TOKEN/CHAT_ID, TURSO_*, GEMINI_API_KEY, GROQ_API_KEY
- cron 지연 15~30분 정상 (브리핑 메시지에 실제 발화 시각 명시)

## Phase 8+ (검토)
- 분봉 데이터
- 옵션/선물 (페이퍼)
- 포트폴리오 최적화
