import re
from typing import Any

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MAC_RE = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
TOKEN_RE = re.compile(r"(?i)(token|access_token|authorization|bearer)\s*[:=]\s*['\"]?[^'\"\s,]+")

SENSITIVE_KEYS = {
    "token", "access_token", "authorization", "refresh_token",
    "password", "secret", "latitude", "longitude", "gps", "location",
}


def redact_text(value: str) -> str:
    value = IP_RE.sub("<redacted-ip>", value)
    value = MAC_RE.sub("<redacted-mac>", value)
    value = TOKEN_RE.sub(r"\1=<redacted-token>", value)
    return value


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return redact_dict(value)
    return value


def redact_dict(data: dict) -> dict:
    redacted = {}
    for key, value in data.items():
        if str(key).lower() in SENSITIVE_KEYS:
            redacted[key] = "<redacted>"
        else:
            redacted[key] = redact_value(value)
    return redacted
