from src.hadocs.utils.config import DEFAULT_CONFIG


def test_raw_cache_is_disabled_by_default():
    assert DEFAULT_CONFIG["save_raw_cache"] is False