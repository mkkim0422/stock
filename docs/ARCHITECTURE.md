# ARCHITECTURE — 시스템 구조

## 전체 다이어그램
```
+-------------------+      +------------------+
| GitHub Actions    | ---> | Briefing pipeline|
| (7회/일, Phase 7) |      | (Phase 6)        |
+-------------------+      +---------+--------+
                                     |
+-------------------+                v
| Streamlit UI      | <--------+ Notifications (telegram, Phase 6)
| (app.py+ 8 pages) |          |
+--------+----------+          |
         |                     |
         v                     |
+-------------------+    +-----+------+   +-------------+
| Paper Trader      | -> | Portfolio  |-->| Performance |
| (slippage/fees/   |    | (state)    |   |             |
|  spread/CA)       |    +------------+   +-------------+
+--------+----------+
         ^
         |
+--------+----------+
| Collectors (mock) | <- Phase 2: pykrx/yfinance/FDR
+--------+----------+
         ^
         |
+--------+----------+    +----------------+   +-----------+
| Indicators        |--> | Signals (P3)   |-->| LLM (P5)  |
| (RSI/MACD/MA)     |    +----------------+   +-----------+
+-------------------+

+-----------------------+
| SQLite (WAL)          |  data/db/swing.db
| trades, positions,    |
| signals, prices,      |
| portfolio_snapshots   |
+-----------------------+
```

## 모듈 책임
| 모듈 | 책임 | Phase |
|---|---|---|
| `config/` | settings, constants | 1 |
| `utils/` | logger, timezone, calendar | 1 |
| `storage/` | SQLite WAL, migrations | 1 |
| `collectors/` | base + mock (Phase 2: real) | 1 |
| `symbols/` | 종목 마스터 (static→dynamic Phase 2) | 1 |
| `paper/` | 가상매매 엔진 | 1 |
| `indicators/` | 기술 지표 (직접 구현) | 1 |
| `signals/` | 시그널 생성 | 3 |
| `llm/` | LLM 보조 | 5 |
| `notifications/` | 텔레그램 | 6 |
| `backtest/` | look-ahead/survivorship/OOS/WF | 1 (가드) |
| `ui/` | Streamlit | 1 |

## 데이터 흐름 (Phase 1)
1. UI에서 "AAPL 5주 매수" 클릭
2. `paper/trader.execute_order()` 호출
3. mock collector에서 현재가 조회
4. fx 환산 → slippage → fee → portfolio 갱신
5. SQLite trades 테이블 insert
6. UI 새로고침

## 데이터 흐름 (Phase 6 예고)
1. GitHub Actions cron 발화
2. collectors → 실시간 시세 수집
3. indicators → 지표 계산
4. signals → +8/-3 가중치
5. llm → 코멘트 생성
6. notifications → 텔레그램 전송

## 키 결정
- **로컬 우선**: 모든 상태는 로컬 SQLite. 클라우드 동기화는 옵션.
- **fail-safe 기본값**: 데이터 누락 시 거래 중단, 사용자 알림.
- **Phase 게이팅**: 각 Phase 모듈은 NotImplementedError 로 미완성을 명시.
