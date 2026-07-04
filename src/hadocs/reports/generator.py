from pathlib import Path
from datetime import datetime
from collections import Counter

from src.hadocs.core.builder import build_model
from src.hadocs.core.health import (
    calculate_device_health,
    calculate_health_score,
    find_duplicate_names_by_domain,
    get_critical_entities,
)
from src.hadocs.core.recommendations import build_recommendations
from src.hadocs.exporters.csv_exporter import export_devices_csv, export_entities_csv
from src.hadocs.utils.text import slugify, write_md


def generate_all(data: dict, idx: dict, cfg: dict, log=print) -> None:
    out = Path(cfg.get("output_dir", "output"))
    out.mkdir(exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = cfg.get("project_name", "Home Assistant")

    model = build_model(data, idx)
    device_health = calculate_device_health(model)
    health_score, health_notes = calculate_health_score(model, device_health)
    recommendations = build_recommendations(model, device_health)

    generate_index(out, project_name, now, health_score)
    generate_summary(out, model, health_score, health_notes, now)
    generate_areas(out, model, now)
    generate_devices(out, model, now)
    generate_integrations(out, model, now)
    generate_integration_health(out, model, now)
    generate_device_health(out, device_health, now)
    generate_recommendations(out, recommendations, now)
    generate_problems(out, model, now)
    generate_rules_report(out, model, now)
    generate_dashboard_whitelist(out, model, now)
    generate_architecture(out, now)
    export_entities_csv(out, model)
    export_devices_csv(out, model)

    log(f"Documentation complete: {out / 'index.md'}")


def generate_index(out: Path, project_name: str, now: str, health_score: int) -> None:
    write_md(out / "index.md", [
        f"# {project_name} - Documentation",
        "",
        f"Generated: {now}",
        "",
        f"## Health Score: `{health_score}/100`",
        "",
        "## Reports",
        "",
        "- [01 Overview](01_overview.md)",
        "- [02 Areas](02_areas/index.md)",
        "- [03 Devices](03_devices/index.md)",
        "- [04 Integrations](04_integrations.md)",
        "- [05 Integration Health](05_integration_health.md)",
        "- [06 Device Health](06_device_health.md)",
        "- [07 Recommendations](07_recommendations.md)",
        "- [08 Problems and cleanup](08_problems.md)",
        "- [09 Rule Matches](09_rule_matches.md)",
        "- [10 Dashboard whitelist](10_dashboard_whitelist.md)",
        "- [11 Architecture](11_architecture.md)",
        "- [CSV entities](csv/entities.csv)",
        "- [CSV devices](csv/devices.csv)",
    ])


def generate_summary(out, model, health_score, health_notes, now):
    physical_devices = [d for d in model.devices.values() if d.is_physical]
    virtual_devices = [d for d in model.devices.values() if d.is_virtual]
    system_devices = [d for d in model.devices.values() if d.is_system]
    ignored_entities = [e for e in model.entities.values() if e.is_ignored]
    bad_ignored = [e for e in ignored_entities if e.state in ("unknown", "unavailable")]
    important_entities = [e for e in model.entities.values() if e.importance == "important"]
    diagnostic_entities = [e for e in model.entities.values() if e.importance == "diagnostic"]

    lines = [
        "# 01 Overview", "", f"Generated: {now}", "",
        f"## Health Score: `{health_score}/100`", "",
    ]
    for note in health_notes or ["No major problems found."]:
        lines.append(f"- {note}")

    lines += [
        "", "## Core model", "",
        f"- Areas: `{len(model.areas)}`",
        f"- Devices: `{len(model.devices)}`",
        f"- Physical devices: `{len(physical_devices)}`",
        f"- Virtual devices: `{len(virtual_devices)}`",
        f"- System devices: `{len(system_devices)}`",
        f"- Entities: `{len(model.entities)}`",
        f"- Important entities: `{len(important_entities)}`",
        f"- Diagnostic entities: `{len(diagnostic_entities)}`",
        f"- Ignored entities: `{len(ignored_entities)}`",
        f"- Ignored unknown/unavailable entities: `{len(bad_ignored)}`",
        f"- Integrations: `{len(model.integrations)}`",
    ]
    write_md(out / "01_overview.md", lines)


def generate_areas(out, model, now):
    area_dir = out / "02_areas"
    index = ["# 02 Areas", "", f"Generated: {now}", ""]
    for area in sorted(model.areas.values(), key=lambda a: a.name):
        filename = f"{slugify(area.name)}.md"
        index.append(f"- [{area.name}]({filename}) — {len(area.devices)} devices, {len(area.entities)} entities")
        lines = [f"# {area.name}", "", f"Generated: {now}", "", "## Devices", ""]
        for device in sorted(area.devices, key=lambda d: d.name):
            lines.append(f"- **{device.name}** — `{device.classification}` — {len(device.entities)} entities")
        lines += ["", "## Important entities", ""]
        for entity in sorted([e for e in area.entities if e.importance == "important"], key=lambda e: e.entity_id):
            lines.append(f"- **{entity.name}** — `{entity.entity_id}` — `{entity.state}`")
        write_md(area_dir / filename, lines)
    write_md(area_dir / "index.md", index)


def generate_devices(out, model, now):
    dev_dir = out / "03_devices"
    index = ["# 03 Devices", "", f"Generated: {now}", ""]
    for device in sorted(model.devices.values(), key=lambda d: (d.classification, d.name)):
        filename = f"{slugify(device.classification)}__{slugify(device.name)}.md"
        index.append(f"- [{device.name}]({filename}) — `{device.classification}`")
        lines = [
            f"# {device.name}", "", f"Generated: {now}", "",
            f"- Classification: `{device.classification}`",
            f"- Area ID: `{device.area_id}`",
            f"- Manufacturer: `{device.manufacturer}`",
            f"- Model: `{device.model}`",
            f"- Software: `{device.sw_version}`",
            f"- Hardware: `{device.hw_version}`",
            f"- Entity count: `{len(device.entities)}`",
            "", "## Entities", "",
        ]
        for entity in sorted(device.entities, key=lambda e: e.entity_id):
            lines.append(
                f"- `{entity.entity_id}` — `{entity.state}` — `{entity.importance}` — {entity.rule_reason}"
            )
        write_md(dev_dir / filename, lines)
    write_md(dev_dir / "index.md", index)


def generate_integrations(out, model, now):
    lines = ["# 04 Integrations", "", f"Generated: {now}", ""]
    for integration in sorted(model.integrations.values(), key=lambda i: i.platform):
        important = [e for e in integration.entities if e.importance == "important"]
        diagnostic = [e for e in integration.entities if e.importance == "diagnostic"]
        ignored = [e for e in integration.entities if e.is_ignored]
        bad = [e for e in integration.entities if e.state in ("unknown", "unavailable") and not e.is_ignored]
        lines += [
            f"## {integration.platform}", "",
            f"- Entities: `{len(integration.entities)}`",
            f"- Devices: `{len(integration.devices)}`",
            f"- Important: `{len(important)}`",
            f"- Diagnostic: `{len(diagnostic)}`",
            f"- Ignored: `{len(ignored)}`",
            f"- Relevant unknown/unavailable: `{len(bad)}`", "",
        ]
    write_md(out / "04_integrations.md", lines)


def generate_integration_health(out, model, now):
    lines = ["# 05 Integration Health", "", f"Generated: {now}", ""]
    for integration in sorted(model.integrations.values(), key=lambda i: i.platform):
        relevant = [e for e in integration.entities if not e.is_ignored and e.importance != "diagnostic"]
        bad = [e for e in relevant if e.state in ("unknown", "unavailable")]
        score = 100 if not relevant else max(0, 100 - min(60, len(bad) * 5))
        lines += [
            f"## {integration.platform}", "",
            f"- Score: `{score}/100`",
            f"- Relevant entities: `{len(relevant)}`",
            f"- Relevant unknown/unavailable: `{len(bad)}`", "",
        ]
    write_md(out / "05_integration_health.md", lines)


def generate_device_health(out, device_health, now):
    lines = ["# 06 Device Health", "", f"Generated: {now}", ""]
    for item in sorted(device_health, key=lambda d: (d.status, d.score, d.device.name)):
        lines += [
            f"## {item.device.name}", "",
            f"- Status: `{item.status}`",
            f"- Score: `{item.score}/100`",
            f"- Area ID: `{item.device.area_id}`",
            f"- Entity count: `{len(item.device.entities)}`", "",
        ]
        if item.reasons:
            lines.append("### Reasons")
            lines.append("")
            for reason in item.reasons:
                lines.append(f"- {reason}")
            lines.append("")
    write_md(out / "06_device_health.md", lines)


def generate_recommendations(out, recommendations, now):
    lines = ["# 07 Recommendations", "", f"Generated: {now}", ""]
    if not recommendations:
        lines.append("No recommendations found.")
    for rec in recommendations:
        stars = "★" * rec["priority"] + "☆" * (5 - rec["priority"])
        lines += [
            f"## {rec['title']}", "",
            f"- Priority: `{stars}`",
            f"- Reason: {rec['reason']}",
            f"- Estimated score gain: `+{rec['estimated_score_gain']}`", "",
        ]
    write_md(out / "07_recommendations.md", lines)


def generate_problems(out, model, now):
    critical = get_critical_entities(model)
    duplicates = find_duplicate_names_by_domain(model)
    physical_without_area = [d for d in model.devices.values() if d.is_physical and (not d.area_id or d.area_id == "_uden_område")]
    ignored_bad = [e for e in model.entities.values() if e.is_ignored and e.state in ("unknown", "unavailable")]

    lines = ["# 08 Problems and cleanup", "", f"Generated: {now}", ""]
    lines += ["## Critical entities", ""]
    for entity in critical:
        lines.append(f"- `{entity.entity_id}` — `{entity.state}`")
    lines += ["", "## Physical devices without area", ""]
    for device in sorted(physical_without_area, key=lambda d: d.name):
        lines.append(f"- **{device.name}** — `{device.manufacturer}` `{device.model}`")
    lines += ["", "## Duplicate names within same domain", ""]
    for (domain, name), ids in sorted(duplicates.items()):
        lines.append(f"- **{domain}: {name}**")
        for entity_id in ids:
            lines.append(f"  - `{entity_id}`")
    lines += ["", "## Ignored unknown/unavailable", ""]
    for entity in sorted(ignored_bad, key=lambda e: e.entity_id):
        lines.append(f"- `{entity.entity_id}` — `{entity.state}` — `{entity.rule_reason}`")
    write_md(out / "08_problems.md", lines)


def generate_rules_report(out, model, now):
    lines = ["# 09 Rule Matches", "", f"Generated: {now}", ""]
    counts = Counter((e.importance, e.rule_reason) for e in model.entities.values())
    for (importance, reason), count in sorted(counts.items(), key=lambda x: (-x[1], x[0][0])):
        lines.append(f"- `{importance}` — {reason}: `{count}`")
    write_md(out / "09_rule_matches.md", lines)


def generate_dashboard_whitelist(out, model, now):
    lines = ["# 10 Dashboard whitelist", "", f"Generated: {now}", ""]
    for area in sorted(model.areas.values(), key=lambda a: a.name):
        candidates = [e for e in area.entities if e.importance == "important" and not e.is_ignored]
        if not candidates:
            continue
        lines += [f"## {area.name}", ""]
        for entity in sorted(candidates, key=lambda e: e.entity_id):
            lines.append(f"- **{entity.name}** — `{entity.entity_id}` — `{entity.state}`")
        lines.append("")
    write_md(out / "10_dashboard_whitelist.md", lines)


def generate_architecture(out, now):
    write_md(out / "11_architecture.md", [
        "# 11 Architecture", "", f"Generated: {now}", "",
        "```text",
        "Home Assistant API",
        "      │",
        "      ▼",
        "HADocs Core Model",
        "      │",
        "      ├── Rules Engine",
        "      ├── Areas",
        "      ├── Physical Devices",
        "      ├── Virtual Devices",
        "      ├── System Devices",
        "      ├── Entities",
        "      ├── Integrations",
        "      └── Health Model",
        "      │",
        "      ▼",
        "Reports / CSV / Future HTML / Future Relationship Engine",
        "```",
    ])
