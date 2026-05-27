"""_market_of 가 symbol master 조회를 우선하는지."""
from src.paper.trader import _market_of


def test_kr_six_digit():
    assert _market_of("005930") == "KR"


def test_us_alpha():
    assert _market_of("AAPL") == "US"


def test_us_dotted():
    assert _market_of("BRK.B") == "US"


def test_unknown_falls_back_us():
    # 마스터에 없고 6자리 숫자도 아니면 US 폴백
    assert _market_of("UNKNOWN_XYZ") == "US"
