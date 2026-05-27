"""브리핑 메시지 생성 — 시장 상태 + 보유 + 시그널 후보 종합."""
from __future__ import annotations

from datetime import date, timedelta

from src.collectors import fetch_ohlcv
from src.paper.performance import evaluate
from src.signals import evaluate as evaluate_signal
from src.storage import connect
from src.symbols.watchlist import list_all
from src.utils.market_hours import kr_status, status_label, us_status
from src.utils.timezone import now_kst


def compose_briefing(slot: str = "정시") -> str:
    """브리핑 메시지 본문 (Markdown)."""
    now = now_kst()
    kr = kr_status(now)
    us = us_status(now)
    e = evaluate()

    lines = [
        f"*[swing-advisor {slot}]* {now.strftime('%Y-%m-%d %H:%M KST')}",
        f"🇰🇷 KR: {status_label(kr)}  ·  🇺🇸 US: {status_label(us)}",
        "",
        f"💰 *평가액*: ₩{e['total_value_krw']:,.0f}  "
        f"(누적 {float(e['cum_return_pct']):+.2f}%)",
        f"📦 보유: {len(e['positions'])}개  ·  현금 KRW ₩{float(e['cash_krw']):,.0f}",
    ]

    # 보유 종목 손익 요약 (상위 5)
    if e["positions"]:
        lines.append("\n*📊 보유 포지션 (상위 5):*")
        sorted_pos = sorted(
            e["positions"], key=lambda p: float(p["pnl_pct"]), reverse=True
        )[:5]
        for p in sorted_pos:
            pnl_pct = float(p["pnl_pct"])
            emoji = "🟢" if pnl_pct >= 0 else "🔴"
            lines.append(
                f"  {emoji} `{p['symbol']}` x{p['qty']} "
                f"({pnl_pct:+.2f}%)"
            )

    # 워치리스트 시그널 후보
    watched = list_all()
    buy_candidates = []
    sell_candidates = []
    for sym in watched[:20]:
        try:
            end = date.today()
            df = fetch_ohlcv(sym, end - timedelta(days=250), end)
            if df.empty or len(df) < 60:
                continue
            sig = evaluate_signal(sym, df)
            if sig.action == "BUY":
                buy_candidates.append((sym, sig.score))
            elif sig.action == "SELL":
                sell_candidates.append((sym, sig.score))
        except Exception:
            continue

    if buy_candidates:
        lines.append("\n*🟢 매수 후보 (≥+8):*")
        for s, sc in sorted(buy_candidates, key=lambda x: -x[1])[:5]:
            lines.append(f"  • `{s}` 점수 {sc:+d}")
    if sell_candidates:
        lines.append("\n*🔴 매도 후보 (≤-3):*")
        for s, sc in sorted(sell_candidates, key=lambda x: x[1])[:5]:
            lines.append(f"  • `{s}` 점수 {sc:+d}")
    if not buy_candidates and not sell_candidates and watched:
        lines.append("\n_워치리스트 시그널: 모두 관망 (HOLD)_")

    lines.append("\n_📌 페이퍼 트레이딩. 매매 책임은 본인._")
    return "\n".join(lines)


def persist_briefing(slot: str, body: str, status: str = "sent") -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO briefings (ts, slot, body, status)
            VALUES (?, ?, ?, ?)
            """,
            (now_kst().isoformat(timespec="seconds"), slot, body, status),
        )
        return cur.lastrowid or 0


def send_briefing(slot: str) -> dict:
    """브리핑 생성 + 텔레그램 전송 + DB 기록."""
    from src.notifications.telegram import is_telegram_configured, send_message

    body = compose_briefing(slot)
    if is_telegram_configured():
        ok = send_message(body)
        status = "sent" if ok else "failed"
    else:
        status = "skipped (텔레그램 미설정)"
        ok = False
    persist_briefing(slot, body, status)
    return {"slot": slot, "ok": ok, "status": status, "body": body}
