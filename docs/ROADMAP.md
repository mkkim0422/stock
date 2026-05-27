# ROADMAP

## Phase 1 (현재) — 골격 + 작동 가상투자
- 폴더/문서/skills/agents 골격
- 검증 시스템 (ruff/mypy/pytest)
- 작동 가상투자 (fixtures)
- 로컬 SQLite + WAL
- Streamlit UI (4_PaperTrading, 5_Results 작동)
- 보안/면책 시스템

## Phase 2 — 실제 데이터 수집
- pykrx (한국)
- yfinance + FinanceDataReader 폴백 (미국)
- exchangerate.host (환율)
- 종목 마스터 동적 갱신
- Turso 검토

## Phase 3 — 지표/시그널 엔진
- RSI/MACD/MA 확장
- 거래량 지표 (VR, OBV)
- 가중치 +8/-3 결합
- DB `signals` 테이블 사용

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
