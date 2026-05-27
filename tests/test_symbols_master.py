from src.symbols import list_kr_symbols, list_us_symbols, search_symbols


def test_kr_loaded():
    syms = list_kr_symbols()
    assert any(s.symbol == "005930" for s in syms)


def test_us_loaded():
    syms = list_us_symbols()
    assert any(s.symbol == "AAPL" for s in syms)


def test_search_korean_name():
    hits = search_symbols("삼성")
    assert any(s.symbol == "005930" for s in hits)


def test_search_ticker():
    hits = search_symbols("AAPL")
    assert any(s.name == "Apple" for s in hits)
