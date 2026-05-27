# SIGNALS — 시그널 엔진

## 현재 상태 (Phase 3 활성)
- `src/signals/engine.py` — `evaluate(symbol, ohlcv_df)` / `evaluate_and_persist()`
- `src/signals/components.py` — 컴포넌트별 점수 함수
- `src/signals/base.py` — `SignalOutput` 데이터클래스
- DB `signals` 테이블에 모든 평가 기록
- UI 9_Signals.py — 워치리스트 종목 실시간 모니터링

## 가중치 (확정)
- 매수 강도 기준점: **+8**
- 매도 강도 기준점: **-3** (보수적, 손절 빠르게)

## 가중치 (구현 완료)
| 컴포넌트 | 조건 | 점수 |
|---|---|---|
| RSI | <30 (과매도) | +2 |
| RSI | >70 (과매수) | -2 |
| MACD | 히스토그램 - → + (골든크로스) | +3 |
| MACD | 히스토그램 + → - (데드크로스) | -3 |
| MA20 | 종가 > MA20 | +1 |
| MA60 | 종가 > MA60 | +1 |
| MA200 | 종가 > MA200 | +1 |
| 단기과열 | 5거래일 +5% 이상 | -1 |
| 거래량 | 20봉 평균 2배+ | +2 |
| OBV | 20봉 평균 위 (매집) | +1 |

이론적 최대 +10 / 최소 -6.

## 결합 규칙
- 합산 점수 ≥ +8 → 매수 후보
- 합산 점수 ≤ -3 → 매도 후보
- 그 사이: 관망

## 출력
- timestamp, symbol, score, components(JSON), action
- DB `signals` 테이블 저장

## 백테스트 (Phase 4)
- 위 가중치는 워크포워드 최적화 대상
- OOS 검증 필수
