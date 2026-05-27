---
name: db-migration
description: SQLite 마이그레이션 추가 (멱등성, WAL, 인덱스)
---

# db-migration skill

## 언제 사용
- 테이블/컬럼 추가
- 인덱스 추가
- 새 Phase 의 데이터 모델 변경

## 원칙
- 멱등성: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
- 파일명: `src/storage/migrations/000N_short_name.sql`
- N은 순서대로 (0001, 0002, ...)
- 기존 파일 수정 금지 — 새 파일로 추가
- WAL 모드 유지

## 단계
1. 새 sql 파일 작성
2. `src/storage/db.py`의 `apply_migrations()` 가 자동으로 실행
3. `pytest tests/test_storage/` 통과 확인
4. 기존 DB 가 있다면 백업 후 적용

## 주의
- 컬럼 삭제는 SQLite 가 어려움 → 새 테이블 + 데이터 이전 + RENAME
- 외래키 변경은 신중
