"""Turso (libSQL) 원격 DB 어댑터.

배포 환경 (Streamlit Cloud Python 3.11) 에서 TURSO_DATABASE_URL +
TURSO_AUTH_TOKEN 이 설정되어 있을 때 활성화된다. libsql_client 가
import 가능하지 않은 환경(로컬 Python 3.14 wheel 미배포)에서는
ImportError 를 잡아 자동으로 로컬 SQLite 로 폴백.

사용 패턴:
    if is_turso_configured() and has_libsql():
        use_cloud(...)
    else:
        use_local_sqlite(...)
"""
from __future__ import annotations

import os


def is_turso_configured() -> bool:
    return bool(os.environ.get("TURSO_DATABASE_URL")) and bool(
        os.environ.get("TURSO_AUTH_TOKEN")
    )


def has_libsql() -> bool:
    try:
        import libsql_client  # noqa: F401
        return True
    except ImportError:
        return False


def get_status() -> dict:
    """현재 클라우드 DB 사용 가능 여부와 상태."""
    configured = is_turso_configured()
    has = has_libsql()
    return {
        "configured": configured,
        "library_available": has,
        "active": configured and has,
        "url_host": _extract_host(os.environ.get("TURSO_DATABASE_URL", "")),
    }


def _extract_host(url: str) -> str:
    if not url:
        return ""
    if "://" in url:
        url = url.split("://", 1)[1]
    return url.split("/", 1)[0]
