"""뉴스 헤드라인 수집 — Google News RSS (무료, 가입X).

종목 이름으로 한국어 RSS 검색. 호출 간격을 두어 차단 회피.
"""
from __future__ import annotations

import time
import urllib.parse
from xml.etree import ElementTree as ET

import httpx

from src.utils.logger import get_logger

_log = get_logger("collectors.news")
_LAST_CALL_TS = 0.0
_MIN_INTERVAL_SEC = 0.5
_RSS_URL = "https://news.google.com/rss/search?q={q}&hl=ko-KR&gl=KR&ceid=KR:ko"


def _throttle() -> None:
    global _LAST_CALL_TS
    now = time.monotonic()
    diff = now - _LAST_CALL_TS
    if diff < _MIN_INTERVAL_SEC:
        time.sleep(_MIN_INTERVAL_SEC - diff)
    _LAST_CALL_TS = time.monotonic()


def fetch_headlines(query: str, limit: int = 5) -> list[dict]:
    """질의어로 Google News 한국어 RSS 를 받아 헤드라인 반환.

    반환: [{"title", "link", "published", "source"}].
    실패해도 예외 없이 빈 리스트.
    """
    if not query.strip():
        return []
    _throttle()
    url = _RSS_URL.format(q=urllib.parse.quote_plus(query))
    try:
        r = httpx.get(url, timeout=8.0, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except Exception as e:
        _log.warning("Google News RSS 실패 (%s): %s", query, e)
        return []

    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        _log.warning("RSS 파싱 실패 (%s): %s", query, e)
        return []

    items: list[dict] = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else ""
        # 구글 뉴스 제목은 "제목 - 출처" 형태. 출처 분리.
        if " - " in title and not source:
            t, s = title.rsplit(" - ", 1)
            title, source = t.strip(), s.strip()
        items.append({
            "title": title,
            "link": link,
            "published": pub,
            "source": source,
        })
    return items
