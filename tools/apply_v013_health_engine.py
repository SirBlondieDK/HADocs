from __future__ import annotations

from pathlib import Path

ROOT = Path(".")
CORE_HEALTH = Path("src/hadocs/core/health.py")
GENERATOR = Path("src/hadocs/reports/generator.py")
OLD_MODULE = Path("src/hadocs/analysis/health_score_v2.py")

HEALTH_ENGINE_TEXT = r"""from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HealthScoreBreakdown:
    score: int
    potential_score: int
    grade: str
    status: str
    enabled_entities: int
    disabled_entities_ignored: int
    affected_active_entities: int
    normalized_penalty: int
    severity_penalty: int
    root_cause_penalty: int

    def as_dict(self) -> dict[str, int | str]:
        return {
            "score": self.score,
            "potential_score": self.potential_score,
            "grade": self.grade,
            "status": self.status,
            "enabled_entities": self.enabled_entities,
            "disabled_entities_ignored": self.disabled_entities_ignored,
            "affected_active_entities": self.affected_active_entities,
            "normalized_penalty": self.normalized_penalty,
            "severity_penalty": self.severity_penalty,
            "root_cause_penalty": self.root_cause_penalty,
        }


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return list(value.values())
    return []


def is_disabled_entity(entity: Any) -> bool:
    """Return True when Home Assistant marks an entity as intentionally disabled."""

    if _get(entity, "disabled_by"):
        return True

    entity_registry = _get(entity, "entity_registry", {})
    if isinstance(entity_registry, dict) and entity_registry.get("disabled_by"):
        return True

    if bool(_get(entity, "disabled", False)):
        return True

    state = str(_get(entity, "state", "")).lower()
    return state in {"disabled", "unavailable_disabled"}


def _incident_severity(incident: Any) -> str:
    sev = str(_get(incident, "severity", "")).lower()
    if sev in {"critical", "error"}:
        return "critical"
    if sev in {"warning", "warn"}:
        return "warning"
    return "maintenance"


def _affected_entity_key(entity: Any) -> str:
    return str(
        _get(entity, "entity_id", None)
        or _get(entity, "id", None)
        or _get(entity, "unique_id", None)
        or entity
    )


def calculate_health_score_v2(model: Any, incidents: list[Any]) -> HealthScoreBreakdown:
    """Calculate a fairer Health Score for small and large HA installations.

    Design:
    - Disabled entities are ignored as active problems.
    - Affected-entity penalty is normalized by installation size.
    - Severity and root-cause penalties are capped so large installations do not
      get stuck at an artificially low score.
    """

    entities = _as_list(_get(model, "entities", []))
    enabled_entities = [entity for entity in entities if not is_disabled_entity(entity)]
    disabled_entities = max(0, len(entities) - len(enabled_entities))
    enabled_count = max(1, len(enabled_entities))

    affected_active: set[str] = set()
    disabled_problem_entities = 0

    for incident in incidents or []:
        for entity in _as_list(_get(incident, "affected_entities", [])):
            if is_disabled_entity(entity):
                disabled_problem_entities += 1
                continue
            affected_active.add(_affected_entity_key(entity))

    affected_count = len(affected_active)

    # Normalization: same number of problems hurts less in a larger install.
    # sqrt keeps severe large-installation issues visible without crushing score.
    normalized_penalty = round((affected_count / max(1.0, math.sqrt(enabled_count))) * 2.6)

    critical = 0
    warning = 0
    maintenance = 0

    for incident in incidents or []:
        severity = _incident_severity(incident)
        if severity == "critical":
            critical += 1
        elif severity == "warning":
            warning += 1
        else:
            maintenance += 1

    severity_penalty = min(28, critical * 3 + warning * 2 + maintenance)
    root_cause_penalty = min(18, round(len(incidents or []) * 0.9))

    total_penalty = min(75, normalized_penalty + severity_penalty + root_cause_penalty)
    score = max(25, 100 - total_penalty)

    potential_score = min(100, score + min(30, 6 + critical * 2 + warning))

    if score >= 90:
        grade, status = "A", "Excellent"
    elif score >= 80:
        grade, status = "B", "Healthy"
    elif score >= 65:
        grade, status = "C", "Needs attention"
    elif score >= 50:
        grade, status = "D", "Degraded"
    else:
        grade, status = "E", "Critical"

    return HealthScoreBreakdown(
        score=int(score),
        potential_score=int(potential_score),
        grade=grade,
        status=status,
        enabled_entities=int(enabled_count),
        disabled_entities_ignored=int(disabled_problem_entities or disabled_entities),
        affected_active_entities=int(affected_count),
        normalized_penalty=int(normalized_penalty),
        severity_penalty=int(severity_penalty),
        root_cause_penalty=int(root_cause_penalty),
    )


def apply_health_score_v2(model: Any, executive: Any, incidents: list[Any]) -> Any:
    """Enrich the existing executive object without changing its type."""

    breakdown = calculate_health_score_v2(model, incidents)
    data = breakdown.as_dict()

    if isinstance(executive, dict):
        executive["score"] = breakdown.score
        executive["potential_score"] = breakdown.potential_score
        executive["health_score_v2"] = data
        executive["health_grade"] = breakdown.grade
        executive["health_status_v2"] = breakdown.status
        return executive

    for key, value in {
        "score": breakdown.score,
        "potential_score": breakdown.potential_score,
        "health_score_v2": data,
        "health_grade": breakdown.grade,
        "health_status_v2": breakdown.status,
    }.items():
        try:
            setattr(executive, key, value)
        except Exception:
            pass

    return executive
"""


def ensure_health_engine() -> None:
    if not CORE_HEALTH.exists():
        raise SystemExit("Missing src/hadocs/core/health.py")

    text = CORE_HEALTH.read_text(encoding="utf-8")

    # Remove any older broken copies if they were already appended.
    marker = "class HealthScoreBreakdown:"
    if marker in text:
        text = text[: text.index("@dataclass(frozen=True)\nclass HealthScoreBreakdown:")].rstrip() + "\n\n"

    if "def calculate_health_score_v2(" not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + HEALTH_ENGINE_TEXT + "\n"

    CORE_HEALTH.write_text(text, encoding="utf-8")


def ensure_import(text: str, import_line: str) -> str:
    if import_line in text:
        return text

    # Remove old experimental import.
    text = text.replace("from src.hadocs.analysis.health_score_v2 import apply_health_score_v2\n", "")

    lines = text.splitlines(True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1

    lines.insert(insert_at, import_line + "\n")
    return "".join(lines)


def remove_broken_score_lines(text: str) -> str:
    bad_lines = [
        "executive = apply_health_score_v2(model, executive, incidents)\n",
        "    executive = apply_health_score_v2(model, executive, incidents)\n",
    ]
    for line in bad_lines:
        text = text.replace(line, "")
    return text


def indent_generate_all_calls(text: str) -> str:
    call_prefixes = (
        "generate_index(",
        "generate_executive_dashboard(",
        "generate_root_causes(",
        "generate_incidents(",
        "generate_summary(",
        "generate_areas(",
        "generate_devices(",
        "generate_integrations(",
        "generate_device_health(",
        "generate_maintenance(",
        "generate_problems(",
        "generate_rules_report(",
        "generate_relationships(",
        "generate_insights(",
        "generate_history(",
        "generate_architecture(",
        "export_entities_csv(",
        "export_devices_csv(",
        "executive = apply_health_score_v2(",
    )

    fixed = []
    for line in text.splitlines(True):
        stripped = line.lstrip()
        if line == stripped and stripped.startswith(call_prefixes):
            fixed.append("    " + line)
        else:
            fixed.append(line)
    return "".join(fixed)


def patch_generator() -> None:
    if not GENERATOR.exists():
        raise SystemExit("Missing src/hadocs/reports/generator.py")

    text = GENERATOR.read_text(encoding="utf-8")
    text = ensure_import(
        text,
        "from src.hadocs.core.health import apply_health_score_v2",
    )
    text = remove_broken_score_lines(text)

    marker = "generate_index(out, project_name, executive, incidents, now)"
    if marker not in text:
        raise SystemExit("Could not find generate_index call in generator.py")

    text = text.replace(
        marker,
        "executive = apply_health_score_v2(model, executive, incidents)\n" + marker,
        1,
    )

    text = indent_generate_all_calls(text)

    # Add dashboard explanation values if the Dashboard Engine v2 renderer is present.
    if 'health_score_v2 = get(executive, "health_score_v2", {})' not in text:
        text = text.replace(
            'score = clamp(get(executive, "score", 0))',
            'score = clamp(get(executive, "score", 0))\n'
            '    health_score_v2 = get(executive, "health_score_v2", {})\n'
            '    score_grade = get(health_score_v2, "grade", "-")\n'
            '    ignored_disabled = get(health_score_v2, "disabled_entities_ignored", 0)\n'
            '    affected_active = get(health_score_v2, "affected_active_entities", 0)\n'
            '    normalized_penalty = get(health_score_v2, "normalized_penalty", 0)\n'
            '    severity_penalty = get(health_score_v2, "severity_penalty", 0)\n'
            '    root_cause_penalty = get(health_score_v2, "root_cause_penalty", 0)',
            1,
        )

    if "Health Score v2" not in text and "{render_installation()}" in text:
        text = text.replace(
            "{render_installation()}",
            """{render_installation()}
      <section class="section panel" id="score-model">
        <div class="section-head">
          <h2>Health Score v2</h2>
          <p class="muted">Smarter scoring: disabled entities are ignored and penalties are normalized for large installations.</p>
        </div>
        <div class="grid four">
          {render_metric("Grade", score_grade)}
          {render_metric("Active affected entities", affected_active)}
          {render_metric("Disabled ignored", ignored_disabled)}
          {render_metric("Size-normalized penalty", normalized_penalty)}
          {render_metric("Severity penalty", severity_penalty)}
          {render_metric("Root-cause penalty", root_cause_penalty)}
        </div>
      </section>""",
            1,
        )

    GENERATOR.write_text(text, encoding="utf-8")


def neutralize_old_module() -> None:
    """Keep the old experimental module import-safe if it exists."""

    if OLD_MODULE.exists():
        OLD_MODULE.write_text(
            '"""Deprecated compatibility module. Use src.hadocs.core.health instead."""\n\n'
            "from src.hadocs.core.health import apply_health_score_v2, calculate_health_score_v2, is_disabled_entity\n",
            encoding="utf-8",
        )


def main() -> None:
    if not Path("src/hadocs").exists():
        raise SystemExit("Run from repository root: C:\\HomeAssistantDocs")

    ensure_health_engine()
    patch_generator()
    neutralize_old_module()

    print("v0.13 Health Engine applied.")
    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("Commit:")
    print("  git add src/hadocs/core/health.py src/hadocs/reports/generator.py src/hadocs/analysis/health_score_v2.py docs/V013_HEALTH_ENGINE.md tools/apply_v013_health_engine.py")
    print('  git commit -m "Add Health Engine v2 scoring"')
    print("  git push")


if __name__ == "__main__":
    main()
