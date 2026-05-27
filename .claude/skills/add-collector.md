---
name: add-collector
description: 새 데이터 소스 collector 추가 (인터페이스 준수, 폴백 등록)
---

# add-collector skill

## 언제 사용 (Phase 2+)
- 새 시세 소스 추가
- 환율 소스 추가

## 원칙
- `src/collectors/base.py`의 abstract 인터페이스 구현
- 메서드: `fetch_ohlcv(symbol, start, end)`, `fetch_realtime(symbol)`
- tenacity 백오프 필수
- 캐시 (SQLite `prices` 테이블)
- 폴백 등록: `src/collectors/__init__.py`의 우선순위 리스트에 추가

## 단계
1. `src/collectors/<source>.py` 새 파일
2. base 상속, 메서드 구현
3. tenacity 데코레이터
4. `tests/test_collectors/test_<source>.py` — mock으로 단위 테스트
5. docs/DATA_FALLBACK.md 폴백 순서 갱신
6. Phase 1은 mock 만, 실제 호출 금지

## 주의
- API 키 .env, 절대 커밋 X
- 429 처리 필수
