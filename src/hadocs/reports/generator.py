from pathlib import Path
from datetime import datetime
from collections import Counter

from src.hadocs.advisor.engine import build_executive_summary_from_incidents
from src.hadocs.core.builder import build_model
from src.hadocs.core.health import (
    calculate_device_health,
    calculate_health_score,
    find_duplicate_names_by_domain,
    get_critical_entities,
)
from src.hadocs.core.history import (
    build_trend_summary,
    compare_last_two,
    export_history_summary,
    load_history,
    save_history_snapshot,
    sparkline,
)
from src.hadocs.core.incidents import (
    build_incidents,
    collapse_incidents,
    hidden_incident_count,
    visible_incidents,
)
from src.hadocs.core.relationships import build_relationship_graph
from src.hadocs.exporters.csv_exporter import export_devices_csv, export_entities_csv
from src.hadocs.utils.text import slugify, write_md
from src.hadocs.html.explorer import write_explorer
from src.hadocs.knowledge.exporter import export_knowledge
from src.hadocs.reports.html_hook import generate_html_dashboard


def generate_all(data: dict, idx: dict, cfg: dict, log=print) -> None:
    out = Path(cfg.get("output_dir", "output"))
    out.mkdir(exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = cfg.get("project_name", "Home Assistant")

    model = build_model(data, idx)
    graph = build_relationship_graph(model)
    device_health = calculate_device_health(model)
    health_score, health_notes = calculate_health_score(model, device_health)
    raw_incidents = build_incidents(model, graph)
    incidents = collapse_incidents(raw_incidents)
    executive = build_executive_summary_from_incidents(health_score, incidents)
    save_history_snapshot(cfg, model, health_score, executive, incidents=incidents, raw_incidents=raw_incidents)
    history_comparison = compare_last_two(cfg)
    history = load_history(cfg)
    trend_summary = build_trend_summary(history)
    export_history_summary(cfg)

    write_explorer(out, model, graph)

    export_knowledge(
        out,
        model=model,
        executive=executive,
        incidents=incidents,
        graph=graph,
        version="0.12.0",
    )

    export_knowledge(
        out,
        model=model,
        executive=executive,
        incidents=incidents,
        version="0.11.0",
    )

    generate_html_dashboard(
        out,
        project_name,
        model,
        executive,
        incidents,
        raw_incidents,
        history_comparison,
        now,
    )

    generate_index(out, project_name, executive, incidents, now)
    generate_executive_dashboard(out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now)
    generate_root_causes(out, incidents, now)
    generate_incidents(out, incidents, raw_incidents, now)
    generate_summary(out, model, graph, health_score, health_notes, incidents, raw_incidents, now)
    generate_areas(out, model, now)
    generate_devices(out, model, now)
    generate_integrations(out, model, graph, now)
    generate_device_health(out, device_health, now)
    generate_maintenance(out, executive, incidents, now)
    generate_problems(out, model, now)
    generate_rules_report(out, model, now)
    generate_relationships(out, graph, now)
    generate_insights(out, executive, incidents, now)
    generate_history(out, history_comparison, trend_summary, now)
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


def generate_index(out: Path, project_name: str, executive, incidents, now: str) -> None:
    hidden = hidden_incident_count(incidents)
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
        f"- Potential after top fixes: `{executive.potential_score}/100`",
        f"- Main root cause: **{executive.main_cause}**",
        f"- Estimated repair time: `{executive.estimated_repair_minutes} minutes`",
        f"- Visible root causes: `{len(visible_incidents(incidents))}`",
        f"- Hidden lower-priority incidents: `{hidden}`",
        "",
        "## Start here",
        "",
        "- [00 Executive Dashboard](00_executive_dashboard.md)",
        "- [01 Root Causes](01_root_causes.md)",
        "- [02 Incidents](02_incidents.md)",
        "- [14 Insights](14_insights.md)",
        "- [15 Maintenance](15_maintenance.md)",
        "- [16 History](16_history.md)",
        "",
        "## Reports",
        "",
        "- [03 Overview](03_overview.md)",
        "- [04 Areas](04_areas/index.md)",
        "- [05 Devices](05_devices/index.md)",
        "- [06 Integrations](06_integrations.md)",
        "- [07 Device Health](07_device_health.md)",
        "- [08 Problems and cleanup](08_problems.md)",
        "- [09 Rule Matches](09_rule_matches.md)",
        "- [10 Relationships](10_relationships.md)",
        "- [11 Entity Relationships](11_entity_relationships.md)",
        "- [12 Device Relationships](12_device_relationships.md)",
        "- [13 Integration Relationships](13_integration_relationships.md)",
        "- [17 Architecture](17_architecture.md)",
        "- [CSV entities](csv/entities.csv)",
        "- [CSV devices](csv/devices.csv)",
    ]
    write_md(out / "index.md", lines)


def generate_executive_dashboard(out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now):
    physical_devices = [d for d in model.devices.values() if d.is_physical]
    virtual_devices = [d for d in model.devices.values() if d.is_virtual]
    system_devices = [d for d in model.devices.values() if d.is_system]
    total_symptoms = sum(len(i.affected_entities) for i in incidents)
    hidden = hidden_incident_count(incidents)

    lines = [
        "# 00 Executive Dashboard",
        "",
        f"Generated: `{now}`",
        "",
        f"# {status_icon(executive.score)} {executive.status}",
        "",
        f"## Health Score: `{executive.score}/100`",
        "",
        f"`{bar(executive.score)}`",
        "",
        f"- Potential score after top fixes: `{executive.potential_score}/100`",
        f"- Estimated repair time: `{executive.estimated_repair_minutes} minutes`",
        f"- Main root cause: **{executive.main_cause}**",
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
        "## Root cause summary",
        "",
        f"- 🔥 Collapsed root causes: `{len(incidents)}`",
        f"- 🧩 Relevant affected entities: `{total_symptoms}`",
        f"- 🔴 Critical root causes: `{executive.critical_count}`",
        f"- 🟡 Warning root causes: `{executive.warning_count}`",
        f"- 🧹 Maintenance root causes: `{executive.maintenance_count}`",
        f"- 🗂 Hidden lower-priority incidents: `{hidden}`",
        f"- 🔁 Raw incidents collapsed: `{len(raw_incidents) - len(incidents)}`",
        "",
    ]

    shown = visible_incidents(incidents)
    if shown:
        lines += ["## Fix these first", ""]
        for incident in shown[:10]:
            stars = "★" * {"critical": 5, "warning": 4, "maintenance": 3}.get(incident.severity, 1)
            child_text = f", {incident.child_count} child incidents" if incident.child_count else ""
            lines.append(
                f"- `{stars}` **{incident.root_cause}** — {incident.title} "
                f"({len(incident.affected_entities)} affected, {len(incident.affected_devices)} devices{child_text}, "
                f"+{incident.estimated_score_gain}, ~{incident.estimated_repair_minutes} min)"
            )
        lines.append("")

    if history_comparison:
        lines += [
            "## Since last scan",
            "",
            f"- Health change: `{history_comparison['health_delta']:+}`",
            f"- Problem entity change: `{history_comparison['problem_entity_delta']:+}`",
            f"- New root causes: `{len(history_comparison.get('new_root_causes', []))}`",
            f"- Resolved root causes: `{len(history_comparison.get('resolved_root_causes', []))}`",
            "",
        ]

    if trend_summary and trend_summary.get("scan_count", 0):
        health_values = [point.get("value", 0) for point in trend_summary.get("health_points", [])]
        problem_values = [point.get("value", 0) for point in trend_summary.get("problem_entity_points", [])]
        lines += [
            "## History trend",
            "",
            f"- Scans stored: `{trend_summary.get('scan_count', 0)}`",
            f"- Best Health Score: `{trend_summary.get('best_health')}`",
            f"- Worst Health Score: `{trend_summary.get('worst_health')}`",
            f"- Total Health change: `{trend_summary.get('health_change_total', 0):+}`",
            f"- Health trend: `{sparkline(health_values)}`",
            f"- Problem trend: `{sparkline(problem_values)}`",
            "",
        ]

    if executive.insights:
        lines += ["## Key insights", ""]
        for insight in executive.insights[:5]:
            lines.append(f"- **{insight.title}** — {insight.message}")
        lines.append("")

    if health_notes:
        lines += ["## Score explanation", ""]
        for note in health_notes:
            lines.append(f"- {note}")
        lines.append("")

    write_md(out / "00_executive_dashboard.md", lines)


def generate_root_causes(out, incidents, now):
    lines = ["# 01 Root Causes", "", f"Generated: {now}", ""]
    if not incidents:
        lines.append("No root causes detected.")

    for incident in incidents:
        lines += [
            f"## {incident.root_cause}",
            "",
            f"- Title: {incident.title}",
            f"- Category: `{incident.category}`",
            f"- Severity: `{incident.severity}`",
            f"- Affected entities: `{len(incident.affected_entities)}`",
            f"- Affected devices: `{len(incident.affected_devices)}`",
            f"- Child incidents: `{incident.child_count}`",
            f"- Affected integrations: `{', '.join(incident.affected_integrations)}`",
            f"- Estimated score gain: `+{incident.estimated_score_gain}`",
            f"- Estimated repair time: `{incident.estimated_repair_minutes} minutes`",
            "",
            "### Recommendation",
            "",
            incident.recommendation,
            "",
        ]

        if incident.child_incidents:
            lines += ["### Child incidents", ""]
            for child in incident.child_incidents:
                lines.append(f"- **{child.root_cause}** — {len(child.affected_entities)} affected entities")
            lines.append("")

        if incident.affected_devices:
            lines += ["### Affected devices", ""]
            for item in incident.affected_devices[:20]:
                lines.append(f"- `{item}`")
            lines.append("")

    write_md(out / "01_root_causes.md", lines)


def generate_incidents(out, incidents, raw_incidents, now):
    lines = ["# 02 Incidents", "", f"Generated: {now}", ""]
    lines += [
        f"- Collapsed incidents: `{len(incidents)}`",
        f"- Raw incidents: `{len(raw_incidents)}`",
        f"- Raw incidents hidden/collapsed: `{len(raw_incidents) - len(incidents)}`",
        "",
    ]

    if not incidents:
        lines.append("No incidents detected.")

    for incident in incidents:
        lines += [
            f"## {incident.title}",
            "",
            f"- Incident ID: `{incident.incident_id}`",
            f"- Root cause: `{incident.root_cause}`",
            f"- Severity: `{incident.severity}`",
            f"- Category: `{incident.category}`",
            f"- Child incidents: `{incident.child_count}`",
            f"- Estimated score gain: `+{incident.estimated_score_gain}`",
            f"- Estimated repair time: `{incident.estimated_repair_minutes} minutes`",
            "",
        ]

        if incident.child_incidents:
            lines += ["### Child incidents", ""]
            for child in incident.child_incidents:
                lines.append(f"- `{child.root_cause}` — {len(child.affected_entities)} affected entities")
            lines.append("")

        lines += ["### Affected entities", ""]
        for entity_id in incident.affected_entities[:50]:
            lines.append(f"- `{entity_id}`")
        if len(incident.affected_entities) > 50:
            lines.append(f"- ...and {len(incident.affected_entities) - 50} more")
        lines.append("")

    write_md(out / "02_incidents.md", lines)


def generate_summary(out, model, graph, health_score, health_notes, incidents, raw_incidents, now):
    physical_devices = [d for d in model.devices.values() if d.is_physical]
    ignored_entities = [e for e in model.entities.values() if e.is_ignored]
    diagnostic_entities = [e for e in model.entities.values() if e.importance == "diagnostic"]
    important_entities = [e for e in model.entities.values() if e.importance == "important"]

    lines = [
        "# 03 Overview", "", f"Generated: {now}", "",
        f"## Health Score: `{health_score}/100`", "",
    ]
    for note in health_notes or ["No major problems found."]:
        lines.append(f"- {note}")

    lines += [
        "", "## Core model", "",
        f"- Areas: `{len(model.areas)}`",
        f"- Devices: `{len(model.devices)}`",
        f"- Physical devices: `{len(physical_devices)}`",
        f"- Entities: `{len(model.entities)}`",
        f"- Important entities: `{len(important_entities)}`",
        f"- Diagnostic entities: `{len(diagnostic_entities)}`",
        f"- Ignored entities: `{len(ignored_entities)}`",
        f"- Integrations: `{len(model.integrations)}`",
        f"- Collapsed incidents: `{len(incidents)}`",
        f"- Raw incidents: `{len(raw_incidents)}`",
        f"- Entity relationships: `{len(graph.entities)}`",
        f"- Device relationships: `{len(graph.devices)}`",
        f"- Integration relationships: `{len(graph.integrations)}`",
    ]
    write_md(out / "03_overview.md", lines)


def generate_areas(out, model, now):
    area_dir = out / "04_areas"
    index = ["# 04 Areas", "", f"Generated: {now}", ""]
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
    dev_dir = out / "05_devices"
    index = ["# 05 Devices", "", f"Generated: {now}", ""]
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

    lines = ["# 06 Integrations", "", f"Generated: {now}", ""]
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
    write_md(out / "06_integrations.md", lines)


def generate_device_health(out, device_health, now):
    lines = ["# 07 Device Health", "", f"Generated: {now}", ""]
    for item in sorted(device_health, key=lambda d: (d.status, d.score, d.device.name)):
        stars_count = max(1, min(5, round(item.score / 20)))
        stars = "★" * stars_count + "☆" * (5 - stars_count)
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
    write_md(out / "07_device_health.md", lines)


def generate_maintenance(out, executive, incidents, now):
    lines = ["# 15 Maintenance", "", f"Generated: {now}", ""]
    lines += [
        "## Action plan", "",
        f"- Estimated repair time: `{executive.estimated_repair_minutes} minutes`",
        f"- Potential score: `{executive.potential_score}/100`",
        "",
    ]

    groups = {
        "Critical": [i for i in incidents if i.severity == "critical"],
        "Warning": [i for i in incidents if i.severity == "warning"],
        "Cleanup": [i for i in incidents if i.severity == "maintenance"],
    }

    for group, group_incidents in groups.items():
        lines += [f"## {group}", ""]
        if not group_incidents:
            lines.append("No actions.")
            lines.append("")
            continue
        for incident in group_incidents[:20]:
            stars = "★" * {"critical": 5, "warning": 4, "maintenance": 3}.get(incident.severity, 1)
            lines += [
                f"### {incident.title}",
                "",
                f"- Priority: `{stars}`",
                f"- Root cause: `{incident.root_cause}`",
                f"- Affected entities: `{len(incident.affected_entities)}`",
                f"- Affected devices: `{len(incident.affected_devices)}`",
                f"- Child incidents: `{incident.child_count}`",
                f"- Estimated score gain: `+{incident.estimated_score_gain}`",
                f"- Estimated repair time: `{incident.estimated_repair_minutes} minutes`",
                "",
                incident.recommendation,
                "",
            ]

    write_md(out / "15_maintenance.md", lines)


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


def generate_relationships(out, graph, now):
    write_md(out / "10_relationships.md", [
        "# 10 Relationships", "", f"Generated: {now}", "",
        "```text",
        "Area",
        "  └── Device",
        "        └── Entity",
        "              └── Integration",
        "```",
    ])

    entity_lines = ["# 11 Entity Relationships", "", f"Generated: {now}", ""]
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
    write_md(out / "11_entity_relationships.md", entity_lines)

    device_lines = ["# 12 Device Relationships", "", f"Generated: {now}", ""]
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
    write_md(out / "12_device_relationships.md", device_lines)

    integration_lines = ["# 13 Integration Relationships", "", f"Generated: {now}", ""]
    for rel in sorted(graph.integrations.values(), key=lambda r: r.platform):
        integration_lines += [
            f"## {rel.platform}", "",
            f"- Devices: `{len(rel.devices)}`",
            f"- Important entities: `{len(rel.important_entities)}`",
            f"- Diagnostic entities: `{len(rel.diagnostic_entities)}`",
            f"- Ignored entities: `{len(rel.ignored_entities)}`",
            f"- Problem entities: `{len(rel.problem_entities)}`", "",
        ]
    write_md(out / "13_integration_relationships.md", integration_lines)


def generate_insights(out, executive, incidents, now):
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


def generate_history(out, history_comparison, trend_summary, now):
    lines = ["# 16 History", "", f"Generated: {now}", ""]

    if not trend_summary or not trend_summary.get("scan_count"):
        lines.append("No history snapshots available yet.")
        write_md(out / "16_history.md", lines)
        return

    health_values = [point.get("value", 0) for point in trend_summary.get("health_points", [])]
    problem_values = [point.get("value", 0) for point in trend_summary.get("problem_entity_points", [])]
    latest = trend_summary.get("latest") or {}

    lines += [
        "## Trend summary",
        "",
        f"- Stored scans: `{trend_summary.get('scan_count', 0)}`",
        f"- Latest Health Score: `{latest.get('health_score')}`",
        f"- Best Health Score: `{trend_summary.get('best_health')}`",
        f"- Worst Health Score: `{trend_summary.get('worst_health')}`",
        f"- Total Health change: `{trend_summary.get('health_change_total', 0):+}`",
        f"- Health trend: `{sparkline(health_values)}`",
        f"- Problem entity trend: `{sparkline(problem_values)}`",
        "",
    ]

    if history_comparison:
        lines += [
            "## Since last scan", "",
            f"- Health change: `{history_comparison['health_delta']:+}`",
            f"- Potential score change: `{history_comparison['potential_delta']:+}`",
            f"- Problem entity change: `{history_comparison['problem_entity_delta']:+}`",
            f"- Critical action change: `{history_comparison['critical_delta']:+}`",
            f"- Warning action change: `{history_comparison['warning_delta']:+}`",
            f"- Maintenance action change: `{history_comparison['maintenance_delta']:+}`",
            "",
        ]

        new_causes = history_comparison.get("new_root_causes", [])
        resolved_causes = history_comparison.get("resolved_root_causes", [])

        if new_causes:
            lines += ["### New root causes", ""]
            for cause in new_causes[:20]:
                lines.append(f"- `{cause}`")
            lines.append("")

        if resolved_causes:
            lines += ["### Resolved root causes", ""]
            for cause in resolved_causes[:20]:
                lines.append(f"- `{cause}`")
            lines.append("")
    else:
        lines += ["## Since last scan", "", "No previous scan available yet.", ""]

    lines += [
        "## Latest root causes", "",
    ]
    for cause in latest.get("root_causes", [])[:15]:
        lines.append(
            f"- **{cause.get('key')}** — `{cause.get('severity')}` — "
            f"{cause.get('affected_entities')} affected entities, "
            f"+{cause.get('estimated_score_gain')} score, "
            f"~{cause.get('estimated_repair_minutes')} min"
        )

    write_md(out / "16_history.md", lines)


def generate_architecture(out, now):
    write_md(out / "17_architecture.md", [
        "# 17 Architecture", "", f"Generated: {now}", "",
        "```text",
        "Home Assistant API",
        "      │",
        "      ▼",
        "HADocs Core Model",
        "      │",
        "      ├── Rules Engine",
        "      ├── Advisor Engine",
        "      ├── Smart Home Intelligence Engine",
        "      ├── Incident Collapse Engine",
        "      ├── Health Model",
        "      └── Relationship Graph",
        "      │",
        "      ▼",
        "Reports / CSV / Future HTML / Future Full Relationship Engine",
        "```",
    ])
