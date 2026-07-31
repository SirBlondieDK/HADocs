from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from .models import DeviceMatch
from .service import HUDDService

_ZIGBEE_MANUFACTURER_PREFIXES = (
    "_TZ",
    "_TZE",
    "_TYZB",
    "_TYST",
)


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _registry_identifiers(entry: dict[str, Any]) -> dict[str, str]:
    """Preserve Home Assistant registry identifiers without guessing semantics."""
    result: dict[str, str] = {}
    raw_identifiers = entry.get("identifiers") or []

    for item in raw_identifiers:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        domain, value = _clean(item[0]), _clean(item[1])
        if not domain or not value:
            continue
        result[f"ha_{domain}"] = value

    return result


def build_device_identity(
    entry: dict[str, Any],
    *,
    platforms: Iterable[str] = (),
) -> dict[str, Any]:
    """Translate a HA device-registry entry into conservative HUDD identity data."""
    manufacturer = _clean(entry.get("manufacturer"))
    model = _clean(entry.get("model"))
    identifiers = _registry_identifiers(entry)
    normalized_platforms = {str(item).strip().casefold() for item in platforms if item}

    looks_like_tuya_zigbee = bool(
        manufacturer
        and manufacturer.upper().startswith(_ZIGBEE_MANUFACTURER_PREFIXES)
    )
    is_zigbee = bool(normalized_platforms & {"zha", "zigbee2mqtt"})

    # HA/ZHA commonly exposes the Zigbee manufacturer code in manufacturer.
    # This is a direct field translation, not an online lookup or inferred OEM claim.
    if manufacturer and (looks_like_tuya_zigbee or is_zigbee):
        identifiers.setdefault("zigbee_manufacturer", manufacturer)
    if model and (looks_like_tuya_zigbee or is_zigbee):
        identifiers.setdefault("zigbee_model", model)

    return {
        "manufacturer": manufacturer,
        "model": model,
        "product_name": _clean(entry.get("name_by_user") or entry.get("name")),
        "hardware_revision": _clean(entry.get("hw_version")),
        "identifiers": identifiers,
    }


def match_device_registry_entry(
    entry: dict[str, Any],
    *,
    platforms: Iterable[str] = (),
    service: HUDDService | None = None,
) -> DeviceMatch:
    """Match one collected HA device entirely against the local HUDD database."""
    try:
        service = service or HUDDService()
        return service.find_device(**build_device_identity(entry, platforms=platforms))
    except Exception as exc:
        # HUDD enrichment must never prevent the main HADocs scan from finishing.
        return DeviceMatch(
            device=None,
            confidence=0.0,
            level="unknown",
            reason="HUDD local lookup was unavailable",
            warnings=[f"HUDD lookup error: {type(exc).__name__}: {exc}"],
        )


def serialize_match(match: DeviceMatch) -> dict[str, Any]:
    """Convert a HUDD result into data safe for reports, JSON and CSV."""
    return {
        "device": asdict(match.device) if match.device is not None else None,
        "confidence": match.confidence,
        "level": match.level,
        "reason": match.reason,
        "matched_fields": list(match.matched_fields),
        "warnings": list(match.warnings),
        "offline": True,
    }
