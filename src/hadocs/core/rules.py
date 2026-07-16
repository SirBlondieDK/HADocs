from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Any

from src.hadocs.utils.normalize import normalize_text


@dataclass
class RuleSet:
    name: str
    platforms: set[str] = field(default_factory=set)
    important: list[str] = field(default_factory=list)
    ignore: list[str] = field(default_factory=list)
    diagnostic: list[str] = field(default_factory=list)
    device_system_words: list[str] = field(default_factory=list)
    device_virtual_words: list[str] = field(default_factory=list)


@dataclass
class RuleResult:
    importance: str
    reason: str


def _matches_any(value: Any, patterns: list[Any]) -> bool:
    normalized_value = normalize_text(value)

    for pattern in patterns:
        normalized_pattern = normalize_text(pattern)

        if not normalized_pattern:
            continue

        if fnmatch(normalized_value, normalized_pattern):
            return True

        if normalized_pattern in normalized_value:
            return True

    return False


class RulesEngine:
    def __init__(self, rulesets: list[RuleSet]):
        self.rulesets = rulesets

    def matching_rulesets(self, platform: Any) -> list[RuleSet]:
        normalized_platform = normalize_text(platform) or "_unknown"

        matched = [
            ruleset
            for ruleset in self.rulesets
            if normalized_platform
            in {
                normalize_text(item)
                for item in ruleset.platforms
            }
        ]

        matched.extend(
            [
                ruleset
                for ruleset in self.rulesets
                if "_global"
                in {
                    normalize_text(item)
                    for item in ruleset.platforms
                }
            ]
        )

        return matched

    def classify_entity(
        self,
        entity_id: Any,
        platform: Any,
    ) -> RuleResult:
        rulesets = self.matching_rulesets(platform)

        for ruleset in rulesets:
            if _matches_any(entity_id, ruleset.ignore):
                return RuleResult(
                    "ignored",
                    f"{ruleset.name}: ignored",
                )

            if _matches_any(entity_id, ruleset.diagnostic):
                return RuleResult(
                    "diagnostic",
                    f"{ruleset.name}: diagnostic",
                )

            if _matches_any(entity_id, ruleset.important):
                return RuleResult(
                    "important",
                    f"{ruleset.name}: important",
                )

        return RuleResult("normal", "default")

    def classify_device_by_words(self, name_blob: Any) -> str | None:
        blob = normalize_text(name_blob)

        for ruleset in self.rulesets:
            if any(
                normalize_text(word) in blob
                for word in ruleset.device_system_words
                if normalize_text(word)
            ):
                return "system"

            if any(
                normalize_text(word) in blob
                for word in ruleset.device_virtual_words
                if normalize_text(word)
            ):
                return "virtual"

        return None
