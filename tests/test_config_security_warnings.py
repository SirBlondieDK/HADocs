from src.hadocs.utils.config import (
    INSECURE_HTTP_WARNING,
    validate_config_warnings,
)


def make_config(url):
    return {
        "ha_url": url,
        "token": "test-token",
    }


def test_https_does_not_warn():
    assert validate_config_warnings(
        make_config("https://home.example.com")
    ) == []


def test_http_localhost_does_not_warn():
    assert validate_config_warnings(
        make_config("http://localhost:8123")
    ) == []


def test_http_ipv4_loopback_does_not_warn():
    assert validate_config_warnings(
        make_config("http://127.0.0.1:8123")
    ) == []


def test_http_ipv6_loopback_does_not_warn():
    assert validate_config_warnings(
        make_config("http://[::1]:8123")
    ) == []


def test_http_local_network_warns():
    assert validate_config_warnings(
        make_config("http://192.168.1.10:8123")
    ) == [INSECURE_HTTP_WARNING]


def test_http_hostname_warns():
    assert validate_config_warnings(
        make_config("http://homeassistant.local:8123")
    ) == [INSECURE_HTTP_WARNING]


def test_missing_token_does_not_create_security_warning():
    assert validate_config_warnings(
        {
            "ha_url": "http://192.168.1.10:8123",
            "token": "",
        }
    ) == []
