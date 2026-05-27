# API_GUIDE — 외부 API 사용 가이드 (Phase 2+ 활성)

## 현재 상태 (Phase 2 활성)
- pykrx, yfinance + FinanceDataReader, exchangerate.host 활성
- 환경변수 `USE_MOCK=1` 로 강제 mock (테스트/오프라인)
- 모든 호출은 SQLite 캐시 우선 + tenacity 백오프 + 다중 소스 폴백

## 한국 시세
| 라이브러리 | 용도 | 무료 한도 |
|---|---|---|
| pykrx | KOSPI/KOSDAQ 일봉, 종목 마스터 | 무제한 (스크래핑) |
| FinanceDataReader | 한미 통합 (백업) | 무제한 |

주의: pykrx는 KRX 서버 부담 → 호출 간격 0.5~1초 권장.

## 미국 시세
| 라이브러리 | 용도 | 무료 한도 |
|---|---|---|
| yfinance | Yahoo Finance, 일봉/분봉 | 차단 빈번 |
| FinanceDataReader | 폴백 | 무제한 |

주의: yfinance는 Yahoo 차단/429 빈번. tenacity 백오프 + FDR 폴백 필수.

## 환율
| 소스 | 무료 한도 |
|---|---|
| exchangerate.host | 무제한 (무키) |
| open.er-api.com | 무제한 |
| ECB | 일별 |

## LLM (Phase 5)
| 제공사 | 모델 | 무료 한도 (2026-05 확인) |
|---|---|---|
| Google Gemini | gemini-2.5-flash | 분당 10회, 일일 500회 (2025-12 인하) |
| Google Gemini | gemini-2.5-flash-lite | 분당 15회, 일일 1,000회 |
| Groq | llama-3.1-8b-instant | 분당 30회, 일일 14,400회 |

발급:
- Gemini: https://aistudio.google.com/app/apikey
- Groq: https://console.groq.com/keys

## 텔레그램 (Phase 6)
- @BotFather → /newbot → 토큰
- 본인 채팅 ID: https://api.telegram.org/bot<TOKEN>/getUpdates
- 무료, 무제한.

## 폴백 전략
모든 외부 API는 **다중 소스 + tenacity 백오프 + 마지막 캐시 사용**.
docs/DATA_FALLBACK.md 참고.

## Phase 2에서 활성화될 코드 위치
- `src/collectors/kr.py` — pykrx 구현
- `src/collectors/us.py` — yfinance + FDR 폴백
- `src/collectors/fx.py` — exchangerate.host 구현
