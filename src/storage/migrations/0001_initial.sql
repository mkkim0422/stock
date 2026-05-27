-- 0001_initial.sql — Phase 1 모든 테이블 (Decimal 컬럼 적용)
-- 멱등성: 모든 CREATE 는 IF NOT EXISTS
-- 금액/가격 컬럼: DECIMAL_TEXT 선언 → SQLite TEXT affinity (정밀도 보존)
-- Python sqlite3 PARSE_DECLTYPES + register_converter("DECIMAL_TEXT") 로 Decimal 자동 변환.

CREATE TABLE IF NOT EXISTS symbols (
    symbol      TEXT PRIMARY KEY,
    market      TEXT NOT NULL CHECK(market IN ('KR','US')),
    name        TEXT NOT NULL,
    name_kr     TEXT,
    sector      TEXT,
    delisted    INTEGER NOT NULL DEFAULT 0,
    delisted_at TEXT,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prices (
    symbol      TEXT NOT NULL,
    date        TEXT NOT NULL,
    open        DECIMAL_TEXT NOT NULL,
    high        DECIMAL_TEXT NOT NULL,
    low         DECIMAL_TEXT NOT NULL,
    close       DECIMAL_TEXT NOT NULL,
    volume      INTEGER NOT NULL CHECK(volume >= 0),
    adj_close   DECIMAL_TEXT,
    PRIMARY KEY (symbol, date),
    CHECK(CAST(open AS REAL) > 0 AND CAST(high AS REAL) > 0
          AND CAST(low AS REAL) > 0 AND CAST(close AS REAL) > 0),
    CHECK(CAST(high AS REAL) >= CAST(low AS REAL)),
    CHECK(CAST(high AS REAL) >= CAST(open AS REAL)
          AND CAST(high AS REAL) >= CAST(close AS REAL)),
    CHECK(CAST(low AS REAL)  <= CAST(open AS REAL)
          AND CAST(low AS REAL)  <= CAST(close AS REAL))
);

CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date);

CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    market          TEXT NOT NULL CHECK(market IN ('KR','US')),
    side            TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
    qty             INTEGER NOT NULL CHECK(qty > 0),
    fill_price      DECIMAL_TEXT NOT NULL CHECK(CAST(fill_price AS REAL) > 0),
    slippage_amt    DECIMAL_TEXT NOT NULL DEFAULT '0',
    fee_amt         DECIMAL_TEXT NOT NULL DEFAULT '0',
    tax_amt         DECIMAL_TEXT NOT NULL DEFAULT '0',
    fx_rate         DECIMAL_TEXT,
    cash_delta_krw  DECIMAL_TEXT NOT NULL,
    cash_delta_usd  DECIMAL_TEXT NOT NULL DEFAULT '0',
    realized_pnl    DECIMAL_TEXT,
    note            TEXT
);

CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_ts ON trades(ts);

CREATE TABLE IF NOT EXISTS positions (
    symbol      TEXT PRIMARY KEY,
    market      TEXT NOT NULL CHECK(market IN ('KR','US')),
    qty         INTEGER NOT NULL CHECK(qty >= 0),
    avg_price   DECIMAL_TEXT NOT NULL CHECK(CAST(avg_price AS REAL) >= 0),
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    date                 TEXT PRIMARY KEY,
    cash_krw             DECIMAL_TEXT NOT NULL,
    cash_usd             DECIMAL_TEXT NOT NULL,
    fx_rate              DECIMAL_TEXT NOT NULL,
    positions_value_krw  DECIMAL_TEXT NOT NULL,
    total_value_krw      DECIMAL_TEXT NOT NULL,
    daily_pnl_krw        DECIMAL_TEXT NOT NULL DEFAULT '0'
);

CREATE TABLE IF NOT EXISTS fx_cache (
    date        TEXT PRIMARY KEY,
    krw_per_usd DECIMAL_TEXT NOT NULL CHECK(CAST(krw_per_usd AS REAL) > 0)
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
    cash_krw        DECIMAL_TEXT NOT NULL,
    cash_usd        DECIMAL_TEXT NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS corporate_actions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol      TEXT NOT NULL,
    ex_date     TEXT NOT NULL,
    kind        TEXT NOT NULL CHECK(kind IN ('SPLIT','DIVIDEND')),
    ratio_num   INTEGER,
    ratio_den   INTEGER,
    dividend    DECIMAL_TEXT,
    applied_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_ca_symbol ON corporate_actions(symbol);
