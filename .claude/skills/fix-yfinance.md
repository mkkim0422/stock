---
name: fix-yfinance
description: yfinance 차단/타임아웃 시 폴백 및 백오프 적용 (Phase 2+)
---

# fix-yfinance skill

## 언제 사용 (Phase 2+)
- yfinance 가 429 / Empty data 반환
- "Yahoo Finance Connection Error"

## 진단
1. 단일 종목 호출 가능?
2. 다른 IP에서 동작?
3. 사용자 ratelimit 인가, IP 차단인가?

## 조치
1. tenacity 지수 백오프 (1s → 30s, 5회)
2. `src/collectors/us.py` 의 FDR 폴백 사용
3. 마지막 캐시 사용 (`prices` 테이블)
4. 전부 실패 → 거래 중단 + 알림

## 코드 위치
- `src/collectors/us.py` (Phase 2에서 작성)
- `src/collectors/__init__.py` 폴백 우선순위

## 예방
- 호출 간격 1초+
- 한 번에 1종목씩
- ETF/지수 우선, 개별주는 뒤로
