# DB_PERSISTENCE — DB 영속성

## Phase 1: 로컬 SQLite
- 파일: `data/db/swing.db`
- 모드: WAL (`PRAGMA journal_mode=WAL`)
- 동시성: 단일 사용자 가정. WAL로 읽기/쓰기 분리.

## 테이블 (Phase 1)
- `symbols` — 종목 마스터
- `prices` — 일봉 OHLCV
- `trades` — 매매 체결 (가상)
- `positions` — 현재 포지션
- `portfolio_snapshots` — 일별 평가액
- `fx_cache` — 환율 캐시
- `signals` — 시그널 (Phase 3 채움)
- `briefings` — 브리핑 로그 (Phase 6 채움)

## 마이그레이션
- `src/storage/migrations/0001_initial.sql` — 모든 테이블 + 인덱스
- 멱등성: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
- 추가 마이그레이션은 `000N_*.sql` 형식

## 백업 (Phase 7)
- 주 1회 SQLite VACUUM + 파일 복사
- `data/backups/swing-YYYYMMDD.db`
- 보존: 8주 (이후 자동 삭제)

## Phase 2 검토: Turso
- 무료 티어: 9GB, 1B reads/month
- libsql-client 사용
- 로컬 ↔ Turso 양방향 동기화 검토
- 현재는 미사용

## 백압 복원
```powershell
copy data/backups/swing-20260520.db data/db/swing.db
```

## 무결성
- 외래키 활성: `PRAGMA foreign_keys = ON`
- 체크 제약: 가격 > 0, 수량 != 0
- 트랜잭션 필수 (매매는 atomic)
