from src.hadocs.core.models import DeviceHealth, HADocsModel


CRITICAL_PATTERNS = [
    "homeassistant_status", "hp_mini_status", "adguard_status",
    "zigbee2mqtt_status", "zigbee2mqtt_bridge_connection_state",
    "frigate_status", "remote_ui", "internet_online", "deco_online",
]


def calculate_device_health(model: HADocsModel) -> list[DeviceHealth]:
    results: list[DeviceHealth] = []

    for device in model.devices.values():
        if not device.is_physical:
            continue

        relevant_entities = [
            entity for entity in device.entities
            if not entity.is_ignored and entity.is_physical and entity.importance != "diagnostic"
        ]

        if not relevant_entities:
            continue

        unavailable = [e for e in relevant_entities if e.state == "unavailable"]
        unknown = [e for e in relevant_entities if e.state == "unknown"]

        score = 100
        reasons = []

        if unavailable:
            important_count = sum(1 for e in unavailable if e.importance == "important")
            normal_count = len(unavailable) - important_count
            penalty = min(55, important_count * 10 + normal_count * 3)
            score -= penalty
            reasons.append(f"{len(unavailable)} relevant entities unavailable")

        if unknown:
            important_count = sum(1 for e in unknown if e.importance == "important")
            normal_count = len(unknown) - important_count
            penalty = min(25, important_count * 5 + normal_count)
            score -= penalty
            reasons.append(f"{len(unknown)} relevant entities unknown")

        battery_entities = [e for e in relevant_entities if "battery" in e.entity_id.lower()]
        for entity in battery_entities:
            try:
                value = float(entity.state)
                if value <= 10:
                    score -= 12
                    reasons.append(f"{entity.entity_id} battery critical ({value}%)")
                elif value <= 25:
                    score -= 4
                    reasons.append(f"{entity.entity_id} battery low ({value}%)")
            except Exception:
                pass

        score = max(0, min(100, score))

        if score >= 85:
            status = "healthy"
        elif score >= 55:
            status = "warning"
        else:
            status = "problem"

        results.append(DeviceHealth(device=device, status=status, score=score, reasons=reasons))

    return results


def calculate_health_score(model: HADocsModel, device_health: list[DeviceHealth]) -> tuple[int, list[str]]:
    score = 100
    notes = []

    problem_devices = [d for d in device_health if d.status == "problem"]
    warning_devices = [d for d in device_health if d.status == "warning"]

    if problem_devices:
        penalty = min(30, len(problem_devices) * 5)
        score -= penalty
        notes.append(f"{len(problem_devices)} physical devices have serious problems (-{penalty})")

    if warning_devices:
        penalty = min(15, len(warning_devices) * 2)
        score -= penalty
        notes.append(f"{len(warning_devices)} physical devices have warnings (-{penalty})")

    physical_without_area = [
        d for d in model.devices.values()
        if d.is_physical and (not d.area_id or d.area_id == "_uden_område")
    ]
    if physical_without_area:
        penalty = min(6, max(1, len(physical_without_area) // 10))
        score -= penalty
        notes.append(f"{len(physical_without_area)} physical devices have no area (-{penalty})")

    duplicate_domain_names = find_duplicate_names_by_domain(model)
    if duplicate_domain_names:
        penalty = min(2, max(1, len(duplicate_domain_names) // 15))
        score -= penalty
        notes.append(f"{len(duplicate_domain_names)} duplicate names within same domain (-{penalty})")

    ignored_bad = [
        e for e in model.entities.values()
        if e.is_ignored and e.state in ("unknown", "unavailable")
    ]
    if ignored_bad:
        notes.append(f"{len(ignored_bad)} ignored diagnostic/system entities are unknown/unavailable")

    return max(0, min(100, score)), notes


def find_duplicate_names_by_domain(model: HADocsModel) -> dict[tuple[str, str], list[str]]:
    grouped: dict[tuple[str, str], list[str]] = {}

    for entity in model.entities.values():
        if entity.is_ignored or entity.importance == "diagnostic":
            continue
        if entity.domain in {"device_tracker", "sensor"}:
            continue
        key = (entity.domain, entity.name)
        grouped.setdefault(key, []).append(entity.entity_id)

    return {key: value for key, value in grouped.items() if len(value) > 1}


def get_critical_entities(model: HADocsModel):
    critical = []
    for entity in model.entities.values():
        if entity.state not in ("unknown", "unavailable"):
            continue
        if entity.is_ignored or entity.importance == "diagnostic":
            continue
        eid = entity.entity_id.lower()
        if any(pattern in eid for pattern in CRITICAL_PATTERNS):
            critical.append(entity)
    return critical
