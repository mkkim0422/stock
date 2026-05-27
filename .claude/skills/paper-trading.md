---
name: paper-trading
description: 가상매매(페이퍼 트레이딩) 핵심 흐름을 검증하고 작은 주문을 실행하는 방법
---

# paper-trading skill

## 언제 사용
- 매수/매도 흐름 검증
- 새 종목 시뮬레이션
- 수수료/슬리피지/거래세 영향 확인

## 입력
- symbol (예: 005930, AAPL)
- action (buy/sell)
- qty (정수)

## 단계
1. `src/symbols/master.py` 로 종목 유효성 검사
2. `src/collectors/mock.py` 로 현재가 조회
3. `src/paper/fx.py` 로 USD 환산 (미국 종목)
4. `src/paper/slippage.py`, `fees.py` 적용
5. `src/paper/trader.execute_order()` 호출
6. SQLite `trades` insert, `positions` 업데이트
7. UI 갱신

## 주의
- Phase 1은 mock 시세만. 실제 호출 금지.
- 거래세 KOSPI/KOSDAQ 모두 0.20% (2026-01-01 시행)
- 환전 수수료 0.1%
