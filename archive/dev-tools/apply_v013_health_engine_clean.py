
from __future__ import annotations

from pathlib import Path
import base64
import re

CORE_HEALTH = Path("src/hadocs/core/health.py")
GENERATOR = Path("src/hadocs/reports/generator.py")
OLD_MODULE = Path("src/hadocs/analysis/health_score_v2.py")

HEALTH_APPEND = base64.b64decode("CiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCiMgSGVhbHRoIEVuZ2luZSB2MgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQoKaW1wb3J0IG1hdGgKZnJvbSBkYXRhY2xhc3NlcyBpbXBvcnQgZGF0YWNsYXNzCmZyb20gdHlwaW5nIGltcG9ydCBBbnkKCgpAZGF0YWNsYXNzKGZyb3plbj1UcnVlKQpjbGFzcyBIZWFsdGhTY29yZUJyZWFrZG93bjoKICAgIHNjb3JlOiBpbnQKICAgIHBvdGVudGlhbF9zY29yZTogaW50CiAgICBncmFkZTogc3RyCiAgICBzdGF0dXM6IHN0cgogICAgZW5hYmxlZF9lbnRpdGllczogaW50CiAgICBkaXNhYmxlZF9lbnRpdGllc19pZ25vcmVkOiBpbnQKICAgIGFmZmVjdGVkX2FjdGl2ZV9lbnRpdGllczogaW50CiAgICBub3JtYWxpemVkX3BlbmFsdHk6IGludAogICAgc2V2ZXJpdHlfcGVuYWx0eTogaW50CiAgICByb290X2NhdXNlX3BlbmFsdHk6IGludAoKICAgIGRlZiBhc19kaWN0KHNlbGYpIC0+IGRpY3Rbc3RyLCBpbnQgfCBzdHJdOgogICAgICAgIHJldHVybiB7CiAgICAgICAgICAgICJzY29yZSI6IHNlbGYuc2NvcmUsCiAgICAgICAgICAgICJwb3RlbnRpYWxfc2NvcmUiOiBzZWxmLnBvdGVudGlhbF9zY29yZSwKICAgICAgICAgICAgImdyYWRlIjogc2VsZi5ncmFkZSwKICAgICAgICAgICAgInN0YXR1cyI6IHNlbGYuc3RhdHVzLAogICAgICAgICAgICAiZW5hYmxlZF9lbnRpdGllcyI6IHNlbGYuZW5hYmxlZF9lbnRpdGllcywKICAgICAgICAgICAgImRpc2FibGVkX2VudGl0aWVzX2lnbm9yZWQiOiBzZWxmLmRpc2FibGVkX2VudGl0aWVzX2lnbm9yZWQsCiAgICAgICAgICAgICJhZmZlY3RlZF9hY3RpdmVfZW50aXRpZXMiOiBzZWxmLmFmZmVjdGVkX2FjdGl2ZV9lbnRpdGllcywKICAgICAgICAgICAgIm5vcm1hbGl6ZWRfcGVuYWx0eSI6IHNlbGYubm9ybWFsaXplZF9wZW5hbHR5LAogICAgICAgICAgICAic2V2ZXJpdHlfcGVuYWx0eSI6IHNlbGYuc2V2ZXJpdHlfcGVuYWx0eSwKICAgICAgICAgICAgInJvb3RfY2F1c2VfcGVuYWx0eSI6IHNlbGYucm9vdF9jYXVzZV9wZW5hbHR5LAogICAgICAgIH0KCgpkZWYgX2hzX2dldChvYmo6IEFueSwgbmFtZTogc3RyLCBkZWZhdWx0OiBBbnkgPSBOb25lKSAtPiBBbnk6CiAgICBpZiBpc2luc3RhbmNlKG9iaiwgZGljdCk6CiAgICAgICAgcmV0dXJuIG9iai5nZXQobmFtZSwgZGVmYXVsdCkKICAgIHJldHVybiBnZXRhdHRyKG9iaiwgbmFtZSwgZGVmYXVsdCkKCgpkZWYgX2hzX2xpc3QodmFsdWU6IEFueSkgLT4gbGlzdFtBbnldOgogICAgaWYgdmFsdWUgaXMgTm9uZToKICAgICAgICByZXR1cm4gW10KICAgIGlmIGlzaW5zdGFuY2UodmFsdWUsIGxpc3QpOgogICAgICAgIHJldHVybiB2YWx1ZQogICAgaWYgaXNpbnN0YW5jZSh2YWx1ZSwgdHVwbGUpOgogICAgICAgIHJldHVybiBsaXN0KHZhbHVlKQogICAgaWYgaXNpbnN0YW5jZSh2YWx1ZSwgZGljdCk6CiAgICAgICAgcmV0dXJuIGxpc3QodmFsdWUudmFsdWVzKCkpCiAgICByZXR1cm4gW10KCgpkZWYgaXNfZGlzYWJsZWRfZW50aXR5KGVudGl0eTogQW55KSAtPiBib29sOgogICAgZGlzYWJsZWRfYnkgPSBfaHNfZ2V0KGVudGl0eSwgImRpc2FibGVkX2J5IikKICAgIGlmIGRpc2FibGVkX2J5OgogICAgICAgIHJldHVybiBUcnVlCgogICAgcmVnaXN0cnkgPSBfaHNfZ2V0KGVudGl0eSwgImVudGl0eV9yZWdpc3RyeSIsIHt9KQogICAgaWYgaXNpbnN0YW5jZShyZWdpc3RyeSwgZGljdCkgYW5kIHJlZ2lzdHJ5LmdldCgiZGlzYWJsZWRfYnkiKToKICAgICAgICByZXR1cm4gVHJ1ZQoKICAgIGlmIGJvb2woX2hzX2dldChlbnRpdHksICJkaXNhYmxlZCIsIEZhbHNlKSk6CiAgICAgICAgcmV0dXJuIFRydWUKCiAgICBzdGF0ZSA9IHN0cihfaHNfZ2V0KGVudGl0eSwgInN0YXRlIiwgIiIpKS5sb3dlcigpCiAgICByZXR1cm4gc3RhdGUgaW4geyJkaXNhYmxlZCIsICJ1bmF2YWlsYWJsZV9kaXNhYmxlZCJ9CgoKZGVmIF9oc19zZXZlcml0eShpbmNpZGVudDogQW55KSAtPiBzdHI6CiAgICBzZXZlcml0eSA9IHN0cihfaHNfZ2V0KGluY2lkZW50LCAic2V2ZXJpdHkiLCAiIikpLmxvd2VyKCkKICAgIGlmIHNldmVyaXR5IGluIHsiY3JpdGljYWwiLCAiZXJyb3IifToKICAgICAgICByZXR1cm4gImNyaXRpY2FsIgogICAgaWYgc2V2ZXJpdHkgaW4geyJ3YXJuaW5nIiwgIndhcm4ifToKICAgICAgICByZXR1cm4gIndhcm5pbmciCiAgICByZXR1cm4gIm1haW50ZW5hbmNlIgoKCmRlZiBfaHNfZW50aXR5X2tleShlbnRpdHk6IEFueSkgLT4gc3RyOgogICAgcmV0dXJuIHN0cigKICAgICAgICBfaHNfZ2V0KGVudGl0eSwgImVudGl0eV9pZCIsIE5vbmUpCiAgICAgICAgb3IgX2hzX2dldChlbnRpdHksICJpZCIsIE5vbmUpCiAgICAgICAgb3IgX2hzX2dldChlbnRpdHksICJ1bmlxdWVfaWQiLCBOb25lKQogICAgICAgIG9yIGVudGl0eQogICAgKQoKCmRlZiBjYWxjdWxhdGVfaGVhbHRoX3Njb3JlX3YyKG1vZGVsOiBBbnksIGluY2lkZW50czogbGlzdFtBbnldKSAtPiBIZWFsdGhTY29yZUJyZWFrZG93bjoKICAgIGVudGl0aWVzID0gX2hzX2xpc3QoX2hzX2dldChtb2RlbCwgImVudGl0aWVzIiwgW10pKQogICAgZW5hYmxlZF9lbnRpdGllcyA9IFtlbnRpdHkgZm9yIGVudGl0eSBpbiBlbnRpdGllcyBpZiBub3QgaXNfZGlzYWJsZWRfZW50aXR5KGVudGl0eSldCiAgICBkaXNhYmxlZF9lbnRpdGllcyA9IG1heCgwLCBsZW4oZW50aXRpZXMpIC0gbGVuKGVuYWJsZWRfZW50aXRpZXMpKQogICAgZW5hYmxlZF9jb3VudCA9IG1heCgxLCBsZW4oZW5hYmxlZF9lbnRpdGllcykpCgogICAgYWZmZWN0ZWRfYWN0aXZlOiBzZXRbc3RyXSA9IHNldCgpCiAgICBkaXNhYmxlZF9wcm9ibGVtX2VudGl0aWVzID0gMAoKICAgIGZvciBpbmNpZGVudCBpbiBpbmNpZGVudHMgb3IgW106CiAgICAgICAgZm9yIGVudGl0eSBpbiBfaHNfbGlzdChfaHNfZ2V0KGluY2lkZW50LCAiYWZmZWN0ZWRfZW50aXRpZXMiLCBbXSkpOgogICAgICAgICAgICBpZiBpc19kaXNhYmxlZF9lbnRpdHkoZW50aXR5KToKICAgICAgICAgICAgICAgIGRpc2FibGVkX3Byb2JsZW1fZW50aXRpZXMgKz0gMQogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgYWZmZWN0ZWRfYWN0aXZlLmFkZChfaHNfZW50aXR5X2tleShlbnRpdHkpKQoKICAgIGFmZmVjdGVkX2NvdW50ID0gbGVuKGFmZmVjdGVkX2FjdGl2ZSkKCiAgICAjIEZhaXJlciBzY29yaW5nIGZvciBsYXJnZSBpbnN0YWxsYXRpb25zOgogICAgIyBzYW1lIGFic29sdXRlIGlzc3VlIGNvdW50IHNob3VsZCBodXJ0IGxlc3MgaW4gYSAyMDAwIGVudGl0eSBpbnN0YWxsIHRoYW4gaW4gYSAxMDAgZW50aXR5IGluc3RhbGwuCiAgICBub3JtYWxpemVkX3BlbmFsdHkgPSByb3VuZCgoYWZmZWN0ZWRfY291bnQgLyBtYXgoMS4wLCBtYXRoLnNxcnQoZW5hYmxlZF9jb3VudCkpKSAqIDIuNikKCiAgICBjcml0aWNhbCA9IDAKICAgIHdhcm5pbmcgPSAwCiAgICBtYWludGVuYW5jZSA9IDAKCiAgICBmb3IgaW5jaWRlbnQgaW4gaW5jaWRlbnRzIG9yIFtdOgogICAgICAgIHNldmVyaXR5ID0gX2hzX3NldmVyaXR5KGluY2lkZW50KQogICAgICAgIGlmIHNldmVyaXR5ID09ICJjcml0aWNhbCI6CiAgICAgICAgICAgIGNyaXRpY2FsICs9IDEKICAgICAgICBlbGlmIHNldmVyaXR5ID09ICJ3YXJuaW5nIjoKICAgICAgICAgICAgd2FybmluZyArPSAxCiAgICAgICAgZWxzZToKICAgICAgICAgICAgbWFpbnRlbmFuY2UgKz0gMQoKICAgIHNldmVyaXR5X3BlbmFsdHkgPSBtaW4oMjgsIGNyaXRpY2FsICogMyArIHdhcm5pbmcgKiAyICsgbWFpbnRlbmFuY2UpCiAgICByb290X2NhdXNlX3BlbmFsdHkgPSBtaW4oMTgsIHJvdW5kKGxlbihpbmNpZGVudHMgb3IgW10pICogMC45KSkKCiAgICB0b3RhbF9wZW5hbHR5ID0gbWluKDc1LCBub3JtYWxpemVkX3BlbmFsdHkgKyBzZXZlcml0eV9wZW5hbHR5ICsgcm9vdF9jYXVzZV9wZW5hbHR5KQogICAgc2NvcmUgPSBtYXgoMjUsIDEwMCAtIHRvdGFsX3BlbmFsdHkpCiAgICBwb3RlbnRpYWxfc2NvcmUgPSBtaW4oMTAwLCBzY29yZSArIG1pbigzMCwgNiArIGNyaXRpY2FsICogMiArIHdhcm5pbmcpKQoKICAgIGlmIHNjb3JlID49IDkwOgogICAgICAgIGdyYWRlLCBzdGF0dXMgPSAiQSIsICJFeGNlbGxlbnQiCiAgICBlbGlmIHNjb3JlID49IDgwOgogICAgICAgIGdyYWRlLCBzdGF0dXMgPSAiQiIsICJIZWFsdGh5IgogICAgZWxpZiBzY29yZSA+PSA2NToKICAgICAgICBncmFkZSwgc3RhdHVzID0gIkMiLCAiTmVlZHMgYXR0ZW50aW9uIgogICAgZWxpZiBzY29yZSA+PSA1MDoKICAgICAgICBncmFkZSwgc3RhdHVzID0gIkQiLCAiRGVncmFkZWQiCiAgICBlbHNlOgogICAgICAgIGdyYWRlLCBzdGF0dXMgPSAiRSIsICJDcml0aWNhbCIKCiAgICByZXR1cm4gSGVhbHRoU2NvcmVCcmVha2Rvd24oCiAgICAgICAgc2NvcmU9aW50KHNjb3JlKSwKICAgICAgICBwb3RlbnRpYWxfc2NvcmU9aW50KHBvdGVudGlhbF9zY29yZSksCiAgICAgICAgZ3JhZGU9Z3JhZGUsCiAgICAgICAgc3RhdHVzPXN0YXR1cywKICAgICAgICBlbmFibGVkX2VudGl0aWVzPWludChlbmFibGVkX2NvdW50KSwKICAgICAgICBkaXNhYmxlZF9lbnRpdGllc19pZ25vcmVkPWludChkaXNhYmxlZF9wcm9ibGVtX2VudGl0aWVzIG9yIGRpc2FibGVkX2VudGl0aWVzKSwKICAgICAgICBhZmZlY3RlZF9hY3RpdmVfZW50aXRpZXM9aW50KGFmZmVjdGVkX2NvdW50KSwKICAgICAgICBub3JtYWxpemVkX3BlbmFsdHk9aW50KG5vcm1hbGl6ZWRfcGVuYWx0eSksCiAgICAgICAgc2V2ZXJpdHlfcGVuYWx0eT1pbnQoc2V2ZXJpdHlfcGVuYWx0eSksCiAgICAgICAgcm9vdF9jYXVzZV9wZW5hbHR5PWludChyb290X2NhdXNlX3BlbmFsdHkpLAogICAgKQoKCmRlZiBhcHBseV9oZWFsdGhfc2NvcmVfdjIobW9kZWw6IEFueSwgZXhlY3V0aXZlOiBBbnksIGluY2lkZW50czogbGlzdFtBbnldKSAtPiBBbnk6CiAgICBicmVha2Rvd24gPSBjYWxjdWxhdGVfaGVhbHRoX3Njb3JlX3YyKG1vZGVsLCBpbmNpZGVudHMpCiAgICBkYXRhID0gYnJlYWtkb3duLmFzX2RpY3QoKQoKICAgIGlmIGlzaW5zdGFuY2UoZXhlY3V0aXZlLCBkaWN0KToKICAgICAgICBleGVjdXRpdmVbInNjb3JlIl0gPSBicmVha2Rvd24uc2NvcmUKICAgICAgICBleGVjdXRpdmVbInBvdGVudGlhbF9zY29yZSJdID0gYnJlYWtkb3duLnBvdGVudGlhbF9zY29yZQogICAgICAgIGV4ZWN1dGl2ZVsiaGVhbHRoX3Njb3JlX3YyIl0gPSBkYXRhCiAgICAgICAgZXhlY3V0aXZlWyJoZWFsdGhfZ3JhZGUiXSA9IGJyZWFrZG93bi5ncmFkZQogICAgICAgIGV4ZWN1dGl2ZVsiaGVhbHRoX3N0YXR1c192MiJdID0gYnJlYWtkb3duLnN0YXR1cwogICAgICAgIHJldHVybiBleGVjdXRpdmUKCiAgICB2YWx1ZXMgPSB7CiAgICAgICAgInNjb3JlIjogYnJlYWtkb3duLnNjb3JlLAogICAgICAgICJwb3RlbnRpYWxfc2NvcmUiOiBicmVha2Rvd24ucG90ZW50aWFsX3Njb3JlLAogICAgICAgICJoZWFsdGhfc2NvcmVfdjIiOiBkYXRhLAogICAgICAgICJoZWFsdGhfZ3JhZGUiOiBicmVha2Rvd24uZ3JhZGUsCiAgICAgICAgImhlYWx0aF9zdGF0dXNfdjIiOiBicmVha2Rvd24uc3RhdHVzLAogICAgfQoKICAgIGZvciBrZXksIHZhbHVlIGluIHZhbHVlcy5pdGVtcygpOgogICAgICAgIHRyeToKICAgICAgICAgICAgc2V0YXR0cihleGVjdXRpdmUsIGtleSwgdmFsdWUpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgcGFzcwoKICAgIHJldHVybiBleGVjdXRpdmUK").decode("utf-8")


def remove_old_block(text: str) -> str:
    marker = "# ---------------------------------------------------------------------------\n# Health Engine v2\n# ---------------------------------------------------------------------------"
    if marker in text:
        return text[: text.index(marker)].rstrip() + "\n"
    return text


def ensure_core_health() -> None:
    text = CORE_HEALTH.read_text(encoding="utf-8")
    text = remove_old_block(text)

    if "def apply_health_score_v2(" not in text:
        text = text.rstrip() + "\n\n" + HEALTH_APPEND.strip() + "\n"
    else:
        text = text.rstrip() + "\n\n" + HEALTH_APPEND.strip() + "\n"

    CORE_HEALTH.write_text(text, encoding="utf-8")


def ensure_import(text: str) -> str:
    text = text.replace("from src.hadocs.analysis.health_score_v2 import apply_health_score_v2\n", "")
    wanted = "from src.hadocs.core.health import apply_health_score_v2\n"
    if wanted in text:
        return text

    lines = text.splitlines(True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1
    lines.insert(insert_at, wanted)
    return "".join(lines)


def clean_generate_all(text: str) -> str:
    # Remove old duplicate score application lines regardless of indentation.
    text = re.sub(r"^[ \t]*executive\s*=\s*apply_health_score_v2\(model,\s*executive,\s*incidents\)\s*\n", "", text, flags=re.MULTILINE)

    marker = "generate_index(out, project_name, executive, incidents, now)"
    if marker not in text:
        raise RuntimeError("Could not find generate_index call in generator.py")

    text = text.replace(
        marker,
        "executive = apply_health_score_v2(model, executive, incidents)\n" + marker,
        1,
    )

    # Ensure key generate_all body calls are indented exactly one level when accidentally left at column 0.
    prefixes = (
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
        "write_explorer(",
        "export_knowledge(",
    )

    fixed = []
    for line in text.splitlines(True):
        stripped = line.lstrip()
        if line == stripped and stripped.startswith(prefixes):
            fixed.append("    " + line)
        else:
            fixed.append(line)

    return "".join(fixed)


def patch_dashboard(text: str) -> str:
    # Only touch Dashboard Engine v2 style function if present.
    if 'score = clamp(get(executive, "score", 0))' not in text:
        return text

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
          <p class="muted">Disabled entities are ignored and penalties are normalized for large installations.</p>
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

    return text


def patch_generator() -> None:
    text = GENERATOR.read_text(encoding="utf-8")
    text = ensure_import(text)
    text = clean_generate_all(text)
    text = patch_dashboard(text)
    GENERATOR.write_text(text, encoding="utf-8")


def neutralize_old_module() -> None:
    OLD_MODULE.parent.mkdir(parents=True, exist_ok=True)
    OLD_MODULE.write_text(
        '"""Compatibility wrapper for the old experimental Health Score v2 module."""\n\n'
        "from src.hadocs.core.health import apply_health_score_v2, calculate_health_score_v2, is_disabled_entity\n",
        encoding="utf-8",
    )


def main() -> None:
    if not CORE_HEALTH.exists() or not GENERATOR.exists():
        raise SystemExit("Run from repository root: C:\\HomeAssistantDocs")

    ensure_core_health()
    neutralize_old_module()
    patch_generator()

    print("Clean Health Engine v0.13 applied.")
    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("If green:")
    print("  git add src/hadocs/core/health.py src/hadocs/reports/generator.py src/hadocs/analysis/health_score_v2.py docs/V013_HEALTH_ENGINE_CLEAN.md tools/apply_v013_health_engine_clean.py")
    print('  git commit -m "Add clean Health Engine v2 scoring"')
    print("  git push")


if __name__ == "__main__":
    main()
