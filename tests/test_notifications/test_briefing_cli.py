"""briefing_cli 진입점 E2E (network mock 환경)."""
import os
import subprocess
import sys
from pathlib import Path


def test_briefing_cli_runs_clean(tmp_path):
    db = tmp_path / "cli.db"
    env = os.environ.copy()
    env["DB_PATH"] = str(db)
    env["USE_MOCK"] = "1"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent.parent)
    # 텔레그램 미설정 → skipped
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_CHAT_ID", None)

    r = subprocess.run(
        [sys.executable, "-m", "scripts.briefing_cli", "--slot", "test"],
        env=env, capture_output=True, text=True, timeout=60,
    )
    # skipped 도 성공 처리
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    assert "test" in r.stdout.lower() or "skipped" in r.stdout.lower()
