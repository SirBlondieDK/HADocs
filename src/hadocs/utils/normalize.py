from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def normalize_text(value: Any) -> str:
    """Convert an external value safely to stripped lowercase text."""
    if value is None:
        return ""

    return str(value).strip().lower()


def normalize_bool(value: Any, default: bool = False) -> bool:
    """Convert common external boolean representations safely."""
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value != 0

    normalized = normalize_text(value)

    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True

    if normalized in {"0", "false", "no", "off", "disabled", ""}:
        return False

    return default


def normalize_list(value: Any) -> list[Any]:
    """Convert an external value safely to a list."""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, (tuple, set)):
        return list(value)

    return [value]


def normalize_dict(value: Any) -> dict[str, Any]:
    """Convert a mapping safely to a plain dictionary."""
    if isinstance(value, Mapping):
        return dict(value)

    return {}


def text_contains_any(
    value: Any,
    patterns: list[Any] | tuple[Any, ...] | set[Any],
) -> bool:
    """Return True when normalized text contains a non-empty pattern."""
    normalized_value = normalize_text(value)

    for pattern in patterns:
        normalized_pattern = normalize_text(pattern)

        if normalized_pattern and normalized_pattern in normalized_value:
            return True

    return False
