# TESTING — 테스트 전략

## 도구
- pytest (단위/통합)
- pytest-cov (커버리지)
- pytest-mock (mock fixtures)
- ruff (린트/포맷)
- mypy (타입)

## 디렉토리
```
tests/
  fixtures/                 # CSV 샘플
  test_utils/               # logger, timezone, calendar
  test_paper/               # fx, fees, slippage, trader
  test_storage/             # DB, migrations
  test_collectors/          # mock collector
  test_backtest/            # lookahead, survivorship
  test_indicators/          # RSI, MACD, MA
  test_integration/         # E2E 시나리오 5개
  conftest.py
```

## 커버리지 목표
- Phase 1: src/paper, src/utils 90%+
- Phase 1: 전체 70%+

## 시나리오 (E2E)
1. 매수→매도→실현손익
2. 분할매수→평단가
3. 환전→AAPL 매수
4. 거래세 0.20% (2026-01-01 시행)
5. 5:1 분할 → 평단 1/5

## 실행
```powershell
pytest -v --cov=src --cov-report=term-missing
ruff check src/ tests/
mypy src/
```

## CI (Phase 7)
- push마다 lint + test
- 실패 시 머지 차단
