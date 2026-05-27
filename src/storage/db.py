"""SQLite 접속 + 마이그레이션 (WAL 모드).

사용 예:
    with connect() as conn:
        cur = conn.execute("SELECT * FROM trades")
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from src.config import get_settings

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_db_path() -> Path:
    p = Path(get_settings().db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = get_db_path()
    conn = sqlite3.connect(path, isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


def apply_migrations() -> list[str]:
    """모든 0001_*.sql 마이그레이션 적용 (멱등).

    반환: 실행된 파일명 리스트.
    """
    applied: list[str] = []
    files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    with connect() as conn:
        for f in files:
            sql = f.read_text(encoding="utf-8")
            conn.executescript(sql)
            applied.append(f.name)
    return applied


def reset_db() -> None:
    """테스트용: DB 파일 삭제 후 다시 마이그레이션."""
    path = get_db_path()
    for ext in ("", "-wal", "-shm", "-journal"):
        target = Path(str(path) + ext)
        if target.exists():
            target.unlink()
    apply_migrations()
