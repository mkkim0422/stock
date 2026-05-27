"""종목 마스터 자동 갱신 (3시간 간격).

`should_refresh()` 가 True 면 `refresh_kr_from_krx()` 를 호출하고
system_meta 에 마지막 갱신 시각을 기록.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.storage import connect

_KEY = "kr_symbols_last_refresh"
_INTERVAL = timedelta(hours=3)


def get_last_refresh() -> datetime | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT value FROM system_meta WHERE key=?", (_KEY,)
        ).fetchone()
    if row is None:
        return None
    return datetime.fromisoformat(row["value"])


def set_last_refresh(ts: datetime) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO system_meta (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                updated_at=CURRENT_TIMESTAMP
            """,
            (_KEY, ts.isoformat()),
        )


def should_refresh(now: datetime | None = None) -> bool:
    now = now or datetime.now(UTC)
    last = get_last_refresh()
    if last is None:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    return (now - last) >= _INTERVAL


def maybe_refresh() -> tuple[bool, int]:
    """3시간 지났으면 갱신. 반환: (실행여부, 영향행수)."""
    if not should_refresh():
        return False, 0
    from src.symbols.master import refresh_kr_from_krx

    n = refresh_kr_from_krx()
    set_last_refresh(datetime.now(UTC))
    return True, n
