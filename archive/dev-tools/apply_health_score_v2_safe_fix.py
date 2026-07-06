from __future__ import annotations

from pathlib import Path

GENERATOR = Path("src/hadocs/reports/generator.py")
MODULE = Path("src/hadocs/analysis/health_score_v2.py")

MODULE_TEXT = r"""from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HealthScoreV2Result:
    score: int
    potential_score: int
    status: str
    grade: str
    affected_active_entities: int
    disabled_ignored: int
    entity_count: int
    normalized_penalty: int
    severity_penalty: int
    root_cause_penalty: int


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
    disabled_by = _get(entity, "disabled_by")
    if disabled_by:
        return True

    registry = _get(entity, "entity_registry", {})
    if isinstance(registry, dict) and registry.get("disabled_by"):
        return True

    if bool(_get(entity, "disabled", False)):
        return True

    state = str(_get(entity, "state", "")).lower()
    return state in {"disabled", "unavailable_disabled"}


def calculate_health_score_v2(model: Any, incidents: list[Any]) -> HealthScoreV2Result:
    entities = _as_list(_get(model, "entities", []))
    enabled_entities = [e for e in entities if not is_disabled_entity(e)]
    disabled_ignored = max(0, len(entities) - len(enabled_entities))
    entity_count = max(1, len(enabled_entities))

    affected_ids: set[str] = set()
    disabled_problem_count = 0

    for incident in incidents or []:
        for entity in _as_list(_get(incident, "affected_entities", [])):
            if is_disabled_entity(entity):
                disabled_problem_count += 1
                continue
            entity_id = _get(entity, "entity_id", None) or _get(entity, "id", None) or str(entity)
            affected_ids.add(str(entity_id))

    affected_active = len(affected_ids)

    scale = max(1.0, math.sqrt(entity_count))
    normalized_penalty = round((affected_active / scale) * 2.6)

    critical = 0
    warnings = 0
    maintenance = 0

    for incident in incidents or []:
        sev = str(_get(incident, "severity", "")).lower()
        if sev in {"critical", "error"}:
            critical += 1
        elif sev in {"warning", "warn"}:
            warnings += 1
        else:
            maintenance += 1

    severity_penalty = min(28, critical * 3 + warnings * 2 + maintenance)
    root_cause_penalty = min(18, round(len(incidents or []) * 0.9))

    total_penalty = min(75, normalized_penalty + severity_penalty + root_cause_penalty)
    score = max(25, 100 - total_penalty)
    potential_score = min(100, score + min(30, 6 + critical * 2 + warnings))

    if score >= 90:
        status, grade = "Excellent", "A"
    elif score >= 80:
        status, grade = "Healthy", "B"
    elif score >= 65:
        status, grade = "Needs attention", "C"
    elif score >= 50:
        status, grade = "Degraded", "D"
    else:
        status, grade = "Critical", "E"

    return HealthScoreV2Result(
        score=int(score),
        potential_score=int(potential_score),
        status=status,
        grade=grade,
        affected_active_entities=affected_active,
        disabled_ignored=int(disabled_problem_count or disabled_ignored),
        entity_count=entity_count,
        normalized_penalty=int(normalized_penalty),
        severity_penalty=int(severity_penalty),
        root_cause_penalty=int(root_cause_penalty),
    )


def apply_health_score_v2(model: Any, executive: Any, incidents: list[Any]) -> Any:
    \"\"\"Safely enrich the existing executive object/dict.

    Important: this function returns the same executive shape it received.
    It does not replace the executive model, so existing dashboard/tests keep
    working.
    \"\"\"

    result = calculate_health_score_v2(model, incidents)
    data = result.__dict__

    if isinstance(executive, dict):
        executive["score"] = result.score
        executive["potential_score"] = result.potential_score
        executive["health_score_v2"] = data
        executive["health_grade"] = result.grade
        executive["health_status_v2"] = result.status
        return executive

    for key, value in {
        "score": result.score,
        "potential_score": result.potential_score,
        "health_score_v2": data,
        "health_grade": result.grade,
        "health_status_v2": result.status,
    }.items():
        try:
            setattr(executive, key, value)
        except Exception:
            pass

    return executive
"""


def ensure_import(text: str, line: str) -> str:
    if line in text:
        return text
    lines = text.splitlines(True)
    pos = 0
    for i, item in enumerate(lines):
        if item.startswith("import ") or item.startswith("from "):
            pos = i + 1
    lines.insert(pos, line + "\n")
    return "".join(lines)


def fix_generate_all_block(text: str) -> str:
    # Remove broken/duplicated score application lines first.
    broken_lines = [
        "    executive = apply_health_score_v2(model, executive, incidents)\n",
        "executive = apply_health_score_v2(model, executive, incidents)\n",
    ]
    for line in broken_lines:
        text = text.replace(line, "")

    marker = "generate_index(out, project_name, executive, incidents, now)"
    if marker not in text:
        raise RuntimeError("Could not find generate_index call")

    # Insert score application directly before generate_index, with correct indentation.
    text = text.replace(
        marker,
        "executive = apply_health_score_v2(model, executive, incidents)\n" + marker,
        1,
    )

    # Fix accidental over-indented dashboard call.
    text = text.replace(
        "    generate_executive_dashboard(out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now)",
        "generate_executive_dashboard(out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now)",
    )

    # Now indent all known generate_all calls with exactly four spaces if they are at column 0.
    call_prefixes = [
        "executive = apply_health_score_v2(",
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
    ]

    fixed = []
    for line in text.splitlines(True):
        stripped = line.lstrip()
        if line == stripped and any(stripped.startswith(prefix) for prefix in call_prefixes):
            fixed.append("    " + line)
        else:
            fixed.append(line)
    return "".join(fixed)


def patch_dashboard_explanation(text: str) -> str:
    # Optional UI enhancement; only patches when the v2 dashboard renderer text exists.
    if 'health_score_v2 = get(executive, "health_score_v2", {})' not in text:
        text = text.replace(
            'score = clamp(get(executive, "score", 0))',
            'score = clamp(get(executive, "score", 0))\n'
            '    health_score_v2 = get(executive, "health_score_v2", {})\n'
            '    score_grade = get(health_score_v2, "grade", "-")\n'
            '    ignored_disabled = get(health_score_v2, "disabled_ignored", 0)\n'
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
          {render_metric("Disabled ignored", ignored_disabled)}
          {render_metric("Size-normalized penalty", normalized_penalty)}
          {render_metric("Severity penalty", severity_penalty)}
        </div>
        <p class="muted">Root-cause penalty: {esc(root_cause_penalty)}. This keeps serious issues visible without punishing large installations unfairly.</p>
      </section>""",
            1,
        )

    return text


def main() -> None:
    if not GENERATOR.exists():
        raise SystemExit("Run from repository root: C:\\HomeAssistantDocs")

    MODULE.parent.mkdir(parents=True, exist_ok=True)
    MODULE.write_text(MODULE_TEXT, encoding="utf-8")

    text = GENERATOR.read_text(encoding="utf-8")
    text = ensure_import(text, "from src.hadocs.analysis.health_score_v2 import apply_health_score_v2")
    text = fix_generate_all_block(text)
    text = patch_dashboard_explanation(text)
    GENERATOR.write_text(text, encoding="utf-8")

    print("Safe Health Score v2 integration applied.")
    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("If green:")
    print("  git add src/hadocs/analysis/health_score_v2.py src/hadocs/reports/generator.py docs/V102_HEALTH_SCORE_V2_SAFE_FIX.md tools/apply_health_score_v2_safe_fix.py")
    print('  git commit -m "Safely integrate Health Score v2"')
    print("  git push")


if __name__ == "__main__":
    main()
