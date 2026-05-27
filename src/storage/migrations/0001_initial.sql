-- 0001_initial.sql — Phase 1 모든 테이블
-- 멱등성: 모든 CREATE 는 IF NOT EXISTS

CREATE TABLE IF NOT EXISTS symbols (
    symbol      TEXT PRIMARY KEY,
    market      TEXT NOT NULL CHECK(market IN ('KR','US')),
    name        TEXT NOT NULL,
    name_kr     TEXT,
    sector      TEXT,
    delisted    INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prices (
    symbol      TEXT NOT NULL,
    date        TEXT NOT NULL,
    open        REAL NOT NULL CHECK(open > 0),
    high        REAL NOT NULL CHECK(high > 0),
    low         REAL NOT NULL CHECK(low > 0),
    close       REAL NOT NULL CHECK(close > 0),
    volume      INTEGER NOT NULL CHECK(volume >= 0),
    adj_close   REAL,
    PRIMARY KEY (symbol, date)
);

CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date);

CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    market          TEXT NOT NULL CHECK(market IN ('KR','US')),
    side            TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
    qty             INTEGER NOT NULL CHECK(qty > 0),
    fill_price      REAL NOT NULL CHECK(fill_price > 0),
    slippage_amt    REAL NOT NULL DEFAULT 0,
    fee_amt         REAL NOT NULL DEFAULT 0,
    tax_amt         REAL NOT NULL DEFAULT 0,
    fx_rate         REAL,
    cash_delta_krw  REAL NOT NULL,
    cash_delta_usd  REAL NOT NULL DEFAULT 0,
    realized_pnl    REAL,
    note            TEXT
);

CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_ts ON trades(ts);

CREATE TABLE IF NOT EXISTS positions (
    symbol      TEXT PRIMARY KEY,
    market      TEXT NOT NULL CHECK(market IN ('KR','US')),
    qty         INTEGER NOT NULL CHECK(qty >= 0),
    avg_price   REAL NOT NULL CHECK(avg_price >= 0),
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    date            TEXT PRIMARY KEY,
    cash_krw        REAL NOT NULL,
    cash_usd        REAL NOT NULL,
    fx_rate         REAL NOT NULL,
    positions_value_krw REAL NOT NULL,
    total_value_krw REAL NOT NULL,
    daily_pnl_krw   REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fx_cache (
    date        TEXT PRIMARY KEY,
    krw_per_usd REAL NOT NULL CHECK(krw_per_usd > 0)
);

CREATE TABLE IF NOT EXISTS signals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    score       INTEGER NOT NULL,
    components  TEXT NOT NULL,
    action      TEXT NOT NULL CHECK(action IN ('BUY','SELL','HOLD'))
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(ts);

CREATE TABLE IF NOT EXISTS briefings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    slot        TEXT NOT NULL,
    body        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'sent'
);

CREATE TABLE IF NOT EXISTS account_cash (
    id              INTEGER PRIMARY KEY CHECK(id = 1),
    cash_krw        REAL NOT NULL,
    cash_usd        REAL NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
