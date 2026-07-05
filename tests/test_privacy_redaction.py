from src.hadocs.privacy.redaction import redact_dict, redact_text


def test_redact_ip():
    assert "<redacted-ip>" in redact_text("Home Assistant is at 192.168.1.10")


def test_redact_mac():
    assert "<redacted-mac>" in redact_text("AA:BB:CC:DD:EE:FF")


def test_redact_token_key():
    data = {"token": "secret", "name": "Kitchen"}
    result = redact_dict(data)
    assert result["token"] == "<redacted>"
    assert result["name"] == "Kitchen"
