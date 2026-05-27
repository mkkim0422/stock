-- 시스템 메타데이터 (마지막 갱신 시각 등).
CREATE TABLE IF NOT EXISTS system_meta (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
