from src.utils.logger import get_logger


def test_logger_returns_same_instance():
    a = get_logger("test_a")
    b = get_logger("test_a")
    assert a is b


def test_logger_has_handlers():
    log = get_logger("test_handlers")
    assert len(log.handlers) >= 1
