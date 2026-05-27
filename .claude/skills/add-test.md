---
name: add-test
description: pytest 테스트 추가 (fixtures 활용, 커버리지 유지)
---

# add-test skill

## 언제 사용
- 새 함수/모듈 추가 시 (TDD 권장)
- 버그 회귀 방지

## 디렉토리
- 단위: `tests/test_<module>/test_<file>.py`
- 통합: `tests/test_integration/test_<scenario>.py`

## fixtures
- `tests/conftest.py`에 공통 fixture
- `tests/fixtures/*.csv` 가격 데이터

## 원칙
- AAA: Arrange, Act, Assert
- 1 테스트 = 1 동작
- 외부 호출 mock (Phase 1은 외부 호출이 없으므로 거의 불필요)
- 부동소수 비교: `pytest.approx` 또는 `Decimal`

## 단계
1. 테스트 파일 생성
2. fixture 활용
3. `pytest -v tests/test_xxx.py` 통과
4. `pytest --cov=src` 커버리지 확인
5. commit

## 커버리지 목표
- src/paper, src/utils: 90%+
- 전체: 70%+
