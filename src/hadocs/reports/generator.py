from pathlib import Path
from datetime import datetime

from src.hadocs.analyzers.core import analyze
from src.hadocs.analyzers.health import calculate_health_score
from src.hadocs.analyzers.helpers import (
    area_name,
    device_name,
    entity_area,
    friendly_name,
    state_for,
)
from src.hadocs.exporters.csv_exporter import export_entities_csv
from src.hadocs.utils.text import safe, slugify, write_md


def generate_all(data: dict, idx: dict, cfg: dict, log=print) -> None:
    out = Path(cfg.get("output_dir", "output"))
    out.mkdir(exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = cfg.get("project_name", "Home Assistant")
    analysis = analyze(data, idx)
    health_score, health_notes = calculate_health_score(analysis)

    generate_index(out, project_name, now, health_score)
    generate_summary(out, data, idx, analysis, health_score, health_notes, now)
    generate_areas(out, data, idx, now)
    generate_devices(out, data, idx, now)
    generate_integrations(out, data, idx, analysis, now)
    generate_server(out, idx, analysis, now)
    generate_network(out, data, idx, now)
    generate_problems(out, data, idx, analysis, now)
    generate_dashboard(out, idx, analysis, now)
    generate_battery(out, idx, analysis, now)
    generate_architecture(out, idx, analysis, now)
    export_entities_csv(out, data, idx)

    log(f"Dokumentation færdig: {out / 'index.md'}")


def generate_index(out: Path, project_name: str, now: str, health_score: int) -> None:
    write_md(out / "index.md", [
        f"# {project_name} - Dokumentation",
        "",
        f"Genereret: {now}",
        "",
        f"## Health Score: `{health_score}/100`",
        "",
        "## Rapporter",
        "",
        "- [01 Oversigt](01_oversigt.md)",
        "- [02 Rum](02_rum/index.md)",
        "- [03 Enheder](03_enheder/index.md)",
        "- [04 Integrationer](04_integrationer.md)",
        "- [05 Serverrum](05_serverrum.md)",
        "- [06 Netværk](06_netvaerk.md)",
        "- [07 Problemer og oprydning](07_problemer.md)",
        "- [08 Dashboard whitelist](08_dashboard_whitelist.md)",
        "- [09 Batterier](09_batterier.md)",
        "- [10 Arkitektur](10_arkitektur.md)",
        "- [CSV data](csv/entities.csv)",
    ])


def generate_summary(out, data, idx, a, health_score, health_notes, now):
    lines = [
        "# 01 Oversigt",
        "",
        f"Genereret: {now}",
        "",
        f"## Health Score: `{health_score}/100`",
        "",
    ]

    if health_notes:
        for note in health_notes:
            lines.append(f"- {note}")
    else:
        lines.append("- Ingen store problemer fundet.")

    lines += [
        "",
        "## System",
        "",
        f"- Home Assistant version: `{data['config'].get('version', '')}`",
        f"- Lokation: `{data['config'].get('location_name', '')}`",
        f"- Timezone: `{data['config'].get('time_zone', '')}`",
        f"- States: `{a['counts']['states']}`",
        f"- Entiteter: `{a['counts']['entities']}`",
        f"- Enheder: `{a['counts']['devices']}`",
        f"- Rum: `{a['counts']['areas']}`",
        f"- Unknown: `{a['counts']['unknown']}`",
        f"- Unavailable: `{a['counts']['unavailable']}`",
        "",
        "## Domæner",
        "",
    ]

    for domain, count in sorted(a["domain_counts"].items()):
        lines.append(f"- `{domain}`: {count}")

    lines += ["", "## Platforme", ""]
    for platform, count in sorted(a["platform_counts"].items()):
        lines.append(f"- `{platform}`: {count}")

    write_md(out / "01_oversigt.md", lines)


def generate_areas(out, data, idx, now):
    area_dir = out / "02_rum"
    index = ["# 02 Rum", "", f"Genereret: {now}", ""]

    for area_id, ents in sorted(idx["entities_by_area"].items(), key=lambda x: area_name(x[0], idx)):
        name = area_name(area_id, idx)
        filename = f"{slugify(name)}.md"
        index.append(f"- [{name}]({filename}) — {len(ents)} entiteter")

        lines = [f"# {name}", "", f"Genereret: {now}", ""]
        by_domain = {}

        for ent in ents:
            by_domain.setdefault(ent["entity_id"].split(".")[0], []).append(ent)

        for domain in sorted(by_domain):
            lines += [f"## {domain}", ""]
            for ent in sorted(by_domain[domain], key=lambda e: e["entity_id"]):
                st = state_for(ent["entity_id"], idx)
                lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{st.get('state', 'unknown')}`")
            lines.append("")

        write_md(area_dir / filename, lines)

    write_md(area_dir / "index.md", index)


def generate_devices(out, data, idx, now):
    dev_dir = out / "03_enheder"
    index = ["# 03 Enheder", "", f"Genereret: {now}", ""]

    for dev in sorted(data["devices"], key=lambda d: (area_name(d.get("area_id"), idx), device_name(d))):
        name = device_name(dev)
        filename = f"{slugify(area_name(dev.get('area_id'), idx))}__{slugify(name)}.md"
        index.append(f"- [{name}]({filename}) — {area_name(dev.get('area_id'), idx)}")

        lines = [
            f"# {name}",
            "",
            f"Genereret: {now}",
            "",
            f"- Area: `{area_name(dev.get('area_id'), idx)}`",
            f"- Manufacturer: `{safe(dev.get('manufacturer'))}`",
            f"- Model: `{safe(dev.get('model'))}`",
            f"- Hardware: `{safe(dev.get('hw_version'))}`",
            f"- Software: `{safe(dev.get('sw_version'))}`",
            f"- Device ID: `{dev.get('id')}`",
        ]

        if dev.get("configuration_url"):
            lines.append(f"- Configuration URL: `{dev.get('configuration_url')}`")

        lines += ["", "## Entiteter", ""]
        for ent in sorted(idx["entities_by_device"].get(dev["id"], []), key=lambda e: e["entity_id"]):
            st = state_for(ent["entity_id"], idx)
            lines.append(f"- `{ent['entity_id']}` — `{st.get('state', 'unknown')}`")

        write_md(dev_dir / filename, lines)

    write_md(dev_dir / "index.md", index)


def generate_integrations(out, data, idx, a, now):
    lines = ["# 04 Integrationer", "", f"Genereret: {now}", ""]
    for platform, ents in sorted(idx["entities_by_platform"].items()):
        states = [state_for(e["entity_id"], idx).get("state", "unknown") for e in ents]
        bad = sum(1 for s in states if s in ("unknown", "unavailable"))
        lines += [f"## {platform}", "", f"- Antal: `{len(ents)}`", f"- Unknown/unavailable: `{bad}`", ""]
        for ent in sorted(ents, key=lambda e: e["entity_id"]):
            st = state_for(ent["entity_id"], idx)
            lines.append(f"- `{ent['entity_id']}` — `{st.get('state', 'unknown')}`")
        lines.append("")
    write_md(out / "04_integrationer.md", lines)


def generate_server(out, idx, a, now):
    lines = ["# 05 Serverrum", "", f"Genereret: {now}", ""]
    for ent in sorted(a["server_entities"], key=lambda e: e["entity_id"]):
        st = state_for(ent["entity_id"], idx)
        lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{st.get('state', 'unknown')}`")
    write_md(out / "05_serverrum.md", lines)


def generate_network(out, data, idx, now):
    words = ["deco", "wifi", "wlan", "internet", "rssi", "linkquality", "device_tracker", "adguard", "dns", "remote_ui"]
    lines = ["# 06 Netværk", "", f"Genereret: {now}", ""]
    for ent in sorted(data["entities"], key=lambda e: e["entity_id"]):
        eid = ent["entity_id"].lower()
        if ent.get("platform") in ("tplink_deco", "mobile_app") or any(w in eid for w in words):
            st = state_for(ent["entity_id"], idx)
            lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{st.get('state', 'unknown')}`")
    write_md(out / "06_netvaerk.md", lines)


def generate_problems(out, data, idx, a, now):
    lines = ["# 07 Problemer og oprydning", "", f"Genereret: {now}", ""]

    lines += ["## Kritiske offline/unknown", ""]
    for ent in sorted(a["offline_critical"], key=lambda e: e["entity_id"]):
        st = state_for(ent["entity_id"], idx)
        lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{st.get('state')}`")

    lines += ["", "## Lavt batteri", ""]
    for ent, val in sorted(a["low_batteries"], key=lambda x: x[1]):
        lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{val}%`")

    lines += ["", "## Unavailable", ""]
    for st in sorted(a["unavailable"], key=lambda s: s["entity_id"]):
        lines.append(f"- **{st.get('attributes', {}).get('friendly_name', st['entity_id'])}** — `{st['entity_id']}`")

    lines += ["", "## Unknown", ""]
    for st in sorted(a["unknown"], key=lambda s: s["entity_id"]):
        lines.append(f"- **{st.get('attributes', {}).get('friendly_name', st['entity_id'])}** — `{st['entity_id']}`")

    lines += ["", "## Enheder uden område", ""]
    for dev in sorted(a["devices_without_area"], key=device_name):
        lines.append(f"- **{device_name(dev)}** — `{dev.get('manufacturer','')}` `{dev.get('model','')}`")

    lines += ["", "## Entiteter uden område", ""]
    for ent in sorted(a["entities_without_area"], key=lambda e: e["entity_id"]):
        lines.append(f"- `{ent['entity_id']}`")

    lines += ["", "## Duplicate friendly names", ""]
    for name, count in sorted(a["duplicate_names"].items()):
        lines.append(f"- **{name}** — {count} stk.")

    write_md(out / "07_problemer.md", lines)


def generate_dashboard(out, idx, a, now):
    lines = ["# 08 Dashboard whitelist", "", f"Genereret: {now}", ""]
    for area_id, ents in sorted(a["dashboard_candidates_by_area"].items(), key=lambda x: area_name(x[0], idx)):
        lines += [f"## {area_name(area_id, idx)}", ""]
        for ent in sorted(ents, key=lambda e: e["entity_id"]):
            st = state_for(ent["entity_id"], idx)
            lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{st.get('state', 'unknown')}`")
        lines.append("")
    write_md(out / "08_dashboard_whitelist.md", lines)


def generate_battery(out, idx, a, now):
    lines = ["# 09 Batterier", "", f"Genereret: {now}", ""]
    for ent in sorted(a["battery_entities"], key=lambda e: e["entity_id"]):
        st = state_for(ent["entity_id"], idx)
        lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{st.get('state', 'unknown')}`")
    write_md(out / "09_batterier.md", lines)


def generate_architecture(out, idx, a, now):
    lines = [
        "# 10 Arkitektur",
        "",
        f"Genereret: {now}",
        "",
        "```text",
        "Internet",
        "  │",
        "  ├── Deco / Router",
        "  │     ├── WiFi-klienter",
        "  │     ├── Kameraer",
        "  │     └── IoT-enheder",
        "  │",
        "  └── HP Mini / Proxmox",
        "        ├── Home Assistant",
        "        ├── Zigbee2MQTT",
        "        ├── AdGuard",
        "        ├── Frigate",
        "        ├── Jellyfin",
        "        ├── Nextcloud",
        "        └── Proxy / NPM",
        "```",
        "",
        "## Serverrelaterede entiteter",
        "",
    ]
    for ent in sorted(a["server_entities"], key=lambda e: e["entity_id"]):
        st = state_for(ent["entity_id"], idx)
        lines.append(f"- `{ent['entity_id']}` — `{st.get('state', 'unknown')}`")
    write_md(out / "10_arkitektur.md", lines)
