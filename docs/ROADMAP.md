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

## Phase 4 — 백테스트 엔진
- 워크포워드
- OOS 검증
- 메트릭 (CAGR, Sharpe, Sortino, MDD)
- 거래비용 포함

## Phase 5 — LLM 보조
- Gemini Flash
- Groq Llama
- 시그널 코멘트, 종목 요약

## Phase 6 — 텔레그램 브리핑
- 7회/일 브리핑
- 보유/시그널/시장 요약
- 발화 시각 보정 (cron 지연 명시)

## Phase 7 — 무중단 운영
- GitHub Actions 활성
- Streamlit Cloud 배포
- keepalive
- DB 백업 자동
- security audit 주기화

## Phase 8+ (검토)
- 분봉 데이터
- 옵션/선물 (페이퍼)
- 포트폴리오 최적화
