---
name: update-ui-page
description: Streamlit 페이지를 docs/UI_GUIDE.md 의 UX 원칙대로 추가/수정
---

# update-ui-page skill

## 언제 사용
- 새 페이지 추가
- 기존 페이지 개선

## 파일명 규약
- `src/ui/pages/<N>_<EnglishName>.py` (영문 prefix, 한글 금지)
- 페이지 안에서 `st.title("아이콘 한글 제목")` 으로 한글 표시

## UX 원칙 (docs/UI_GUIDE.md 참고)
1. 정보 위계: KPI 카드 → 표/차트 → 액션 → 로그
2. 색상 의미: 초록=수익, 빨강=손실, 파랑=중립
3. 빈 상태 안내 필수
4. 로딩 인디케이터 (`st.spinner`)
5. 숫자 포맷: 천단위 콤마, 통화 prefix
6. 사이드바: 모드, 평가액, 갱신시각
7. 푸터 면책 1줄
8. 확인 단계 (액션 → 미리보기 → 확정)
9. 차트는 plotly만

## 단계
1. 파일 생성 (영문명)
2. 위 원칙 적용
3. `src/ui/components/` 재사용 부품 활용
4. `streamlit run src/ui/app.py` 로 시각 확인
5. tests/ 에서 import 가능 여부 확인

## 금지
- matplotlib 사용 (plotly만)
- 한국어 파일명
- KPI 없는 결과 페이지
- 면책 없는 페이지
