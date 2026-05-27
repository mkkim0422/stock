"""SQLite 접속 + 마이그레이션 (WAL 모드, Decimal 컬럼 매핑).

DECIMAL 컬럼은 PARSE_DECLTYPES + register_converter 로 Python Decimal 로 변환.
INSERT 시 Decimal → 'f' 포맷 문자열로 저장.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

from src.config import get_settings

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


sqlite3.register_adapter(Decimal, lambda d: format(d, "f"))


def _decimal_converter(value: bytes) -> Decimal:
    return Decimal(value.decode("ascii"))


sqlite3.register_converter("DECIMAL_TEXT", _decimal_converter)


def get_db_path() -> Path:
    p = Path(get_settings().db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = get_db_path()
    conn = sqlite3.connect(
        path,
        isolation_level=None,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA synchronous = NORMAL")
        yield conn
    finally:
        conn.close()


_applied_for_path: dict[str, list[str]] = {}


def apply_migrations() -> list[str]:
    """마이그레이션 적용 (멱등 + 프로세스 내 1회 캐시).

    같은 DB 경로에 대해 같은 프로세스에서 한 번만 실제 SQL 실행.
    파일 자체는 IF NOT EXISTS 라 재실행해도 안전하나 매 요청마다의
    비용을 피하기 위함이다.
    """
    key = str(get_db_path())
    cached = _applied_for_path.get(key)
    if cached is not None:
        return cached

    applied: list[str] = []
    files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    with connect() as conn:
        for f in files:
            sql = f.read_text(encoding="utf-8")
            conn.executescript(sql)
            applied.append(f.name)
    _applied_for_path[key] = applied
    return applied


def reset_db() -> None:
    """테스트용: DB 파일 삭제 후 다시 마이그레이션."""
    path = get_db_path()
    for ext in ("", "-wal", "-shm", "-journal"):
        target = Path(str(path) + ext)
        if target.exists():
            target.unlink()
    _applied_for_path.pop(str(path), None)
    apply_migrations()
