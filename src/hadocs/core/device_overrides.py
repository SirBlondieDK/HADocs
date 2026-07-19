from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatch
import json
from pathlib import Path
import os
import shutil
from typing import Iterable, Mapping, Sequence

from src.hadocs.platform import AppPaths


OWNERSHIP_VALUES = {"unspecified", "owned", "shared", "external", "unknown"}
POLICY_TYPES = {"normal", "power_controlled", "seasonal", "temporary", "external"}
PURPOSE_VALUES = {
    "unspecified", "infrastructure", "automation", "presence", "media",
    "testing", "temporary", "seasonal",
}


@dataclass(frozen=True, slots=True)
class DeviceOverride:
    ownership: str = "unspecified"
    purpose: str = "unspecified"
    policy_type: str = "normal"
    expected_offline: bool = False
    ignore_battery: bool = False
    ignore_stale: bool = False
    active_months: tuple[int, ...] = ()
    reason: str = ""
    expires_at: datetime | None = None
    device_id: str | None = None
    device_name: str | None = None
    entity_globs: tuple[str, ...] = ()

    def expired(self, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        current = now or datetime.now(UTC)
        expiry = self.expires_at
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        return current >= expiry


@dataclass(frozen=True, slots=True)
class DevicePolicy:
    ownership: str = "unspecified"
    purpose: str = "unspecified"
    policy_type: str = "normal"
    expected_offline: bool = False
    ignore_battery: bool = False
    ignore_stale: bool = False
    active_months: tuple[int, ...] = ()
    in_active_season: bool | None = None
    reason: str = ""
    matched: bool = False
    match_source: str | None = None


EMPTY_DEVICE_POLICY = DevicePolicy()


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _normalise_choice(value: object, allowed: set[str], fallback: str) -> str:
    result = str(value or fallback).strip().lower()
    return result if result in allowed else fallback


def _parse_months(value: object) -> tuple[int, ...]:
    if isinstance(value, int):
        value = (value,)
    if not isinstance(value, Sequence) or isinstance(value, str):
        return ()
    months: list[int] = []
    for item in value:
        try:
            month = int(item)
        except (TypeError, ValueError):
            continue
        if 1 <= month <= 12 and month not in months:
            months.append(month)
    return tuple(sorted(months))


def override_from_mapping(data: Mapping[str, object]) -> DeviceOverride:
    """Parse both legacy flat overrides and the new nested policy format."""
    nested = data.get("policy", {})
    policy = nested if isinstance(nested, Mapping) else {}

    globs = data.get("entity_globs", ())
    if isinstance(globs, str):
        globs = (globs,)
    elif not isinstance(globs, Sequence):
        globs = ()

    ownership = _normalise_choice(
        policy.get("ownership", data.get("ownership", "unspecified")),
        OWNERSHIP_VALUES,
        "unknown",
    )
    purpose = _normalise_choice(
        policy.get("purpose", data.get("purpose", "unspecified")),
        PURPOSE_VALUES,
        "unspecified",
    )

    # `profile` was used by an early draft. Keep accepting it as an alias.
    policy_type = _normalise_choice(
        policy.get(
            "type",
            policy.get(
                "availability",
                data.get("policy_type", data.get("profile", "normal")),
            ),
        ),
        POLICY_TYPES,
        "normal",
    )
    if ownership == "external":
        policy_type = "external"

    return DeviceOverride(
        ownership=ownership,
        purpose=purpose,
        policy_type=policy_type,
        expected_offline=bool(
            policy.get("expected_offline", data.get("expected_offline", False))
        ),
        ignore_battery=bool(
            policy.get("ignore_battery", data.get("ignore_battery", False))
        ),
        ignore_stale=bool(
            policy.get("ignore_stale", data.get("ignore_stale", False))
        ),
        active_months=_parse_months(
            policy.get("active_months", data.get("active_months", ()))
        ),
        reason=str(data.get("reason", policy.get("reason", "")) or ""),
        expires_at=_parse_datetime(data.get("expires_at", policy.get("expires_at"))),
        device_id=str(data["device_id"]) if data.get("device_id") else None,
        device_name=str(data["device_name"]) if data.get("device_name") else None,
        entity_globs=tuple(str(x) for x in globs if str(x).strip()),
    )


def _overrides_from_sequence(raw: object) -> tuple[DeviceOverride, ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, str):
        return ()
    return tuple(
        item if isinstance(item, DeviceOverride) else override_from_mapping(item)
        for item in raw
        if isinstance(item, (DeviceOverride, Mapping))
    )


def load_device_overrides_file(path: str | Path) -> tuple[DeviceOverride, ...]:
    """Load overrides from a dedicated JSON file."""
    override_path = Path(path)
    if not override_path.exists():
        return ()
    try:
        payload = json.loads(override_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Could not load device overrides from {override_path}: {exc}"
        ) from exc
    if isinstance(payload, list):
        raw = payload
    elif isinstance(payload, Mapping):
        raw = payload.get("devices", payload.get("device_overrides", ()))
    else:
        raw = ()
    return _overrides_from_sequence(raw)


APP_PATHS = AppPaths.discover()


def _resolve_device_overrides_file(
    config: Mapping[str, object],
    *,
    base_dir: str | Path | None = None,
) -> Path:
    """Resolve the dedicated overrides file without breaking legacy installs."""
    configured_path = config.get("device_overrides_file")

    if configured_path:
        file_path = Path(str(configured_path)).expanduser()
        if file_path.is_absolute():
            return file_path

        root = Path(base_dir) if base_dir is not None else APP_PATHS.root_dir
        return root / file_path

    # Explicit base directories are primarily used by callers and tests that
    # manage their own runtime folder. Preserve the historical filename there.
    if base_dir is not None:
        return Path(base_dir) / "device_overrides.json"

    # Keep existing installations on the old root-level file until the
    # migration component moves it into config/.
    if (
        APP_PATHS.legacy_overrides_file.exists()
        and not APP_PATHS.overrides_file.exists()
    ):
        return APP_PATHS.legacy_overrides_file

    return APP_PATHS.overrides_file


def load_device_overrides(
    config: Mapping[str, object] | None,
    *,
    base_dir: str | Path | None = None,
) -> tuple[DeviceOverride, ...]:
    """Merge dedicated-file overrides with legacy inline overrides."""
    cfg = config if isinstance(config, Mapping) else {}
    file_path = _resolve_device_overrides_file(cfg, base_dir=base_dir)
    file_overrides = load_device_overrides_file(file_path)
    inline_overrides = _overrides_from_sequence(cfg.get("device_overrides", ()))
    return (*inline_overrides, *file_overrides)


def match_override(device, overrides: Iterable[DeviceOverride], now: datetime | None = None):
    active = [o for o in overrides if not o.expired(now)]
    did, name = getattr(device, "device_id", None), getattr(device, "name", None)
    for o in active:
        if o.device_id and o.device_id == did:
            return o, "device_id"
    for o in active:
        if o.device_name and o.device_name == name:
            return o, "device_name"
    ids = [getattr(e, "entity_id", "") for e in getattr(device, "entities", [])]
    for o in active:
        if any(fnmatch(eid, pat) for eid in ids for pat in o.entity_globs):
            return o, "entity_glob"
    return None


def get_device_policy(
    device,
    overrides: Iterable[DeviceOverride] = (),
    now: datetime | None = None,
) -> DevicePolicy:
    match = match_override(device, overrides, now)
    if match is None:
        return EMPTY_DEVICE_POLICY

    override, source = match
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)

    in_active_season: bool | None = None
    expected_offline = override.expected_offline

    if override.policy_type == "power_controlled":
        # Physical power control means offline is a normal operating state.
        expected_offline = True
    elif override.policy_type == "seasonal":
        if override.active_months:
            in_active_season = current.month in override.active_months
            expected_offline = expected_offline or not in_active_season
        else:
            # Without a season definition, retain the explicit legacy flag.
            in_active_season = None
    elif override.policy_type == "external":
        expected_offline = False

    return DevicePolicy(
        ownership=override.ownership,
        purpose=override.purpose,
        policy_type=override.policy_type,
        expected_offline=expected_offline,
        ignore_battery=override.ignore_battery,
        ignore_stale=override.ignore_stale,
        active_months=override.active_months,
        in_active_season=in_active_season,
        reason=override.reason,
        matched=True,
        match_source=source,
    )


def resolve_device_overrides_file(
    config: Mapping[str, object] | None = None,
    *,
    base_dir: str | Path | None = None,
) -> Path:
    """Return the active device-overrides file used by HADocs."""
    cfg = config if isinstance(config, Mapping) else {}
    return _resolve_device_overrides_file(cfg, base_dir=base_dir)


def device_override_to_mapping(override: DeviceOverride) -> dict[str, object]:
    """Serialize an override using the canonical nested policy format."""
    policy: dict[str, object] = {
        "ownership": override.ownership,
        "purpose": override.purpose,
        "type": override.policy_type,
        "expected_offline": override.expected_offline,
        "ignore_battery": override.ignore_battery,
        "ignore_stale": override.ignore_stale,
    }
    if override.active_months:
        policy["active_months"] = list(override.active_months)

    result: dict[str, object] = {"policy": policy}
    if override.device_id:
        result["device_id"] = override.device_id
    if override.device_name:
        result["device_name"] = override.device_name
    if override.entity_globs:
        result["entity_globs"] = list(override.entity_globs)
    if override.reason:
        result["reason"] = override.reason
    if override.expires_at is not None:
        result["expires_at"] = override.expires_at.isoformat()
    return result


def save_device_overrides_file(
    path: str | Path, overrides: Iterable[DeviceOverride]
) -> Path:
    """Validate and atomically save overrides, keeping a one-file backup."""
    override_path = Path(path)
    override_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = tuple(overrides)

    seen_ids: set[str] = set()
    for item in normalized:
        if not isinstance(item, DeviceOverride):
            raise TypeError("All overrides must be DeviceOverride instances")
        if not (item.device_id or item.device_name or item.entity_globs):
            raise ValueError(
                "An override must target a device ID, device name, or entity glob"
            )
        if item.device_id:
            if item.device_id in seen_ids:
                raise ValueError(f"Duplicate override for device ID: {item.device_id}")
            seen_ids.add(item.device_id)

    payload = {
        "devices": [device_override_to_mapping(item) for item in normalized]
    }
    temp_path = override_path.with_name(override_path.name + ".tmp")
    backup_path = override_path.with_name(override_path.name + ".bak")
    temp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    try:
        if override_path.exists():
            shutil.copy2(override_path, backup_path)
        os.replace(temp_path, override_path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
    return override_path


def upsert_device_override(
    path: str | Path, override: DeviceOverride
) -> tuple[DeviceOverride, ...]:
    """Add or replace an override by device ID, then save it safely."""
    current = list(load_device_overrides_file(path))
    replaced = False
    if override.device_id:
        for index, existing in enumerate(current):
            if existing.device_id == override.device_id:
                current[index] = override
                replaced = True
                break
    if not replaced:
        current.append(override)
    save_device_overrides_file(path, current)
    return tuple(current)


def remove_device_override(
    path: str | Path, device_id: str
) -> tuple[DeviceOverride, ...]:
    """Remove a device-ID override and save the remaining entries safely."""
    target = str(device_id or "").strip()
    current = [
        item for item in load_device_overrides_file(path)
        if item.device_id != target
    ]
    save_device_overrides_file(path, current)
    return tuple(current)
