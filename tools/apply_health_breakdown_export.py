from __future__ import annotations

from pathlib import Path
import re

EXPORTER = Path("src/hadocs/knowledge/exporter.py")
TEST = Path("tests/test_health_breakdown_export.py")
DOC = Path("docs/HEALTH_SCORE_BREAKDOWN_EXPORT.md")


NEW_BUILD_HEALTH = """def build_health(executive) -> dict:
    def get(obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    breakdown = get(executive, "health_score_v2", {}) or {}

    data = {
        "health_score": get(executive, "score"),
        "status": get(executive, "status"),
        "potential_score": get(executive, "potential_score"),
        "estimated_repair_minutes": get(executive, "estimated_repair_minutes"),
        "main_root_cause": get(executive, "main_cause"),
    }

    if breakdown:
        data["grade"] = get(executive, "health_grade", breakdown.get("grade"))
        data["status_v2"] = get(executive, "health_status_v2", breakdown.get("status"))
        data["breakdown"] = {
            "enabled_entities": breakdown.get("enabled_entities"),
            "disabled_entities_ignored": breakdown.get("disabled_entities_ignored"),
            "affected_active_entities": breakdown.get("affected_active_entities"),
            "normalized_penalty": breakdown.get("normalized_penalty"),
            "severity_penalty": breakdown.get("severity_penalty"),
            "root_cause_penalty": breakdown.get("root_cause_penalty"),
        }

    return data
"""


TEST_TEXT = """from src.hadocs.knowledge.exporter import build_health


def test_build_health_exports_v2_breakdown():
    executive = {
        "score": 78,
        "status": "GOOD",
        "potential_score": 93,
        "estimated_repair_minutes": 37,
        "main_cause": "Mobile App devices",
        "health_grade": "B",
        "health_status_v2": "Healthy",
        "health_score_v2": {
            "score": 78,
            "potential_score": 93,
            "grade": "B",
            "status": "Healthy",
            "enabled_entities": 1618,
            "disabled_entities_ignored": 0,
            "affected_active_entities": 176,
            "normalized_penalty": 2,
            "severity_penalty": 12,
            "root_cause_penalty": 5,
        },
    }

    health = build_health(executive)

    assert health["health_score"] == 78
    assert health["potential_score"] == 93
    assert health["grade"] == "B"
    assert health["status_v2"] == "Healthy"
    assert health["breakdown"]["affected_active_entities"] == 176
    assert health["breakdown"]["normalized_penalty"] == 2
    assert health["breakdown"]["severity_penalty"] == 12
    assert health["breakdown"]["root_cause_penalty"] == 5
"""


DOC_TEXT = """# Health Score Breakdown Export

Exports the Health Engine v2.1 breakdown into `output/knowledge/health.json`.

Example:

```json
{
  "health_score": 78,
  "status": "GOOD",
  "potential_score": 93,
  "grade": "B",
  "status_v2": "Healthy",
  "breakdown": {
    "enabled_entities": 1618,
    "disabled_entities_ignored": 0,
    "affected_active_entities": 176,
    "normalized_penalty": 2,
    "severity_penalty": 12,
    "root_cause_penalty": 5
  }
}
```

This makes the Health Score explainable without changing the dashboard layout.
"""


def patch_exporter(text: str) -> str:
    pattern = re.compile(
        r"def build_health\\(executive\\) -> dict:\\n"
        r".*?\\n\\n"
        r"def build_incidents\\(incidents\\) -> list\\[dict\\]:",
        re.S,
    )

    replacement = NEW_BUILD_HEALTH + "\\n\\ndef build_incidents(incidents) -> list[dict]:"
    new_text, count = pattern.subn(replacement, text)
    if count != 1:
        raise SystemExit("Could not patch build_health() in src/hadocs/knowledge/exporter.py")
    return new_text


def main() -> None:
    if not EXPORTER.exists():
        raise SystemExit("Run from repository root: C:\\\\HomeAssistantDocs")

    EXPORTER.write_text(patch_exporter(EXPORTER.read_text(encoding="utf-8")), encoding="utf-8")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    DOC.write_text(DOC_TEXT, encoding="utf-8")

    print("Health breakdown export applied.")
    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  rmdir /s /q output")
    print("  py -3.14 main.py generate")
    print("  type output\\knowledge\\health.json")
    print("")
    print("Commit:")
    print("  git add src/hadocs/core/health.py src/hadocs/knowledge/exporter.py tests/test_health_breakdown_export.py docs/HEALTH_SCORE_BREAKDOWN_EXPORT.md tools/apply_health_breakdown_export.py")
    print('  git commit -m "Calibrate health score and export breakdown"')
    print("  git push")


if __name__ == "__main__":
    main()
