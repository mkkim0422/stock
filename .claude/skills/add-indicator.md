---
name: add-indicator
description: 기술 지표를 numpy+pandas 로 직접 구현하고 단위 테스트를 추가하는 방법
---

# add-indicator skill

## 언제 사용
- 새 지표 추가 (RSI 변형, Stoch, Bollinger, ATR 등)

## 원칙
- **pandas-ta 의존 금지**. numpy + pandas로만.
- `src/indicators/technical.py` 또는 `volume.py`에 함수 추가
- 함수 시그니처: `def name(df: pd.DataFrame, n: int = ...) -> pd.Series`
- look-ahead 방지: 입력은 종가까지, 출력은 다음 봉 신호용
- NaN 처리: 첫 n-1 봉

## 단계
1. docs/INDICATORS.md 에 수식 추가
2. `src/indicators/technical.py`에 함수 작성
3. `tests/test_indicators/test_<name>.py`에 알려진 값으로 단위 테스트
4. ruff/mypy 통과
5. 변경 commit

## 예시 (RSI)
docs/INDICATORS.md 수식 참고.
