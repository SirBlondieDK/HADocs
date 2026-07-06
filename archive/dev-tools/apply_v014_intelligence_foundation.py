from __future__ import annotations

from pathlib import Path

GENERATOR = Path("src/hadocs/reports/generator.py")
ENGINE = Path("src/hadocs/core/intelligence.py")

ENGINE_TEXT = r'''from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ForecastStep:
    title: str
    root_cause: str
    score_gain: int
    repair_minutes: int
    health_after: int
    impact_score: int
    impact_label: str

    def as_dict(self) -> dict[str, int | str]:
        return self.__dict__.copy()


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


def _num(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _severity(incident: Any) -> str:
    severity = str(_get(incident, "severity", "")).lower()
    if severity in {"critical", "error"}:
        return "critical"
    if severity in {"warning", "warn"}:
        return "warning"
    return "maintenance"


def _root(incident: Any) -> str:
    return str(_get(incident, "root_cause", _get(incident, "title", "Issue")))


def _title(incident: Any) -> str:
    return str(_get(incident, "title", _root(incident)))


def _affected_entities(incident: Any) -> list[Any]:
    return _as_list(_get(incident, "affected_entities", []))


def _affected_devices(incident: Any) -> list[Any]:
    return _as_list(_get(incident, "affected_devices", []))


def _children(incident: Any) -> list[Any]:
    return _as_list(_get(incident, "children", [])) or _as_list(_get(incident, "child_incidents", []))


def calculate_impact_score(incident: Any) -> int:
    entities = len(_affected_entities(incident))
    devices = len(_affected_devices(incident))
    children = _num(_get(incident, "child_count", len(_children(incident))), len(_children(incident)))
    gain = _num(_get(incident, "estimated_score_gain", 0))
    minutes = max(1, _num(_get(incident, "estimated_repair_minutes", 5), 5))
    severity_bonus = {"critical": 35, "warning": 18, "maintenance": 8}.get(_severity(incident), 8)
    effort_bonus = max(0, 12 - min(12, minutes))
    score = severity_bonus + round(entities * 0.35) + round(devices * 1.5) + round(children * 1.8) + gain * 6 + effort_bonus
    return int(max(1, min(100, score)))


def impact_label(score: int) -> str:
    if score >= 85:
        return "Extreme impact"
    if score >= 65:
        return "High impact"
    if score >= 40:
        return "Medium impact"
    if score >= 20:
        return "Low impact"
    return "Minor impact"


def explain_root_cause(incident: Any) -> dict[str, str]:
    root = _root(incident)
    entities = len(_affected_entities(incident))
    devices = len(_affected_devices(incident))
    children = _num(_get(incident, "child_count", len(_children(incident))), len(_children(incident)))
    gain = _num(_get(incident, "estimated_score_gain", 0))
    minutes = _num(_get(incident, "estimated_repair_minutes", 5), 5)
    severity = _severity(incident)
    root_lower = root.lower()

    if "mobile" in root_lower or "app" in root_lower:
        why = "One or more Home Assistant Companion App devices appear offline or have stopped updating."
        verify = "Open the Companion App on the affected devices and confirm that they can reach Home Assistant."
        fix = "Refresh or restart the Companion App, verify network access, and check background update permissions."
    elif "mqtt" in root_lower:
        why = "MQTT is a central message bus. When it is unhealthy, many sensors and integrations can become unavailable at once."
        verify = "Open the MQTT integration and broker logs. Confirm clients are connected and messages are flowing."
        fix = "Restart the MQTT broker, verify credentials, and reconnect affected clients."
    elif "frigate" in root_lower:
        why = "Frigate provides camera and object-detection entities. If it is unavailable, camera-related entities can fail together."
        verify = "Open Frigate and check service status, logs, camera streams and detector health."
        fix = "Restart Frigate, verify camera streams, and check hardware acceleration or detector availability."
    elif "icloud" in root_lower:
        why = "iCloud entities depend on account authentication and cloud availability."
        verify = "Check the iCloud integration for reauthentication prompts or account errors."
        fix = "Reauthenticate iCloud and verify that tracked devices update again."
    else:
        why = f"HADocs detected that several symptoms point back to the same root cause: {root}."
        verify = "Open the related integration or device in Home Assistant and check logs, availability and recent changes."
        fix = "Fix the parent integration or device first, then rescan to confirm child incidents disappear."

    impact = f"This is marked as {severity}. It affects {entities} entities, {devices} devices and has {children} child incidents. Fixing it may improve Health Score by +{gain}."
    return {"why": why, "impact": impact, "verify": verify, "fix": fix, "time": f"Estimated repair time: about {minutes} minutes."}


def build_health_forecast(current_score: int, incidents: list[Any], limit: int = 6) -> list[dict[str, int | str]]:
    score = max(0, min(100, _num(current_score)))
    selected = sorted(list(incidents or []), key=lambda i: (calculate_impact_score(i), _num(_get(i, "estimated_score_gain", 0))), reverse=True)[:limit]
    steps = []
    for incident in selected:
        gain = max(0, _num(_get(incident, "estimated_score_gain", 0)))
        score = min(100, score + gain)
        impact = calculate_impact_score(incident)
        steps.append(ForecastStep(_title(incident), _root(incident), gain, _num(_get(incident, "estimated_repair_minutes", 5), 5), score, impact, impact_label(impact)).as_dict())
    return steps


def apply_intelligence_v014(model: Any, executive: Any, incidents: list[Any]) -> Any:
    current_score = _num(_get(executive, "score", 0))
    forecast = build_health_forecast(current_score, incidents, limit=6)
    enriched = []
    for incident in incidents or []:
        impact = calculate_impact_score(incident)
        enriched.append({"root_cause": _root(incident), "title": _title(incident), "impact_score": impact, "impact_label": impact_label(impact), "explain": explain_root_cause(incident)})

    if isinstance(executive, dict):
        executive["health_forecast"] = forecast
        executive["root_cause_intelligence"] = enriched
        return executive

    try:
        setattr(executive, "health_forecast", forecast)
        setattr(executive, "root_cause_intelligence", enriched)
    except Exception:
        pass
    return executive
'''


def ensure_import(text: str) -> str:
    wanted = "from src.hadocs.core.intelligence import apply_intelligence_v014\n"
    if wanted in text:
        return text
    lines = text.splitlines(True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1
    lines.insert(insert_at, wanted)
    return "".join(lines)


def patch_generate_all(text: str) -> str:
    line = "executive = apply_intelligence_v014(model, executive, incidents)"
    if line in text:
        return text
    if "executive = apply_health_score_v2(model, executive, incidents)" in text:
        return text.replace(
            "executive = apply_health_score_v2(model, executive, incidents)",
            "executive = apply_health_score_v2(model, executive, incidents)\n    " + line,
            1,
        )
    marker = "generate_index(out, project_name, executive, incidents, now)"
    return text.replace(marker, line + "\n    " + marker, 1)


def patch_dashboard(text: str) -> str:
    if 'health_forecast = get(executive, "health_forecast", [])' not in text and 'score = clamp(get(executive, "score", 0))' in text:
        text = text.replace(
            'score = clamp(get(executive, "score", 0))',
            'score = clamp(get(executive, "score", 0))\n'
            '    health_forecast = get(executive, "health_forecast", [])\n'
            '    root_cause_intelligence = get(executive, "root_cause_intelligence", [])',
            1,
        )

    if "Health Forecast" not in text and "    def render_output_links():" in text:
        funcs = '''
    def render_health_forecast():
        rows = []
        for idx, step in enumerate(health_forecast[:6], 1):
            after = get(step, "health_after", 0)
            rows.append(f"""
            <div class="forecast-step">
              <div class="forecast-number">{idx}</div>
              <div class="forecast-body">
                <strong>{esc(get(step, "root_cause", "Issue"))}</strong>
                <p class="muted">{esc(get(step, "title", ""))}</p>
                <div class="badges">
                  <span>+{esc(get(step, "score_gain", 0))} score</span>
                  <span>{esc(get(step, "impact_label", "Impact"))}</span>
                  <span>~{esc(get(step, "repair_minutes", 0))} min</span>
                </div>
                <div class="impact-bar"><i style="width:{min(100, max(3, int(after)))}%"></i></div>
                <p class="muted">Health after this fix: <strong>{esc(after)}/100</strong></p>
              </div>
            </div>
            """)
        if not rows:
            rows.append("<p class='muted'>No forecast available yet.</p>")
        return f"""
        <section class="section panel" id="forecast">
          <div class="section-head">
            <h2>Health Forecast</h2>
            <p class="muted">A prioritized repair path based on expected health gain and impact.</p>
          </div>
          <div class="forecast">{''.join(rows)}</div>
        </section>
        """

    def intelligence_for(root):
        for item in root_cause_intelligence:
            if get(item, "root_cause", "") == root:
                return item
        return {}

'''
        text = text.replace("    def render_output_links():", funcs + "\n    def render_output_links():", 1)

    if "{render_health_forecast()}" not in text:
        if "{render_actions()}" in text:
            text = text.replace("{render_actions()}", "{render_health_forecast()}\n      {render_actions()}", 1)

    if 'info = intelligence_for(root_of(incident))' not in text:
        text = text.replace(
            'for incident in visible[:18]:\n            sev = severity_of(incident)',
            'for incident in visible[:18]:\n            info = intelligence_for(root_of(incident))\n            explanation = get(info, "explain", {})\n            impact_score = get(info, "impact_score", 0)\n            impact_label_text = get(info, "impact_label", "Impact")\n            sev = severity_of(incident)',
            1,
        )

    if "{esc(impact_label_text)}" not in text:
        text = text.replace(
            '<span>~{esc(minutes)} min</span>',
            '<span>~{esc(minutes)} min</span>\n                <span>{esc(impact_label_text)}</span>\n                <span>{esc(impact_score)} impact</span>',
            1,
        )

    if "Explain this</summary>" not in text:
        text = text.replace(
            "{child_html}\n            </article>",
            """
              <details class="explain">
                <summary>Explain this</summary>
                <h4>Why this happened</h4>
                <p>{esc(get(explanation, "why", ""))}</p>
                <h4>Impact</h4>
                <p>{esc(get(explanation, "impact", ""))}</p>
                <h4>How to verify</h4>
                <p>{esc(get(explanation, "verify", ""))}</p>
                <h4>Suggested fix</h4>
                <p>{esc(get(explanation, "fix", ""))}</p>
                <p class="muted">{esc(get(explanation, "time", ""))}</p>
              </details>
              {child_html}
            </article>""",
            1,
        )

    if ".forecast-step" not in text:
        text = text.replace(
            ".footer{margin:34px 0 10px;color:var(--muted);font-size:13px}",
            ".footer{margin:34px 0 10px;color:var(--muted);font-size:13px}"
            ".forecast{display:grid;gap:14px}.forecast-step{display:flex;gap:16px;border:1px solid var(--border);border-radius:18px;background:#0d1424;padding:18px}"
            ".forecast-number{width:34px;height:34px;border-radius:999px;background:#243044;display:grid;place-items:center;font-weight:900;flex:0 0 auto}"
            ".forecast-body{flex:1}.explain{margin-top:16px;border-top:1px solid var(--border);padding-top:12px}.explain h4{margin:12px 0 4px}",
            1,
        )
    return text


def main() -> None:
    if not GENERATOR.exists():
        raise SystemExit("Run from repository root")
    ENGINE.parent.mkdir(parents=True, exist_ok=True)
    ENGINE.write_text(ENGINE_TEXT, encoding="utf-8")
    text = GENERATOR.read_text(encoding="utf-8")
    text = ensure_import(text)
    text = patch_generate_all(text)
    text = patch_dashboard(text)
    GENERATOR.write_text(text, encoding="utf-8")
    print("v0.14 Intelligence Foundation applied.")
    print("Run: py -3.14 -m pytest")
    print("Run: py -3.14 main.py")


if __name__ == "__main__":
    main()
