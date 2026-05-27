"""백테스트 엔진 — 시그널 기반 매매 시뮬레이션 (look-ahead 가드 포함).

원칙:
- 시그널 평가는 t 시점 종가까지만 사용 (look-ahead 가드).
- 체결은 t+1 시가에 슬리피지/수수료/거래세 반영.
- 단일 종목 single-position 모델 (포지션 1개 또는 현금).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pandas as pd

from src.backtest.lookahead_guard import check_no_lookahead
from src.backtest.metrics import Metrics, compute
from src.config.constants import (
    FEE_RATE_KR,
    FEE_RATE_US,
    INITIAL_CAPITAL_KRW,
    SLIPPAGE_RATE,
    TAX_RATE_KR,
)
from src.signals.engine import evaluate as evaluate_signal


@dataclass(slots=True)
class BacktestResult:
    equity_curve: pd.Series
    trades: list[dict]
    metrics: Metrics
    final_value: float
    cash_end: float

    def persist(self, symbol: str, market: str, mode: str = "full") -> int:
        """결과 메트릭을 backtest_results 테이블에 기록. 반환: id."""
        from src.storage import connect
        from src.utils.timezone import now_kst

        with connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO backtest_results
                (ts, symbol, market, period_start, period_end, mode,
                 total_return_pct, cagr_pct, sharpe, sortino,
                 max_drawdown_pct, win_rate_pct, profit_factor,
                 n_trades, final_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_kst().isoformat(timespec="seconds"),
                    symbol, market,
                    self.metrics.start.isoformat(),
                    self.metrics.end.isoformat(),
                    mode,
                    Decimal(str(self.metrics.total_return_pct)),
                    Decimal(str(self.metrics.cagr_pct)),
                    Decimal(str(self.metrics.sharpe)),
                    Decimal(str(self.metrics.sortino)),
                    Decimal(str(self.metrics.max_drawdown_pct)),
                    Decimal(str(self.metrics.win_rate_pct)),
                    Decimal(str(self.metrics.profit_factor)),
                    self.metrics.n_trades,
                    Decimal(str(self.final_value)),
                ),
            )
            return cur.lastrowid or 0


def _market_fees(market: str) -> tuple[Decimal, Decimal]:
    if market == "KR":
        return FEE_RATE_KR, TAX_RATE_KR
    return FEE_RATE_US, Decimal(0)


def run_single(
    symbol: str,
    df: pd.DataFrame,
    market: str = "KR",
    initial_capital: Decimal = INITIAL_CAPITAL_KRW,
    warmup_bars: int = 200,
) -> BacktestResult:
    """단일 종목 백테스트.

    df: OHLCV. 인덱스: date.
    warmup_bars: 시그널 계산을 위한 초기 데이터 보유 봉 수.
    """
    if df.empty or len(df) < warmup_bars + 2:
        raise ValueError("백테스트 데이터 부족 (warmup + 2 이상 필요)")

    df = df.sort_index().copy()
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["volume"] = df["volume"].astype(float)

    fee_rate, tax_rate = _market_fees(market)
    slip = SLIPPAGE_RATE

    cash = Decimal(initial_capital)
    qty = 0
    avg_price = Decimal(0)
    entry_date: date | None = None
    trades: list[dict] = []
    equity_dates: list = []
    equity_values: list[float] = []

    dates = list(df.index)

    for i in range(warmup_bars, len(dates) - 1):
        next_d = dates[i + 1]

        hist = df.iloc[: i + 1]
        check_no_lookahead(
            hist, next_d if isinstance(next_d, date) else next_d.date()
        )

        sig = evaluate_signal(symbol, hist)
        next_open = Decimal(str(df.iloc[i + 1]["open"]))

        if sig.action == "BUY" and qty == 0:
            fill = next_open * (Decimal(1) + slip)
            shares_max = int(cash // (fill * (Decimal(1) + fee_rate)))
            if shares_max > 0:
                notional = fill * Decimal(shares_max)
                fee = notional * fee_rate
                cash -= notional + fee
                qty = shares_max
                avg_price = fill
                entry_date = next_d if isinstance(next_d, date) else next_d.date()

        elif sig.action == "SELL" and qty > 0:
            fill = next_open * (Decimal(1) - slip)
            notional = fill * Decimal(qty)
            fee = notional * fee_rate
            tax = notional * tax_rate
            proceeds = notional - fee - tax
            cash += proceeds
            pnl = float((fill - avg_price) * Decimal(qty) - fee - tax)
            exit_date = next_d if isinstance(next_d, date) else next_d.date()
            trades.append({
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": float(avg_price),
                "exit_price": float(fill),
                "qty": qty,
                "pnl": pnl,
            })
            qty = 0
            avg_price = Decimal(0)
            entry_date = None

        mtm = cash + (
            Decimal(str(df.iloc[i + 1]["close"])) * Decimal(qty)
            if qty else Decimal(0)
        )
        equity_dates.append(next_d)
        equity_values.append(float(mtm))

    # 잔여 포지션 청산
    if qty > 0:
        last_close = Decimal(str(df.iloc[-1]["close"]))
        fill = last_close * (Decimal(1) - slip)
        notional = fill * Decimal(qty)
        fee = notional * fee_rate
        tax = notional * tax_rate
        cash += notional - fee - tax
        pnl = float((fill - avg_price) * Decimal(qty) - fee - tax)
        exit_d = dates[-1] if isinstance(dates[-1], date) else dates[-1].date()
        trades.append({
            "entry_date": entry_date,
            "exit_date": exit_d,
            "entry_price": float(avg_price),
            "exit_price": float(fill),
            "qty": qty,
            "pnl": pnl,
        })

    equity = pd.Series(equity_values, index=equity_dates)
    metrics = compute(equity, trades)
    return BacktestResult(
        equity_curve=equity,
        trades=trades,
        metrics=metrics,
        final_value=float(equity.iloc[-1]) if not equity.empty else float(initial_capital),
        cash_end=float(cash),
    )
