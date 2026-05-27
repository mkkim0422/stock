"""router(get_collector) 가 시장에 따라 올바른 collector 반환."""

from src.collectors import MockCollector, get_collector


def test_mock_when_use_mock_env(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "1")
    c = get_collector("005930")
    assert isinstance(c, MockCollector)


def test_kr_routes_to_pykrx_when_real(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "0")
    from src.collectors.kr import PykrxCollector
    c = get_collector("005930")
    assert isinstance(c, PykrxCollector)


def test_us_routes_to_uscollector_when_real(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "0")
    from src.collectors.us import USCollector
    c = get_collector("AAPL")
    assert isinstance(c, USCollector)
