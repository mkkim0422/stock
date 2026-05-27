---
name: release-phase
description: 다음 Phase 로 이동하기 전 체크리스트 및 절차
---

# release-phase skill

## 언제 사용
- 현재 Phase 완료 후, 다음 Phase 시작 전

## 공통 체크리스트
- [ ] CLAUDE.md ≤ 250줄
- [ ] ruff/mypy/pytest 통과
- [ ] 커버리지 70%+
- [ ] 키 누출 0건
- [ ] docs/ROADMAP.md 갱신
- [ ] CHANGELOG.md 항목 추가
- [ ] git tag (`phase1-complete` 등)

## Phase 별 추가
### Phase 1 → 2
- 외부 API 키 발급 (Gemini/Groq 는 Phase 5)
- collectors 실제 구현 (mock 유지하되 옵션)
- 종목 마스터 동적 갱신

### Phase 2 → 3
- 지표 모듈 완성 (RSI/MACD/MA/거래량)
- 가중치 +8/-3 검증
- signals 테이블 채움

### Phase 3 → 4
- 백테스트 엔진
- OOS/WF 검증
- 메트릭

### Phase 4 → 5
- LLM 무료 한도 재확인
- 프롬프트 캐싱

### Phase 5 → 6
- 텔레그램 봇 설정
- cron 발화 시각 검증

### Phase 6 → 7
- Streamlit Cloud 배포
- GitHub Actions 활성
- keepalive
