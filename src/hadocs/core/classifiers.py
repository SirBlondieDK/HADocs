from src.hadocs.core.rules import RulesEngine
from src.hadocs.core.rulesets.default import load_builtin_rulesets


IGNORED_DOMAINS = {
    "button", "update", "event", "image", "notify", "conversation",
    "stt", "tts", "ai_task", "weather", "zone",
}

PHYSICAL_DOMAINS = {
    "light", "switch", "sensor", "binary_sensor", "camera",
    "media_player", "device_tracker", "lawn_mower", "siren",
}

SYSTEM_DEVICE_WORDS = [
    "home assistant", "integration", "plugin", "hacs", "backup",
    "conversation", "google ai", "openai", "forecast", "cloud", "sun", "met.no",
    "spotify",
]

VIRTUAL_DEVICE_WORDS = ["group", "cast group", "all units", "speaker group"]


RULES = RulesEngine(load_builtin_rulesets())


def is_ignored_entity_id(entity_id: str) -> bool:
    low = entity_id.lower()
    domain = low.split(".")[0]
    if domain in IGNORED_DOMAINS:
        return True

    result = RULES.classify_entity(entity_id, "_unknown")
    return result.importance == "ignored"


def classify_entity(entity_id: str, platform: str | None) -> tuple[bool, bool, str, str]:
    platform = platform or "_unknown"
    domain = entity_id.split(".")[0]

    rule = RULES.classify_entity(entity_id, platform)

    if rule.importance == "ignored":
        return True, False, "ignored", rule.reason

    if rule.importance == "diagnostic":
        return True, False, "diagnostic", rule.reason

    physical = domain in PHYSICAL_DOMAINS and domain not in IGNORED_DOMAINS

    if rule.importance == "important":
        physical = True

    return False, physical, rule.importance, rule.reason


def classify_device(device: dict, entity_domains: set[str], entity_platforms: set[str]) -> str:
    manufacturer = (device.get("manufacturer") or "").lower()
    model = (device.get("model") or "").lower()
    name = (device.get("name_by_user") or device.get("name") or "").lower()
    blob = " ".join([manufacturer, model, name])

    rules_class = RULES.classify_device_by_words(blob)
    if rules_class:
        return rules_class

    if any(word in blob for word in SYSTEM_DEVICE_WORDS):
        return "system"

    if any(word in blob for word in VIRTUAL_DEVICE_WORDS):
        return "virtual"

    if entity_domains and entity_domains.issubset(IGNORED_DOMAINS):
        return "system"

    if entity_platforms and all(platform in {"spotify", "weather", "sun", "hacs"} for platform in entity_platforms):
        return "system"

    if entity_domains.intersection(PHYSICAL_DOMAINS):
        return "physical"

    return "virtual"
