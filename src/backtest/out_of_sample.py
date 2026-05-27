"""OOS 검증 (Phase 4 활성)."""
from __future__ import annotations

from datetime import date


def split_in_out_of_sample(start: date, end: date, in_sample_ratio: float = 0.7) -> tuple[date, date, date, date]:
    """기간을 in-sample / OOS 로 분리.

    반환: (is_start, is_end, oos_start, oos_end)
    """
    if not 0 < in_sample_ratio < 1:
        raise ValueError("in_sample_ratio must be in (0, 1)")
    total = (end - start).days
    split_days = int(total * in_sample_ratio)
    from datetime import timedelta
    is_end = start + timedelta(days=split_days)
    oos_start = is_end + timedelta(days=1)
    return start, is_end, oos_start, end


def evaluate_oos(*args, **kwargs):
    """Phase 4 활성."""
    raise NotImplementedError("Phase 4 에서 구현됩니다.")
