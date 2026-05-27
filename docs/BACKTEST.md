# BACKTEST — 백테스트 무결성

## Phase 1 현황
무결성 가드만 구현. 엔진은 Phase 4.

## look-ahead bias 방지
- `src/backtest/lookahead_guard.py`
- 모든 시그널/지표 입력은 `t-1` 까지만 허용
- t 시점 의사결정은 t+1 시가에서 체결
- 가드 함수가 미래 데이터 접근 시 예외 발생

## survivorship bias
- 상폐 종목 포함 (Phase 4 데이터셋)
- 상장폐지일 이후 거래 차단
- Phase 1 mock 은 생존 종목만 사용 (한계 명시)

## OOS (Out-of-Sample)
- 학습기간 / 검증기간 분리
- 검증기간 모델 변경 금지

## 워크포워드
- 슬라이딩 윈도우: 학습 N개월 → 검증 1개월 → 슬라이드
- 모든 윈도우 평균 + 분산 보고

## 메트릭 (Phase 4)
- CAGR, Sharpe, Sortino, MDD, 승률, Profit Factor
- 거래비용 포함 (수수료 + 세금 + 슬리피지)
