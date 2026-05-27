"""fixtures CSV 생성기. 결정적 (random seed 고정)."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent


def gen_random_walk(start_price: float, days: int, vol: float, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0005, vol, size=days)
    closes = start_price * np.cumprod(1 + rets)
    rows = []
    d = date(2025, 5, 27)
    for i in range(days):
        c = float(closes[i])
        o = c * (1 + rng.normal(0, vol * 0.3))
        h = max(o, c) * (1 + abs(rng.normal(0, vol * 0.5)))
        low = min(o, c) * (1 - abs(rng.normal(0, vol * 0.5)))
        v = int(abs(rng.normal(1_000_000, 200_000)))
        rows.append({
            "date": d.isoformat(),
            "open": round(o, 2),
            "high": round(h, 2),
            "low": round(low, 2),
            "close": round(c, 2),
            "volume": v,
        })
        d += timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
    return rows


def main() -> None:
    # 한국 종목
    kr_specs = [
        ("005930", "삼성전자", 70_000, 0.015, 11),
        ("000660", "SK하이닉스", 130_000, 0.020, 12),
        ("035720", "카카오", 50_000, 0.025, 13),
    ]
    kr_rows = []
    for sym, _name, p0, vol, seed in kr_specs:
        for r in gen_random_walk(p0, 252, vol, seed):
            kr_rows.append({"symbol": sym, **r})

    kr_file = OUT / "sample_prices_kr.csv"
    with kr_file.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol", "date", "open", "high", "low", "close", "volume"])
        w.writeheader()
        w.writerows(kr_rows)

    # 미국 종목
    us_specs = [
        ("AAPL", "Apple", 200.0, 0.018, 21),
        ("MSFT", "Microsoft", 400.0, 0.016, 22),
        ("NVDA", "NVIDIA", 120.0, 0.030, 23),
    ]
    us_rows = []
    for sym, _name, p0, vol, seed in us_specs:
        for r in gen_random_walk(p0, 252, vol, seed):
            us_rows.append({"symbol": sym, **r})

    us_file = OUT / "sample_prices_us.csv"
    with us_file.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol", "date", "open", "high", "low", "close", "volume"])
        w.writeheader()
        w.writerows(us_rows)

    # 환율 (1,350 ± 노이즈)
    rng = np.random.default_rng(99)
    fx_rows = []
    d = date(2025, 5, 27)
    for _ in range(252):
        fx_rows.append({"date": d.isoformat(), "krw_per_usd": round(1350 + rng.normal(0, 15), 2)})
        d += timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)

    fx_file = OUT / "sample_fx.csv"
    with fx_file.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "krw_per_usd"])
        w.writeheader()
        w.writerows(fx_rows)


if __name__ == "__main__":
    main()
    print("fixtures generated")
