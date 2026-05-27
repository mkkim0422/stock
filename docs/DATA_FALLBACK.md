# DATA_FALLBACK — 다중 소스 폴백 (Phase 2 활성)

## Phase 1 현황
인터페이스 정의만. 실제 호출은 Phase 2.

## 폴백 순서
### 한국
1. pykrx (KRX 직접)
2. FinanceDataReader
3. 마지막 성공 캐시
4. 실패 → 거래 중단 + 알림

### 미국
1. yfinance
2. FinanceDataReader
3. (옵션) Polygon.io 무료 티어
4. 마지막 성공 캐시
5. 실패 → 거래 중단

### 환율
1. exchangerate.host
2. open.er-api.com
3. ECB 일별 (느림)
4. 마지막 성공 캐시 (24시간 이내)

## 캐시 정책
- 봉 데이터: SQLite `prices` 테이블 영구 저장
- 환율: 1일 TTL, `fx_cache` 테이블
- 종목 마스터: 1일 TTL

## 에러 분류
- 429 (rate limit): tenacity 지수 백오프, 다음 소스
- 5xx: 다음 소스
- 4xx (비인증): 다음 소스, 알림
- 데이터 누락: NaN 표시, 거래 중단

## 무결성 체크
- 가격 0 또는 음수 → 거부
- 거래량 음수 → 거부
- 비정상 갭 (전일대비 ±50%) → 액션 조정 여부 검사 (분할/배당)
