"""주문 체결 엔진 (시장가, 페이퍼) — Decimal 정밀도 + 원자 트랜잭션."""
from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from decimal import Decimal

from src.config.constants import INITIAL_CAPITAL_KRW, INITIAL_CAPITAL_USD
from src.paper.fees import calc_fee, calc_tax
from src.paper.fx import get_fx_rate
from src.paper.slippage import apply_slippage
from src.storage import connect


def _market_of(symbol: str) -> str:
    """심볼 마스터 조회 우선, 폴백으로 코드 형태 판별."""
    try:
        from src.symbols import load_symbols
        for s in load_symbols():
            if s.symbol == symbol:
                return s.market
    except Exception:
        pass
    return "KR" if symbol.isdigit() and len(symbol) == 6 else "US"


def execute_order(
    symbol: str,
    side: str,
    qty: int,
    quote_price: Decimal,
    ts: datetime | None = None,
) -> dict:
    """시장가 주문 체결 (단일 트랜잭션, Decimal 정밀도 유지)."""
    if side not in ("BUY", "SELL"):
        raise ValueError(f"side must be BUY or SELL, got {side!r}")
    if qty <= 0:
        raise ValueError(f"qty must be positive, got {qty}")
    if quote_price <= 0:
        raise ValueError(f"quote_price must be positive, got {quote_price}")

    market = _market_of(symbol)
    ts = ts or datetime.now(UTC)

    fill_price = apply_slippage(quote_price, side)
    notional = fill_price * Decimal(qty)
    fee = calc_fee(market, notional)
    tax = calc_tax(market, side, notional)
    fx = get_fx_rate()
    slippage_amt = abs(fill_price - quote_price) * Decimal(qty)
    realized_pnl: Decimal | None = None

    with connect() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")

            row = conn.execute(
                "SELECT cash_krw, cash_usd FROM account_cash WHERE id=1"
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO account_cash (id, cash_krw, cash_usd) VALUES (1, ?, ?)",
                    (INITIAL_CAPITAL_KRW, INITIAL_CAPITAL_USD),
                )
                cash_krw = INITIAL_CAPITAL_KRW
                cash_usd = INITIAL_CAPITAL_USD
            else:
                cash_krw = row["cash_krw"]
                cash_usd = row["cash_usd"]

            prow = conn.execute(
                "SELECT qty, avg_price FROM positions WHERE symbol=?", (symbol,)
            ).fetchone()
            pos = (int(prow["qty"]), prow["avg_price"]) if prow else None

            if side == "BUY":
                cost_local = notional + fee
                if market == "KR":
                    if cash_krw < cost_local:
                        raise ValueError(f"KRW 잔고 부족: {cash_krw} < {cost_local}")
                    cash_krw -= cost_local
                    cash_delta_krw = -cost_local
                    cash_delta_usd = Decimal(0)
                else:
                    if cash_usd < cost_local:
                        raise ValueError(f"USD 잔고 부족: {cash_usd} < {cost_local}")
                    cash_usd -= cost_local
                    cash_delta_krw = Decimal(0)
                    cash_delta_usd = -cost_local

                if pos is None:
                    new_qty, new_avg = qty, fill_price
                else:
                    old_qty, old_avg = pos
                    total_cost = old_qty * old_avg + qty * fill_price
                    new_qty = old_qty + qty
                    new_avg = total_cost / Decimal(new_qty)

            else:  # SELL
                if pos is None or pos[0] < qty:
                    held = 0 if pos is None else pos[0]
                    raise ValueError(f"보유 수량 부족: {held} < {qty}")
                old_qty, old_avg = pos
                gross_proceeds = notional - fee - tax
                realized_pnl = (fill_price - old_avg) * Decimal(qty) - fee - tax

                if market == "KR":
                    cash_krw += gross_proceeds
                    cash_delta_krw = gross_proceeds
                    cash_delta_usd = Decimal(0)
                else:
                    cash_usd += gross_proceeds
                    cash_delta_krw = Decimal(0)
                    cash_delta_usd = gross_proceeds

                new_qty = old_qty - qty
                new_avg = old_avg if new_qty > 0 else Decimal(0)

            if new_qty <= 0:
                conn.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
            else:
                conn.execute(
                    """
                    INSERT INTO positions (symbol, market, qty, avg_price)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        market=excluded.market,
                        qty=excluded.qty,
                        avg_price=excluded.avg_price,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (symbol, market, new_qty, new_avg),
                )

            conn.execute(
                "UPDATE account_cash SET cash_krw=?, cash_usd=?, "
                "updated_at=CURRENT_TIMESTAMP WHERE id=1",
                (cash_krw, cash_usd),
            )

            cur = conn.execute(
                """
                INSERT INTO trades
                (ts, symbol, market, side, qty, fill_price, slippage_amt, fee_amt, tax_amt,
                 fx_rate, cash_delta_krw, cash_delta_usd, realized_pnl, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts.isoformat(timespec="seconds"),
                    symbol,
                    market,
                    side,
                    qty,
                    fill_price,
                    slippage_amt,
                    fee,
                    tax,
                    fx,
                    cash_delta_krw,
                    cash_delta_usd,
                    realized_pnl,
                    None,
                ),
            )
            trade_id = cur.lastrowid
            conn.execute("COMMIT")
        except Exception:
            with contextlib.suppress(Exception):
                conn.execute("ROLLBACK")
            raise

    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "market": market,
        "side": side,
        "qty": qty,
        "fill_price": fill_price,
        "fee": fee,
        "tax": tax,
        "cash_delta_krw": cash_delta_krw,
        "cash_delta_usd": cash_delta_usd,
        "realized_pnl": realized_pnl,
    }
