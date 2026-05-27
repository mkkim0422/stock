-- 백테스트 실행 결과 영속화.
CREATE TABLE IF NOT EXISTS backtest_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    market          TEXT NOT NULL,
    period_start    TEXT NOT NULL,
    period_end      TEXT NOT NULL,
    mode            TEXT NOT NULL,
    total_return_pct  DECIMAL_TEXT NOT NULL,
    cagr_pct          DECIMAL_TEXT NOT NULL,
    sharpe            DECIMAL_TEXT NOT NULL,
    sortino           DECIMAL_TEXT NOT NULL,
    max_drawdown_pct  DECIMAL_TEXT NOT NULL,
    win_rate_pct      DECIMAL_TEXT NOT NULL,
    profit_factor     DECIMAL_TEXT NOT NULL,
    n_trades          INTEGER NOT NULL,
    final_value       DECIMAL_TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bt_symbol ON backtest_results(symbol);
