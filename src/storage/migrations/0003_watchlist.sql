-- 관심 종목 (시그널 모니터링 대상).
CREATE TABLE IF NOT EXISTS watchlist (
    symbol      TEXT PRIMARY KEY,
    added_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
