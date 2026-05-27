"""GitHub Actions cron 진입점.

사용:
    python -m scripts.briefing_cli --slot 09:30
"""
from __future__ import annotations

import argparse
import sys

from src.notifications.briefing import send_briefing
from src.storage import apply_migrations


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--slot", required=True, help="브리핑 슬롯 (예: 09:30)")
    args = p.parse_args()
    apply_migrations()
    r = send_briefing(args.slot)
    print(f"[{r['slot']}] {r['status']}")
    return 0 if r.get("ok") or "skipped" in r.get("status", "") else 1


if __name__ == "__main__":
    sys.exit(main())
