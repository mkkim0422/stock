from datetime import datetime

from src.utils.timezone import KST, NY, now_kst, to_kst, to_ny


def test_now_kst_has_tz():
    assert now_kst().tzinfo is not None


def test_to_kst_naive_treated_as_utc():
    naive = datetime(2026, 1, 1, 0, 0, 0)
    k = to_kst(naive)
    assert k.tzinfo == KST
    assert k.hour == 9


def test_to_ny_converts():
    naive = datetime(2026, 1, 1, 12, 0, 0)
    n = to_ny(naive)
    assert n.tzinfo == NY
