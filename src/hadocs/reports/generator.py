from pathlib import Path
from datetime import datetime
from src.hadocs.analyzers.core import analyze
from src.hadocs.analyzers.health import calculate_health_score
from src.hadocs.analyzers.helpers import area_name, device_name, entity_area, friendly_name, state_for
from src.hadocs.exporters.csv_exporter import export_entities_csv
from src.hadocs.utils.text import safe, slugify, write_md


def generate_all(data: dict, idx: dict, cfg: dict, log=print) -> None:
    out = Path(cfg.get("output_dir", "output")); out.mkdir(exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = cfg.get("project_name", "Home Assistant")
    analysis = analyze(data, idx)
    health_score, health_notes = calculate_health_score(analysis)
    generate_index(out, project_name, now, health_score)
    generate_summary(out, data, analysis, health_score, health_notes, now)
    generate_areas(out, idx, now)
    generate_devices(out, data, idx, now)
    generate_integrations(out, data, idx, now)
    generate_server(out, idx, analysis, now)
    generate_network(out, data, idx, now)
    generate_problems(out, idx, analysis, now)
    generate_dashboard(out, idx, analysis, now)
    generate_battery(out, idx, analysis, now)
    generate_architecture(out, idx, analysis, now)
    generate_health_details(out, analysis, health_score, health_notes, now)
    export_entities_csv(out, data, idx)
    log(f"Documentation complete: {out / 'index.md'}")


def generate_index(out, project_name, now, health_score):
    write_md(out / "index.md", [f"# {project_name} - Documentation", "", f"Generated: {now}", "", f"## Health Score: `{health_score}/100`", "", "## Reports", "", "- [01 Overview](01_oversigt.md)", "- [02 Areas](02_rum/index.md)", "- [03 Devices](03_enheder/index.md)", "- [04 Integrations](04_integrationer.md)", "- [05 Server Room](05_serverrum.md)", "- [06 Network](06_netvaerk.md)", "- [07 Problems and cleanup](07_problemer.md)", "- [08 Dashboard whitelist](08_dashboard_whitelist.md)", "- [09 Batteries](09_batterier.md)", "- [10 Architecture](10_arkitektur.md)", "- [11 Health Score details](11_health_score.md)", "- [CSV data](csv/entities.csv)"])


def generate_summary(out, data, a, health_score, health_notes, now):
    lines = ["# 01 Overview", "", f"Generated: {now}", "", f"## Health Score: `{health_score}/100`", ""]
    lines += [f"- {n}" for n in health_notes] or ["- No major problems found."]
    lines += ["", "## System", "", f"- Home Assistant version: `{data['config'].get('version', '')}`", f"- Location: `{data['config'].get('location_name', '')}`", f"- Time zone: `{data['config'].get('time_zone', '')}`", f"- States: `{a['counts']['states']}`", f"- Entities: `{a['counts']['entities']}`", f"- Devices: `{a['counts']['devices']}`", f"- Areas: `{a['counts']['areas']}`", f"- Raw unknown states: `{a['counts']['unknown']}`", f"- Raw unavailable states: `{a['counts']['unavailable']}`", f"- Real unknown states: `{len(a['real_unknown'])}`", f"- Real unavailable states: `{len(a['real_unavailable'])}`", f"- Ignored unknown/unavailable states: `{len(a['ignored_unknown_unavailable'])}`", "", "## Domains", ""]
    for domain, count in sorted(a["domain_counts"].items()): lines.append(f"- `{domain}`: {count}")
    lines += ["", "## Platforms", ""]
    for platform, count in sorted(a["platform_counts"].items()): lines.append(f"- `{platform}`: {count}")
    write_md(out / "01_oversigt.md", lines)


def generate_areas(out, idx, now):
    area_dir = out / "02_rum"; index = ["# 02 Areas", "", f"Generated: {now}", ""]
    for area_id, ents in sorted(idx["entities_by_area"].items(), key=lambda x: area_name(x[0], idx)):
        name = area_name(area_id, idx); filename = f"{slugify(name)}.md"; index.append(f"- [{name}]({filename}) — {len(ents)} entities")
        lines = [f"# {name}", "", f"Generated: {now}", ""]
        by_domain = {}
        for ent in ents: by_domain.setdefault(ent["entity_id"].split(".")[0], []).append(ent)
        for domain in sorted(by_domain):
            lines += [f"## {domain}", ""]
            for ent in sorted(by_domain[domain], key=lambda e: e["entity_id"]):
                st = state_for(ent["entity_id"], idx); lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{st.get('state', 'unknown')}`")
            lines.append("")
        write_md(area_dir / filename, lines)
    write_md(area_dir / "index.md", index)


def generate_devices(out, data, idx, now):
    dev_dir = out / "03_enheder"; index = ["# 03 Devices", "", f"Generated: {now}", ""]
    for dev in sorted(data["devices"], key=lambda d: (area_name(d.get("area_id"), idx), device_name(d))):
        name = device_name(dev); filename = f"{slugify(area_name(dev.get('area_id'), idx))}__{slugify(name)}.md"; index.append(f"- [{name}]({filename}) — {area_name(dev.get('area_id'), idx)}")
        lines = [f"# {name}", "", f"Generated: {now}", "", f"- Area: `{area_name(dev.get('area_id'), idx)}`", f"- Manufacturer: `{safe(dev.get('manufacturer'))}`", f"- Model: `{safe(dev.get('model'))}`", f"- Hardware: `{safe(dev.get('hw_version'))}`", f"- Software: `{safe(dev.get('sw_version'))}`", f"- Device ID: `{dev.get('id')}`"]
        if dev.get("configuration_url"): lines.append(f"- Configuration URL: `{dev.get('configuration_url')}`")
        lines += ["", "## Entities", ""]
        for ent in sorted(idx["entities_by_device"].get(dev["id"], []), key=lambda e: e["entity_id"]): lines.append(f"- `{ent['entity_id']}` — `{state_for(ent['entity_id'], idx).get('state', 'unknown')}`")
        write_md(dev_dir / filename, lines)
    write_md(dev_dir / "index.md", index)


def generate_integrations(out, data, idx, now):
    lines = ["# 04 Integrations", "", f"Generated: {now}", ""]
    for platform, ents in sorted(idx["entities_by_platform"].items()):
        states = [state_for(e["entity_id"], idx).get("state", "unknown") for e in ents]; bad = sum(1 for s in states if s in ("unknown", "unavailable"))
        lines += [f"## {platform}", "", f"- Count: `{len(ents)}`", f"- Raw unknown/unavailable: `{bad}`", ""]
        for ent in sorted(ents, key=lambda e: e["entity_id"]): lines.append(f"- `{ent['entity_id']}` — `{state_for(ent['entity_id'], idx).get('state', 'unknown')}`")
        lines.append("")
    write_md(out / "04_integrationer.md", lines)


def generate_server(out, idx, a, now):
    lines = ["# 05 Server Room", "", f"Generated: {now}", ""]
    for ent in sorted(a["server_entities"], key=lambda e: e["entity_id"]): lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{state_for(ent['entity_id'], idx).get('state', 'unknown')}`")
    write_md(out / "05_serverrum.md", lines)


def generate_network(out, data, idx, now):
    words = ["deco","wifi","wlan","internet","rssi","linkquality","device_tracker","adguard","dns","remote_ui"]
    lines = ["# 06 Network", "", f"Generated: {now}", ""]
    for ent in sorted(data["entities"], key=lambda e: e["entity_id"]):
        if ent.get("platform") in ("tplink_deco", "mobile_app") or any(w in ent["entity_id"].lower() for w in words): lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{state_for(ent['entity_id'], idx).get('state', 'unknown')}`")
    write_md(out / "06_netvaerk.md", lines)


def generate_problems(out, idx, a, now):
    lines = ["# 07 Problems and cleanup", "", f"Generated: {now}", "", "## Critical offline/unknown", ""]
    for ent in sorted(a["offline_critical"], key=lambda e: e["entity_id"]): lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{state_for(ent['entity_id'], idx).get('state')}`")
    for title, key in [("Low battery", "low_batteries"), ("Real unavailable", "real_unavailable"), ("Real unknown", "real_unknown"), ("Ignored unknown/unavailable", "ignored_unknown_unavailable")]:
        lines += ["", f"## {title}", ""]
        items = a[key]
        if key == "low_batteries":
            for ent, val in sorted(items, key=lambda x: x[1]): lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{val}%`")
        elif key.startswith("real") or key.startswith("ignored"):
            for st in sorted(items, key=lambda s: s["entity_id"]): lines.append(f"- **{st.get('attributes', {}).get('friendly_name', st['entity_id'])}** — `{st['entity_id']}` — `{st.get('state')}`")
    lines += ["", "## Physical devices without area", ""]
    for dev in sorted(a["devices_without_area"], key=device_name): lines.append(f"- **{device_name(dev)}** — `{dev.get('manufacturer','')}` `{dev.get('model','')}`")
    lines += ["", "## Physical entities without area", ""]
    for ent in sorted(a["entities_without_area"], key=lambda e: e["entity_id"]): lines.append(f"- `{ent['entity_id']}`")
    lines += ["", "## Duplicate friendly names", ""]
    for name, count in sorted(a["duplicate_names"].items()): lines.append(f"- **{name}** — {count}")
    write_md(out / "07_problemer.md", lines)


def generate_dashboard(out, idx, a, now):
    lines = ["# 08 Dashboard whitelist", "", f"Generated: {now}", ""]
    for area_id, ents in sorted(a["dashboard_candidates_by_area"].items(), key=lambda x: area_name(x[0], idx)):
        lines += [f"## {area_name(area_id, idx)}", ""]
        for ent in sorted(ents, key=lambda e: e["entity_id"]): lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{state_for(ent['entity_id'], idx).get('state', 'unknown')}`")
        lines.append("")
    write_md(out / "08_dashboard_whitelist.md", lines)


def generate_battery(out, idx, a, now):
    lines = ["# 09 Batteries", "", f"Generated: {now}", ""]
    for ent in sorted(a["battery_entities"], key=lambda e: e["entity_id"]): lines.append(f"- **{friendly_name(ent, idx)}** — `{ent['entity_id']}` — `{state_for(ent['entity_id'], idx).get('state', 'unknown')}`")
    write_md(out / "09_batterier.md", lines)


def generate_architecture(out, idx, a, now):
    lines = ["# 10 Architecture", "", f"Generated: {now}", "", "```text", "Internet", "  │", "  ├── Deco / Router", "  │     ├── WiFi clients", "  │     ├── Cameras", "  │     └── IoT devices", "  │", "  └── HP Mini / Proxmox", "        ├── Home Assistant", "        ├── Zigbee2MQTT", "        ├── AdGuard", "        ├── Frigate", "        ├── Jellyfin", "        ├── Nextcloud", "        └── Proxy / NPM", "```", "", "## Server-related entities", ""]
    for ent in sorted(a["server_entities"], key=lambda e: e["entity_id"]): lines.append(f"- `{ent['entity_id']}` — `{state_for(ent['entity_id'], idx).get('state', 'unknown')}`")
    write_md(out / "10_arkitektur.md", lines)


def generate_health_details(out, a, health_score, health_notes, now):
    lines = ["# 11 Health Score details", "", f"Generated: {now}", "", f"Health Score: `{health_score}/100`", "", "## Notes", ""] + [f"- {note}" for note in health_notes]
    lines += ["", "## Counts used by Health Score", "", f"- Critical offline/unknown: `{len(a['offline_critical'])}`", f"- Real unavailable: `{len(a['real_unavailable'])}`", f"- Real unknown: `{len(a['real_unknown'])}`", f"- Low batteries: `{len(a['low_batteries'])}`", f"- Physical devices without area: `{len(a['devices_without_area'])}`", f"- Duplicate friendly names: `{len(a['duplicate_names'])}`", f"- Ignored unknown/unavailable: `{len(a['ignored_unknown_unavailable'])}`", "", "## Ignored entity model", "", "The Health Score ignores service-only and system entities such as buttons, update entities, events, images, notify services, conversation agents, STT/TTS entities, snapshot actions, restart actions, and firmware controls."]
    write_md(out / "11_health_score.md", lines)
