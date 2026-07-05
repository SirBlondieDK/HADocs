from dataclasses import dataclass, field
from fnmatch import fnmatch


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


def _matches_any(value: str, patterns: list[str]) -> bool:
    value = value.lower()
    for pattern in patterns:
        pattern = pattern.lower()
        if fnmatch(value, pattern):
            return True
        if pattern in value:
            return True
    return False


class RulesEngine:
    def __init__(self, rulesets: list[RuleSet]):
        self.rulesets = rulesets

    def matching_rulesets(self, platform: str) -> list[RuleSet]:
        platform = (platform or "_unknown").lower()
        matched = [
            ruleset for ruleset in self.rulesets
            if platform in {p.lower() for p in ruleset.platforms}
        ]
        matched.extend([
            ruleset for ruleset in self.rulesets
            if "_global" in {p.lower() for p in ruleset.platforms}
        ])
        return matched

    def classify_entity(self, entity_id: str, platform: str) -> RuleResult:
        rulesets = self.matching_rulesets(platform)

        for ruleset in rulesets:
            if _matches_any(entity_id, ruleset.ignore):
                return RuleResult("ignored", f"{ruleset.name}: ignored")
            if _matches_any(entity_id, ruleset.diagnostic):
                return RuleResult("diagnostic", f"{ruleset.name}: diagnostic")
            if _matches_any(entity_id, ruleset.important):
                return RuleResult("important", f"{ruleset.name}: important")

        return RuleResult("normal", "default")

    def classify_device_by_words(self, name_blob: str) -> str | None:
        blob = name_blob.lower()

        for ruleset in self.rulesets:
            if any(word.lower() in blob for word in ruleset.device_system_words):
                return "system"
            if any(word.lower() in blob for word in ruleset.device_virtual_words):
                return "virtual"

        return None
