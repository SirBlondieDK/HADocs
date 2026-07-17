from __future__ import annotations

from typing import Any

from src.hadocs.core.rules import RulesEngine
from src.hadocs.core.rulesets.default import load_builtin_rulesets
from src.hadocs.utils.normalize import normalize_text


IGNORED_DOMAINS = {
    "button",
    "update",
    "event",
    "image",
    "notify",
    "conversation",
    "stt",
    "tts",
    "ai_task",
    "weather",
    "zone",
}

PHYSICAL_DOMAINS = {
    "light",
    "switch",
    "sensor",
    "binary_sensor",
    "camera",
    "media_player",
    "device_tracker",
    "lawn_mower",
    "siren",
}

SYSTEM_PLATFORMS = {
    "hacs",
    "cloud",
    "spotify",
    "sun",
    "weather",
    "backup",
    "conversation",
    "openai_conversation",
    "google_generative_ai_conversation",
}

RULES = RulesEngine(load_builtin_rulesets())


def is_ignored_entity_id(entity_id: Any) -> bool:
    normalized_entity_id = normalize_text(entity_id)
    domain = normalized_entity_id.split(".", maxsplit=1)[0]

    if domain in IGNORED_DOMAINS:
        return True

    result = RULES.classify_entity(
        normalized_entity_id,
        "_global",
    )

    return result.importance == "ignored"


def classify_entity(
    entity_id: Any,
    platform: Any,
) -> tuple[bool, bool, str, str]:
    normalized_entity_id = normalize_text(entity_id)
    normalized_platform = normalize_text(platform) or "_unknown"
    domain = normalized_entity_id.split(".", maxsplit=1)[0]

    if normalized_platform in SYSTEM_PLATFORMS:
        return (
            True,
            False,
            "ignored",
            f"{normalized_platform}: system platform",
        )

    rule = RULES.classify_entity(
        normalized_entity_id,
        normalized_platform,
    )

    if rule.importance == "ignored":
        return True, False, "ignored", rule.reason

    if rule.importance == "diagnostic":
        return True, False, "diagnostic", rule.reason

    physical = (
        domain in PHYSICAL_DOMAINS
        and domain not in IGNORED_DOMAINS
    )

    if rule.importance == "important":
        physical = True

    return False, physical, rule.importance, rule.reason


def classify_device(
    device: dict,
    entity_domains: set[Any],
    entity_platforms: set[Any],
) -> str:
    manufacturer = normalize_text(device.get("manufacturer"))
    model = normalize_text(device.get("model"))
    name = normalize_text(
        device.get("name_by_user")
        or device.get("name")
    )

    blob = " ".join(
        value
        for value in (manufacturer, model, name)
        if value
    )

    rules_class = RULES.classify_device_by_words(blob)
    if rules_class:
        return rules_class

    normalized_platforms = {
        normalize_text(platform)
        for platform in entity_platforms
        if normalize_text(platform)
    }

    normalized_domains = {
        normalize_text(domain)
        for domain in entity_domains
        if normalize_text(domain)
    }

    if (
        normalized_platforms
        and normalized_platforms.issubset(SYSTEM_PLATFORMS)
    ):
        return "system"

    if (
        normalized_domains
        and normalized_domains.issubset(IGNORED_DOMAINS)
    ):
        return "system"

    if normalized_domains.intersection(PHYSICAL_DOMAINS):
        return "physical"

    return "virtual"
