# COSTS — 운영 비용

## Phase 1 비용: ₩0
- 로컬 SQLite
- 외부 API 호출 없음

## Phase 2~6 예상 비용: ₩0 (무료 한도 내)
| 항목 | 무료 한도 | 예상 사용 |
|---|---|---|
| pykrx | 무제한 | OK |
| yfinance | 차단 빈번 | FDR 폴백 |
| FinanceDataReader | 무제한 | OK |
| exchangerate.host | 무제한 | OK |
| Gemini 2.5 Flash | 일 500회 (2025-12 인하) | 7회/일 → 충분 |
| Gemini 2.5 Flash-Lite | 일 1,000회 | 충분 |
| Groq llama-3.1 | 일 14,400회 | 충분 |
| 텔레그램 | 무제한 | OK |
| Streamlit Cloud | 1앱 | 1개만 |
| GitHub Actions | 월 2,000분 | 7회 cron × 30일 × 1분 = 210분/월 |
| Turso (Phase 2 검토) | 9GB / 1B reads | 충분 |

## 비용 발생 가능 시나리오
- Streamlit Cloud 유료 (8GB RAM) — 필요 시 결정
- 유료 데이터 (분봉 실시간) — Phase 7 이후 검토
- 텔레그램 4096자 초과 → 분할 전송

## 한계
- 모든 무료 한도는 변경 가능. 분기 1회 재확인.
