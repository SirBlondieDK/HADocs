from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


_FRIENDLY_INTEGRATIONS = {
    "zha": "ZHA",
    "mqtt": "MQTT",
    "wled": "WLED",
    "esphome": "ESPHome",
    "hue": "Philips Hue",
    "mobile_app": "Mobile App",
    "google_cast": "Google Cast",
    "homekit_controller": "HomeKit Device",
    "matter": "Matter",
    "zwave_js": "Z-Wave JS",
    "ibeacon": "iBeacon",
    "tplink_deco": "TP-Link Deco",
}

# Network/device-tracker integrations often merge into a physical device. They
# are useful secondary integrations, but should not normally become the badge
# shown as the device's primary integration.
_SECONDARY_PLATFORMS = {
    "tplink_deco",
    "unifi",
    "device_tracker",
    "ping",
    "nmap_tracker",
    "bluetooth",
}


@dataclass(slots=True)
class DeviceSummary:
    """The stable device contract returned by ``GET /api/devices``."""

    device_id: str
    name: str
    area: str = ""
    area_id: str = ""
    platform: str = ""
    integration: str = "Unknown integration"
    platforms: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    manufacturer: str = ""
    model: str = ""
    classification: str = ""
    entity_count: int = 0
    entity_ids: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    primary_domain: str = ""
    online: bool | None = None
    unavailable_count: int = 0
    unknown_count: int = 0
    subtitle: str = ""

    def to_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        # Temporary backwards compatibility for the existing Device Override UI.
        payload["device_name"] = self.name
        payload["integration_count"] = len(self.platforms)
        return payload


def friendly_integration(platform: str) -> str:
    value = str(platform or "").strip()
    if not value:
        return "Unknown integration"
    return _FRIENDLY_INTEGRATIONS.get(
        value.casefold(), value.replace("_", " ").title()
    )


def _text(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _primary_platform(item: dict[str, Any], platforms: list[str]) -> str:
    explicit = _text(item, "primary_platform", "platform")
    if explicit and explicit.casefold() not in _SECONDARY_PLATFORMS:
        return explicit

    identity = " ".join(
        _text(item, key)
        for key in ("title", "name", "manufacturer", "model")
    ).casefold()
    identity_hints = {
        "wled": "wled",
        "esphome": "esphome",
        "philips hue": "hue",
        "homekit": "homekit_controller",
        "matter": "matter",
        "zigbee": "zha",
    }
    for hint, platform in identity_hints.items():
        if hint in identity and platform in {p.casefold() for p in platforms}:
            return next(p for p in platforms if p.casefold() == platform)

    preferred = [
        platform for platform in platforms
        if platform.casefold() not in _SECONDARY_PLATFORMS
    ]
    return (preferred or platforms or [explicit])[0] if (preferred or platforms or explicit) else ""


def _summary_from_index(item: dict[str, Any]) -> DeviceSummary | None:
    device_id = _text(item, "id", "device_id")
    if not device_id:
        return None

    subtitle = _text(item, "subtitle")
    platforms = _string_list(item.get("platforms"))
    platform = _primary_platform(item, platforms)

    # Compatibility with pre-v0.2.8 indexes.
    area = _text(item, "area", "area_name")
    if subtitle and not platform:
        parts = [part.strip() for part in subtitle.replace("·", "•").split("•")]
        parts = [part for part in parts if part]
        if parts:
            platform = parts[0]
        if len(parts) > 1 and not area:
            area = parts[1]

    if platform and platform not in platforms:
        platforms.insert(0, platform)

    entity_ids = _string_list(item.get("entity_ids"))
    entities = item.get("entities")
    raw_count = item.get("entity_count")
    if isinstance(raw_count, int):
        entity_count = raw_count
    elif isinstance(entity_ids, list):
        entity_count = len(entity_ids)
    elif isinstance(entities, list):
        entity_count = len(entities)
    else:
        entity_count = 0

    return DeviceSummary(
        device_id=device_id,
        name=_text(item, "title", "name") or device_id,
        subtitle=subtitle,
        platform=platform,
        integration=friendly_integration(platform),
        platforms=platforms,
        integrations=[friendly_integration(value) for value in platforms],
        area=area,
        area_id=_text(item, "area_id"),
        manufacturer=_text(item, "manufacturer"),
        model=_text(item, "model"),
        classification=_text(item, "classification"),
        entity_count=entity_count,
        entity_ids=entity_ids,
        domains=_string_list(item.get("domains")),
        primary_domain=_text(item, "primary_domain"),
        online=item.get("online") if isinstance(item.get("online"), bool) else None,
        unavailable_count=int(item.get("unavailable_count") or 0),
        unknown_count=int(item.get("unknown_count") or 0),
    )


def load_device_summaries(index_path: Path) -> list[dict[str, Any]]:
    """Read Explorer data and return the stable ``DeviceSummary`` contract."""
    if not index_path.is_file():
        return []

    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(payload, list):
        return []

    summaries = []
    for item in payload:
        if not isinstance(item, dict) or item.get("type") != "device":
            continue
        summary = _summary_from_index(item)
        if summary is not None:
            summaries.append(summary)

    summaries.sort(
        key=lambda item: (
            item.name.casefold(),
            item.integration.casefold(),
            item.area.casefold(),
        )
    )
    return [summary.to_mapping() for summary in summaries]
