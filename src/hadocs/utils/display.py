from __future__ import annotations

NO_AREA_ASSIGNED = "No Area Assigned"

_UNASSIGNED_AREA_VALUES = {
    "",
    "_uden_område",
    "_uden_omraade",
    "_uden_omr├ñde",
    "_uden_omr├Ñde",
    "uden område",
    "uden omraade",
    "uden omr├ñde",
    "uden omr├Ñde",
    "unknown",
    "none",
    "null",
}


def is_unassigned_area(value: object) -> bool:
    """Return True when Home Assistant uses an internal unassigned-area value."""
    return str(value or "").strip().lower() in _UNASSIGNED_AREA_VALUES


def display_area(value: object) -> str:
    """Display a user-friendly area name without changing internal IDs or filenames."""
    if is_unassigned_area(value):
        return NO_AREA_ASSIGNED
    return str(value or "").strip()


def display_text(value: object) -> str:
    """Small safe display helper for optional values."""
    return "" if value is None else str(value)
