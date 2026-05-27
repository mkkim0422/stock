"""pytest 공통 fixture.

테스트 환경에서는 외부 API 호출을 차단하기 위해 USE_MOCK=1 강제.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("USE_MOCK", "1")
