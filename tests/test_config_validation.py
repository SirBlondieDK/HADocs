from src.hadocs.utils.config import validate_config


def test_validate_config_requires_token():
    cfg = {
        "ha_url": "http://homeassistant.local:8123",
        "token": "",
        "output_dir": "output",
        "cache_dir": "cache",
    }

    problems = validate_config(cfg)

    assert any("Token" in problem for problem in problems)


def test_validate_config_requires_http_url():
    cfg = {
        "ha_url": "homeassistant.local:8123",
        "token": "abc",
        "output_dir": "output",
        "cache_dir": "cache",
    }

    problems = validate_config(cfg)

    assert any("http" in problem for problem in problems)
