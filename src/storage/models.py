"""dataclass 모델 (SQLAlchemy 없이 가볍게).

테이블 스키마는 migrations/0001_initial.sql 가 진실 소스다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Market = Literal["KR", "US"]
Side = Literal["BUY", "SELL"]


@dataclass(slots=True)
class Symbol:
    symbol: str
    market: Market
    name: str
    name_kr: str | None = None
    sector: str | None = None
    delisted: bool = False


@dataclass(slots=True)
class Trade:
    id: int | None
    ts: str
    symbol: str
    market: Market
    side: Side
    qty: int
    fill_price: float
    slippage_amt: float
    fee_amt: float
    tax_amt: float
    fx_rate: float | None
    cash_delta_krw: float
    cash_delta_usd: float
    realized_pnl: float | None
    note: str | None = None


@dataclass(slots=True)
class Position:
    symbol: str
    market: Market
    qty: int
    avg_price: float


@dataclass(slots=True)
class PortfolioSnapshot:
    date: str
    cash_krw: float
    cash_usd: float
    fx_rate: float
    positions_value_krw: float
    total_value_krw: float
    daily_pnl_krw: float
