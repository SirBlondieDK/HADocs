from pathlib import Path
from datetime import datetime
from collections import Counter

from src.hadocs.advisor.engine import build_executive_summary
from src.hadocs.core.builder import build_model
from src.hadocs.core.health import (
    calculate_device_health,
    calculate_health_score,
    find_duplicate_names_by_domain,
    get_critical_entities,
)
from src.hadocs.core.history import compare_last_two, save_history_snapshot
from src.hadocs.core.recommendations import build_recommendations
from src.hadocs.core.relationships import (
    build_relationship_graph,
    top_problem_devices,
    top_problem_integrations,
)
from src.hadocs.exporters.csv_exporter import export_devices_csv, export_entities_csv
from src.hadocs.utils.text import slugify, write_md


def generate_all(data: dict, idx: dict, cfg: dict, log=print) -> None:
    out = Path(cfg.get("output_dir", "output"))
    out.mkdir(exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = cfg.get("project_name", "Home Assistant")

    model = build_model(data, idx)
    graph = build_relationship_graph(model)
    device_health = calculate_device_health(model)
    health_score, health_notes = calculate_health_score(model, device_health)
    recommendations = build_recommendations(model, device_health)
    executive = build_executive_summary(model, graph, device_health, recommendations, health_score)
    save_history_snapshot(cfg, model, health_score, executive)
    history_comparison = compare_last_two(cfg)

    generate_index(out, project_name, executive, now)
    generate_executive_dashboard(out, project_name, model, graph, executive, health_notes, history_comparison, now)
    generate_summary(out, model, graph, health_score, health_notes, now)
    generate_areas(out, model, now)
    generate_devices(out, model, now)
    generate_integrations(out, model, graph, now)
    generate_device_health(out, device_health, now)
    generate_recommendations(out, recommendations, now)
    generate_problems(out, model, now)
    generate_rules_report(out, model, now)
    generate_relationships(out, model, graph, now)
    generate_insights(out, executive, now)
    generate_maintenance(out, model, executive, now)
    generate_history(out, history_comparison, now)
    generate_architecture(out, now)
    export_entities_csv(out, model)
    export_devices_csv(out, model)

    log(f"Documentation complete: {out / 'index.md'}")


def status_icon(score: int) -> str:
    if score >= 85:
        return "🟢"
    if score >= 60:
        return "🟡"
    return "🔴"


def bar(score: int, width: int = 20) -> str:
    filled = round((score / 100) * width)
    return "█" * filled + "░" * (width - filled)


def generate_index(out: Path, project_name: str, executive, now: str) -> None:
    lines = [
        f"# {project_name} - HADocs",
        "",
        f"Generated: `{now}`",
        "",
        f"# {status_icon(executive.score)} {executive.status}",
        "",
        f"## Health Score: `{executive.score}/100`",
        "",
        f"`{bar(executive.score)}`",
        "",
        f"- Potential after recommended fixes: `{executive.potential_score}/100`",
        f"- Main cause: **{executive.main_cause}**",
        f"- Estimated repair time: `{executive.estimated_repair_minutes} minutes`",
        "",
        "## Start here",
        "",
        "- [00 Executive Dashboard](00_executive_dashboard.md)",
        "- [14 Insights](14_insights.md)",
        "- [15 Maintenance](15_maintenance.md)",
        "- [16 History](16_history.md)",
        "",
        "## Reports",
        "",
        "- [01 Overview](01_overview.md)",
        "- [02 Areas](02_areas/index.md)",
        "- [03 Devices](03_devices/index.md)",
        "- [04 Integrations](04_integrations.md)",
        "- [05 Device Health](05_device_health.md)",
        "- [06 Recommendations](06_recommendations.md)",
        "- [07 Problems and cleanup](07_problems.md)",
        "- [08 Rule Matches](08_rule_matches.md)",
        "- [09 Relationships](09_relationships.md)",
        "- [10 Entity Relationships](10_entity_relationships.md)",
        "- [11 Device Relationships](11_device_relationships.md)",
        "- [12 Integration Relationships](12_integration_relationships.md)",
        "- [13 Architecture](13_architecture.md)",
        "- [CSV entities](csv/entities.csv)",
        "- [CSV devices](csv/devices.csv)",
    ]
    write_md(out / "index.md", lines)


def generate_executive_dashboard(out, project_name, model, graph, executive, health_notes, history_comparison, now):
    physical_devices = [d for d in model.devices.values() if d.is_physical]
    virtual_devices = [d for d in model.devices.values() if d.is_virtual]
    system_devices = [d for d in model.devices.values() if d.is_system]

    lines = [
        f"# 00 Executive Dashboard",
        "",
        f"Generated: `{now}`",
        "",
        f"# {status_icon(executive.score)} {executive.status}",
        "",
        f"## Health Score: `{executive.score}/100`",
        "",
        f"`{bar(executive.score)}`",
        "",
        f"- Potential score after recommended fixes: `{executive.potential_score}/100`",
        f"- Estimated repair time: `{executive.estimated_repair_minutes} minutes`",
        f"- Main cause: **{executive.main_cause}**",
        "",
        "## Installation",
        "",
        f"- 🏠 Areas: `{len(model.areas)}`",
        f"- 💡 Physical devices: `{len(physical_devices)}`",
        f"- 🧩 Virtual devices: `{len(virtual_devices)}`",
        f"- ⚙️ System devices: `{len(system_devices)}`",
        f"- 🔌 Integrations: `{len(model.integrations)}`",
        f"- 📦 Entities: `{len(model.entities)}`",
        "",
        "## Problem summary",
        "",
        f"- 🔴 Critical actions: `{executive.critical_count}`",
        f"- 🟡 Warning actions: `{executive.warning_count}`",
        f"- 🧹 Maintenance actions: `{executive.maintenance_count}`",
        "",
    ]

    if history_comparison:
        health_delta = history_comparison["health_delta"]
        problem_delta = history_comparison["problem_entity_delta"]
        lines += [
            "## Since last scan",
            "",
            f"- Health change: `{health_delta:+}`",
            f"- Problem entity change: `{problem_delta:+}`",
            "",
        ]

    if health_notes:
        lines += ["## Score explanation", ""]
        for note in health_notes:
            lines.append(f"- {note}")
        lines.append("")

    if executive.insights:
        lines += ["## Key insights", ""]
        for insight in executive.insights[:5]:
            lines.append(f"- **{insight.title}** — {insight.message}")
        lines.append("")

    if executive.actions:
        lines += ["## Fix these first", ""]
        for action in executive.actions[:8]:
            stars = "★" * action.priority + "☆" * (5 - action.priority)
            lines.append(
                f"- `{stars}` **{action.title}** — {action.reason} "
                f"(`+{action.estimated_score_gain}` estimated)"
            )
        lines.append("")

    write_md(out / "00_executive_dashboard.md", lines)


def generate_summary(out, model, graph, health_score, health_notes, now):
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
        f"- Entity relationships: `{len(graph.entities)}`",
        f"- Device relationships: `{len(graph.devices)}`",
        f"- Integration relationships: `{len(graph.integrations)}`",
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
            f"- Entity count: `{len(device.entities)}`",
            "", "## Entities", "",
        ]
        for entity in sorted(device.entities, key=lambda e: e.entity_id):
            lines.append(f"- `{entity.entity_id}` — `{entity.state}` — `{entity.importance}` — {entity.rule_reason}")
        write_md(dev_dir / filename, lines)
    write_md(dev_dir / "index.md", index)


def generate_integrations(out, model, graph, now):
    integrations = []
    for integration in model.integrations.values():
        rel = graph.integrations.get(integration.platform)
        bad = rel.problem_entities if rel else []
        important = [e for e in integration.entities if e.importance == "important"]
        score = 100 if not important else max(0, 100 - min(60, len(bad) * 5))
        integrations.append((score, integration, rel, bad, important))

    lines = ["# 04 Integrations", "", f"Generated: {now}", ""]
    for score, integration, rel, bad, important in sorted(integrations, key=lambda x: x[0]):
        diagnostic = [e for e in integration.entities if e.importance == "diagnostic"]
        ignored = [e for e in integration.entities if e.is_ignored]
        lines += [
            f"## {integration.platform}", "",
            f"- Health: `{score}/100`",
            f"- Entities: `{len(integration.entities)}`",
            f"- Devices: `{len(integration.devices)}`",
            f"- Important: `{len(important)}`",
            f"- Diagnostic: `{len(diagnostic)}`",
            f"- Ignored: `{len(ignored)}`",
            f"- Relevant unknown/unavailable: `{len(bad)}`", "",
        ]
    write_md(out / "04_integrations.md", lines)


def generate_device_health(out, device_health, now):
    lines = ["# 05 Device Health", "", f"Generated: {now}", ""]
    for item in sorted(device_health, key=lambda d: (d.status, d.score, d.device.name)):
        stars = "★" * max(1, round(item.score / 20)) + "☆" * (5 - max(1, round(item.score / 20)))
        lines += [
            f"## {item.device.name}", "",
            f"- Health: `{stars}`",
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
    write_md(out / "05_device_health.md", lines)


def generate_recommendations(out, recommendations, now):
    lines = ["# 06 Recommendations", "", f"Generated: {now}", ""]
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
    write_md(out / "06_recommendations.md", lines)


def generate_problems(out, model, now):
    critical = get_critical_entities(model)
    duplicates = find_duplicate_names_by_domain(model)
    physical_without_area = [d for d in model.devices.values() if d.is_physical and (not d.area_id or d.area_id == "_uden_område")]
    ignored_bad = [e for e in model.entities.values() if e.is_ignored and e.state in ("unknown", "unavailable")]

    lines = ["# 07 Problems and cleanup", "", f"Generated: {now}", ""]
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
    write_md(out / "07_problems.md", lines)


def generate_rules_report(out, model, now):
    lines = ["# 08 Rule Matches", "", f"Generated: {now}", ""]
    counts = Counter((e.importance, e.rule_reason) for e in model.entities.values())
    for (importance, reason), count in sorted(counts.items(), key=lambda x: (-x[1], x[0][0])):
        lines.append(f"- `{importance}` — {reason}: `{count}`")
    write_md(out / "08_rule_matches.md", lines)


def generate_relationships(out, model, graph, now):
    lines = ["# 09 Relationships", "", f"Generated: {now}", ""]
    lines += [
        "## Relationship model", "",
        "```text",
        "Area",
        "  └── Device",
        "        └── Entity",
        "              └── Integration",
        "```", "",
        "This is Relationship Engine v1. Future versions will include automations, scripts, helpers, scenes, dashboards and voice assistants.",
        "",
        "## Top problem devices", "",
    ]
    for device in top_problem_devices(graph):
        lines.append(f"- **{device.name}** — `{len(device.problem_entities)}` relevant problem entities")

    lines += ["", "## Top problem integrations", ""]
    for integration in top_problem_integrations(graph):
        lines.append(f"- **{integration.platform}** — `{len(integration.problem_entities)}` relevant problem entities")

    write_md(out / "09_relationships.md", lines)

    entity_lines = ["# 10 Entity Relationships", "", f"Generated: {now}", ""]
    for rel in sorted(graph.entities.values(), key=lambda r: r.entity_id):
        if rel.is_ignored and rel.state not in ("unknown", "unavailable"):
            continue
        entity_lines += [
            f"## {rel.entity_id}", "",
            f"- Name: `{rel.name}`",
            f"- State: `{rel.state}`",
            f"- Domain: `{rel.domain}`",
            f"- Area ID: `{rel.area_id}`",
            f"- Device: `{rel.device_name}`",
            f"- Integration: `{rel.integration}`",
            f"- Importance: `{rel.importance}`",
            f"- Ignored: `{rel.is_ignored}`", "",
        ]
    write_md(out / "10_entity_relationships.md", entity_lines)

    device_lines = ["# 11 Device Relationships", "", f"Generated: {now}", ""]
    for rel in sorted(graph.devices.values(), key=lambda r: r.name):
        device_lines += [
            f"## {rel.name}", "",
            f"- Classification: `{rel.classification}`",
            f"- Area ID: `{rel.area_id}`",
            f"- Integrations: `{', '.join(rel.integrations)}`",
            f"- Important entities: `{len(rel.important_entities)}`",
            f"- Diagnostic entities: `{len(rel.diagnostic_entities)}`",
            f"- Ignored entities: `{len(rel.ignored_entities)}`",
            f"- Problem entities: `{len(rel.problem_entities)}`", "",
        ]
        if rel.problem_entities:
            device_lines.append("### Problems")
            device_lines.append("")
            for entity_id in rel.problem_entities:
                device_lines.append(f"- `{entity_id}`")
            device_lines.append("")
    write_md(out / "11_device_relationships.md", device_lines)

    integration_lines = ["# 12 Integration Relationships", "", f"Generated: {now}", ""]
    for rel in sorted(graph.integrations.values(), key=lambda r: r.platform):
        integration_lines += [
            f"## {rel.platform}", "",
            f"- Devices: `{len(rel.devices)}`",
            f"- Important entities: `{len(rel.important_entities)}`",
            f"- Diagnostic entities: `{len(rel.diagnostic_entities)}`",
            f"- Ignored entities: `{len(rel.ignored_entities)}`",
            f"- Problem entities: `{len(rel.problem_entities)}`", "",
        ]
    write_md(out / "12_integration_relationships.md", integration_lines)


def generate_insights(out, executive, now):
    lines = ["# 14 Insights", "", f"Generated: {now}", ""]
    for insight in executive.insights:
        lines += [
            f"## {insight.title}", "",
            f"- Severity: `{insight.severity}`",
            f"- Estimated score gain: `+{insight.estimated_score_gain}`",
            "",
            insight.message,
            "",
        ]
        if insight.related_items:
            lines += ["### Related", ""]
            for item in insight.related_items:
                lines.append(f"- `{item}`")
            lines.append("")
    write_md(out / "14_insights.md", lines)


def generate_maintenance(out, model, executive, now):
    lines = ["# 15 Maintenance", "", f"Generated: {now}", ""]
    lines += [
        "## Action plan", "",
        f"- Estimated repair time: `{executive.estimated_repair_minutes} minutes`",
        f"- Potential score: `{executive.potential_score}/100`",
        "",
    ]

    groups = {
        "Critical": [a for a in executive.actions if a.priority >= 5],
        "Warning": [a for a in executive.actions if a.priority == 4],
        "Cleanup": [a for a in executive.actions if a.priority <= 3],
    }

    for group, actions in groups.items():
        lines += [f"## {group}", ""]
        if not actions:
            lines.append("No actions.")
            lines.append("")
            continue
        for action in actions:
            stars = "★" * action.priority + "☆" * (5 - action.priority)
            lines += [
                f"### {action.title}",
                "",
                f"- Priority: `{stars}`",
                f"- Reason: {action.reason}",
                f"- Estimated score gain: `+{action.estimated_score_gain}`",
                "",
            ]

    write_md(out / "15_maintenance.md", lines)


def generate_history(out, history_comparison, now):
    lines = ["# 16 History", "", f"Generated: {now}", ""]
    if not history_comparison:
        lines.append("No previous scan available yet.")
    else:
        lines += [
            "## Since last scan", "",
            f"- Health change: `{history_comparison['health_delta']:+}`",
            f"- Problem entity change: `{history_comparison['problem_entity_delta']:+}`",
            f"- Critical action change: `{history_comparison['critical_delta']:+}`",
            f"- Warning action change: `{history_comparison['warning_delta']:+}`",
        ]
    write_md(out / "16_history.md", lines)


def generate_architecture(out, now):
    write_md(out / "13_architecture.md", [
        "# 13 Architecture", "", f"Generated: {now}", "",
        "```text",
        "Home Assistant API",
        "      │",
        "      ▼",
        "HADocs Core Model",
        "      │",
        "      ├── Rules Engine",
        "      ├── Advisor Engine",
        "      ├── Intelligence Engine",
        "      ├── Areas",
        "      ├── Physical Devices",
        "      ├── Virtual Devices",
        "      ├── System Devices",
        "      ├── Entities",
        "      ├── Integrations",
        "      ├── Health Model",
        "      └── Relationship Graph",
        "      │",
        "      ▼",
        "Reports / CSV / Future HTML / Future Full Relationship Engine",
        "```",
    ])
