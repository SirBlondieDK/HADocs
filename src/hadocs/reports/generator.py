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
from src.hadocs.core.incidents_v2 import build_incidents_v2
from src.hadocs.core.relationships import build_relationship_graph
from src.hadocs.exporters.csv_exporter import export_devices_csv, export_entities_csv
from src.hadocs.utils.text import slugify, write_md
from src.hadocs.html.explorer import write_explorer
from src.hadocs.knowledge.exporter import export_knowledge
from src.hadocs.core.health import apply_health_score_v2
from src.hadocs.core.intelligence import apply_intelligence_v014
from src.hadocs.utils.display import display_area, area_filename


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

    # Run Incidents v2 in parallel while the legacy engine remains official.
    # This allows real-world comparison without changing the dashboard,
    # history, executive summary, or existing report contracts yet.
    incidents_v2 = build_incidents_v2(model)

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

    # Keep Health Score v2 details available, but do not override the official score yet.
    executive = apply_intelligence_v014(model, executive, incidents)
    generate_index(out, project_name, executive, incidents, now)
    generate_executive_dashboard(out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now)
    generate_root_causes(out, incidents, now)
    generate_incidents(out, incidents, raw_incidents, now)
    generate_incidents_v2_comparison(
        out,
        legacy_incidents=raw_incidents,
        incidents_v2=incidents_v2,
        now=now,
    )
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


def generate_index(out: Path, project_name: str, *args) -> None:
    if len(args) == 3:
        executive, incidents, now = args
    elif len(args) >= 8:
        model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now = args[:8]
    else:
        raise TypeError(f"generate_index expected 3 or 8+ extra arguments, got {len(args)}")

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
        "- [18 Incidents v2 comparison](18_incidents_v2_comparison.md)",
        "- [CSV entities](csv/entities.csv)",
        "- [CSV devices](csv/devices.csv)",
    ]
    write_md(out / "index.md", lines)


def generate_executive_dashboard(out, project_name, model, executive, health_notes, history_comparison, trend_summary, incidents, raw_incidents, now):
    """Generate polished Dashboard Engine v2.

    Stable self-contained renderer.
    Always writes output/index.html.
    """

    import html
    import base64
    from pathlib import Path

    def get(obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def as_list(value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, dict):
            return list(value.values())
        return []

    def esc(value):
        return html.escape(str(value if value is not None else ""))

    def num(value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def clamp(value, low=0, high=100):
        return max(low, min(high, num(value)))

    def device_type(device):
        return str(get(device, "device_type", get(device, "type", ""))).lower()

    def title_of(incident):
        return get(incident, "title", get(incident, "root_cause", "Issue"))

    def root_of(incident):
        return get(incident, "root_cause", title_of(incident))

    def reason_of(incident):
        return get(incident, "reason", get(incident, "explanation", ""))

    def severity_of(incident):
        sev = str(get(incident, "severity", "")).lower()
        if sev in {"critical", "error"}:
            return "critical"
        if sev in {"warning", "warn"}:
            return "warning"
        return "maintenance"

    def affected_entities(incident):
        return as_list(get(incident, "affected_entities", []))

    def affected_devices(incident):
        return as_list(get(incident, "affected_devices", []))

    def children_of(incident):
        return as_list(get(incident, "children", [])) or as_list(get(incident, "child_incidents", []))

    def entity_label(value):
        if isinstance(value, dict):
            return value.get("entity_id") or value.get("name") or value.get("id") or str(value)
        return str(value)

    def try_logo_data_uri():
        candidates = [
            Path("docs/images/logo.png"),
            Path("docs/images/logo.svg"),
            Path("assets/logo.png"),
            Path("logo.png"),
        ]
        for path in candidates:
            if path.exists():
                data = path.read_bytes()
                if path.suffix.lower() == ".svg":
                    mime = "image/svg+xml"
                else:
                    mime = "image/png"
                return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        return ""

    logo_uri = try_logo_data_uri()

    areas = as_list(get(model, "areas", []))
    devices = as_list(get(model, "devices", []))
    entities = as_list(get(model, "entities", []))
    integrations = as_list(get(model, "integrations", []))

    score = clamp(get(executive, "score", 0))
    health_forecast = get(executive, "health_forecast", [])
    root_cause_intelligence = get(executive, "root_cause_intelligence", [])
    health_score_v2 = get(executive, "health_score_v2", {})
    score_grade = get(health_score_v2, "grade", "-")
    ignored_disabled = get(health_score_v2, "disabled_ignored", 0)
    normalized_penalty = get(health_score_v2, "normalized_penalty", 0)
    severity_penalty = get(health_score_v2, "severity_penalty", 0)
    root_cause_penalty = get(health_score_v2, "root_cause_penalty", 0)
    potential_score = clamp(get(executive, "potential_score", score))
    repair_minutes = num(get(executive, "estimated_repair_minutes", 0))
    main_cause = get(executive, "main_cause", "No major root cause")
    visible = as_list(incidents)
    raw = as_list(raw_incidents)

    critical = [i for i in visible if severity_of(i) == "critical"]
    warnings = [i for i in visible if severity_of(i) == "warning"]
    maintenance = [i for i in visible if severity_of(i) == "maintenance"]
    total_affected = sum(len(affected_entities(i)) for i in visible)
    hidden = max(0, len(raw) - len(visible))

    physical_devices = [d for d in devices if device_type(d) in {"physical", "device", ""}]
    virtual_devices = [d for d in devices if device_type(d) == "virtual"]
    system_devices = [d for d in devices if device_type(d) == "system"]

    status = "Healthy" if score >= 85 else "Needs attention" if score >= 60 else "Critical"
    status_class = "ok" if score >= 85 else "warn" if score >= 60 else "bad"

    top = visible[0] if visible else None
    top_title = title_of(top) if top else "No major issues found"
    top_root = root_of(top) if top else "Healthy installation"
    top_reason = reason_of(top) if top else "Your installation looks healthy."
    top_gain = get(top, "estimated_score_gain", 0) if top else 0
    top_minutes = get(top, "estimated_repair_minutes", 0) if top else 0

    def render_metric(label, value, sub="", icon=""):
        return f"""
        <div class="metric-card">
          <div class="metric-top">{f'<span>{icon}</span>' if icon else ''}<span>{esc(label)}</span></div>
          <div class="metric-value">{esc(value)}</div>
          {f'<div class="metric-sub">{esc(sub)}</div>' if sub else ''}
        </div>
        """

    def render_sidebar():
        items = [
            ("Dashboard", "#dashboard", "▣"),
            ("Executive", "#executive", "★"),
            ("Root Causes", "#root-causes", "◆"),
            ("Actions", "#actions", "✓"),
            ("Installation", "#installation", "⌂"),
            ("Health Notes", "#health-notes", "♡"),
            ("History", "#history", "↺"),
            ("Explorer", "explorer/index.html", "⌕"),
            ("Markdown", "index.md", "▤"),
            ("Knowledge", "knowledge/summary.md", "◇"),
        ]
        links = "".join(f'<a class="{ "active" if idx == 0 else "" }" href="{href}"><span>{icon}</span>{label}</a>' for idx, (label, href, icon) in enumerate(items))
        logo = f'<img src="{logo_uri}" alt="HADocs logo">' if logo_uri else '<div class="logo-fallback">HA</div>'
        return f"""
        <aside class="sidebar">
          <div class="logo-wrap">{logo}<small>HADocs</small></div>
          <div class="brand">
            <h1>HADocs</h1>
            <p>Smart Home Intelligence</p>
          </div>
          <nav>{links}</nav>
          <div class="side-note">Local only • No cloud • No AI calls</div>
        </aside>
        """

    def render_hero():
        return f"""
        <section class="hero-grid" id="dashboard">
          <div class="panel hero">
            <span class="pill {status_class}">{esc(status)}</span>
            <h2>{esc(project_name)}</h2>
            <p class="lead">
              Main root cause: <strong>{esc(main_cause)}</strong>. Fixing the highest-impact issues could improve
              the Health Score from <strong>{score}</strong> to <strong>{potential_score}</strong>.
            </p>
            <div class="hero-stats">
              {render_metric("Potential score", f"{potential_score}/100", "after top fixes", "▲")}
              {render_metric("Repair time", f"{repair_minutes} min", "estimated", "⏱")}
              {render_metric("Affected entities", total_affected, "relevant symptoms", "⚡")}
            </div>
          </div>

          <div class="panel health-panel">
            <div class="ring" style="--value:{score}">
              <span>{score}</span>
              <small>HEALTH</small>
            </div>
            <div>
              <h2>Health Score</h2>
              <p class="muted">Based on device health, unavailable entities, areas, duplicates and filtered diagnostic noise.</p>
              <div class="badges">
                <span>{len(critical)} critical</span>
                <span>{len(warnings)} warnings</span>
                <span>{len(maintenance)} maintenance</span>
              </div>
            </div>
          </div>
        </section>
        """

    def render_executive():
        return f"""
        <section class="section panel" id="executive">
          <div class="section-head">
            <h2>Executive Summary</h2>
            <p class="muted">What matters most in this scan.</p>
          </div>
          <div class="summary-grid">
            <div class="summary-main">
              <h3>{esc(top_root)}</h3>
              <p>{esc(top_title)}</p>
              <p class="muted">{esc(top_reason)}</p>
            </div>
            {render_metric("Current score", f"{score}/100", status, "♡")}
            {render_metric("Top fix gain", f"+{top_gain}", "health score", "▲")}
            {render_metric("Hidden noise", hidden, "lower priority", "◌")}
          </div>
        </section>
        """

    def render_installation():
        return f"""
        <section class="section panel" id="installation">
          <div class="section-head">
            <h2>Installation Overview</h2>
            <p class="muted">Inventory summary from this scan.</p>
          </div>
          <div class="grid">
            {render_metric("Areas", len(areas), icon="⌂")}
            {render_metric("Physical devices", len(physical_devices), icon="▣")}
            {render_metric("Virtual devices", len(virtual_devices), icon="◇")}
            {render_metric("System devices", len(system_devices), icon="⚙")}
            {render_metric("Integrations", len(integrations), icon="⌁")}
            {render_metric("Entities", len(entities), icon="⚡")}
            {render_metric("Collapsed root causes", len(visible), icon="◆")}
            {render_metric("Raw incidents", len(raw), icon="▤")}
          </div>
        </section>
        """

    def render_actions():
        rows = []
        for idx, incident in enumerate(visible[:8], 1):
            rows.append(f"""
            <li>
              <span class="rank">{idx}</span>
              <div>
                <strong>{esc(root_of(incident))}</strong>
                <p>{esc(reason_of(incident) or title_of(incident))}</p>
              </div>
            </li>
            """)
        if not rows:
            rows.append("<li><span class='rank'>✓</span><div><strong>No action needed</strong><p>No root causes found.</p></div></li>")

        return f"""
        <section class="section panel" id="actions">
          <div class="section-head">
            <h2>Top Recommendation</h2>
            <p class="muted">Highest-impact actions first.</p>
          </div>
          <div class="recommendation">
            <h3>{esc(top_title)}</h3>
            <p class="muted">+{esc(top_gain)} Health Score • ~{esc(top_minutes)} min</p>
            <p>{esc(top_reason)}</p>
          </div>
          <ol class="action-list">{''.join(rows)}</ol>
        </section>
        """

    def render_root_cards():
        cards = []
        for incident in visible[:18]:
            info = intelligence_for(root_of(incident))
            explanation = get(info, "explain", {})
            impact_score = get(info, "impact_score", 0)
            impact_label_text = get(info, "impact_label", "Impact")
            sev = severity_of(incident)
            ents = affected_entities(incident)
            devs = affected_devices(incident)
            children = children_of(incident)
            child_count = num(get(incident, "child_count", len(children)), len(children))
            gain = get(incident, "estimated_score_gain", 0)
            minutes = get(incident, "estimated_repair_minutes", 0)

            child_html = ""
            if children:
                child_items = []
                for child in children[:5]:
                    child_items.append(f"<li>{esc(get(child, 'title', get(child, 'entity_id', child)))}</li>")
                if len(children) > 5:
                    child_items.append(f"<li>...and {len(children) - 5} more</li>")
                child_html = f"<details><summary>Child incidents</summary><ul>{''.join(child_items)}</ul></details>"

            entity_html = ""
            if ents:
                entity_items = "".join(f"<li>{esc(entity_label(e))}</li>" for e in ents[:8])
                if len(ents) > 8:
                    entity_items += f"<li>...and {len(ents) - 8} more</li>"
                entity_html = f"<details><summary>Affected entities</summary><ul>{entity_items}</ul></details>"

            cards.append(f"""
            <article class="root-card {sev}">
              <div class="severity-line"></div>
              <h3>{esc(root_of(incident))}</h3>
              <p class="muted">{esc(title_of(incident))}</p>
              <div class="badges">
                <span>{sev.upper()}</span>
                <span>{len(ents)} entities</span>
                <span>{len(devs)} devices</span>
                <span>{child_count} child incidents</span>
                <span>+{esc(gain)} score</span>
                <span>~{esc(minutes)} min</span>
                <span>{esc(impact_label_text)}</span>
                <span>{esc(impact_score)} impact</span>
              </div>
              <div class="impact-bar"><i style="width:{min(100, max(7, len(ents)))}%"></i></div>
              <p>{esc(reason_of(incident))}</p>

              <details class="explain-box">
                <summary>Explain this</summary>
                <div class="explain-grid">
                  <div class="explain-item">
                    <h4>Why this happened</h4>
                    <p>{esc(get(explanation, "why", "HADocs detected that multiple symptoms point to the same root cause."))}</p>
                  </div>
                  <div class="explain-item">
                    <h4>Impact</h4>
                    <p>{esc(get(explanation, "impact", "This issue affects several Home Assistant entities or devices."))}</p>
                  </div>
                  <div class="explain-item">
                    <h4>How to verify</h4>
                    <p>{esc(get(explanation, "verify", "Open the related integration or device in Home Assistant and check availability, logs and recent changes."))}</p>
                  </div>
                  <div class="explain-item">
                    <h4>Suggested fix</h4>
                    <p>{esc(get(explanation, "fix", "Fix the parent integration or device first, then run HADocs again to verify that child incidents disappear."))}</p>
                  </div>
                </div>
                <p class="muted">{esc(get(explanation, "time", f"Estimated repair time: about {minutes} minutes."))}</p>
              </details>

              {child_html}
              {entity_html}
            </article>
            """)

        return f"""
        <section class="section" id="root-causes">
          <div class="section-head">
            <h2>Top Root Causes</h2>
            <p class="muted">Collapsed issues grouped by likely root cause.</p>
          </div>
          <div class="cards">{''.join(cards) if cards else '<div class="panel">No root causes found.</div>'}</div>
        </section>
        """

    def render_health_notes():
        notes = as_list(health_notes)
        note_html = "".join(f"<li>{esc(note)}</li>" for note in notes) if notes else "<li>No detailed health notes available.</li>"
        return f"""
        <section class="section panel" id="health-notes">
          <div class="section-head">
            <h2>Score Explanation</h2>
            <p class="muted">Why the health score is what it is.</p>
          </div>
          <ul class="notes">{note_html}</ul>
        </section>
        """

    def render_history():
        if history_comparison:
            delta = get(history_comparison, "health_delta", 0)
            problem_delta = get(history_comparison, "problem_entity_delta", 0)
            new_count = len(as_list(get(history_comparison, "new_root_causes", [])))
            resolved_count = len(as_list(get(history_comparison, "resolved_root_causes", [])))
            content = f"""
            <div class="grid four">
              {render_metric("Health change", f"{delta:+}", icon="↺")}
              {render_metric("Problem entity change", f"{problem_delta:+}", icon="⚡")}
              {render_metric("New root causes", new_count, icon="+")}
              {render_metric("Resolved root causes", resolved_count, icon="✓")}
            </div>
            """
        else:
            content = "<p class='muted'>No previous scan comparison available yet.</p>"

        scan_count = get(trend_summary, "scan_count", 0) if trend_summary else 0
        if scan_count:
            content += f"<p class='muted trend-note'>Trend history contains {esc(scan_count)} scans.</p>"

        return f"""
        <section class="section panel" id="history">
          <div class="section-head">
            <h2>History</h2>
            <p class="muted">Changes since previous scans.</p>
          </div>
          {content}
        </section>
        """


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


    def render_output_links():
        return """
        <section class="section panel">
          <div class="section-head">
            <h2>Generated Output</h2>
            <p class="muted">Open the generated reports.</p>
          </div>
          <div class="link-grid">
            <a href="explorer/index.html">Open Explorer</a>
            <a href="index.md">Open Markdown Report</a>
            <a href="knowledge/summary.md">Open Knowledge Summary</a>
            <a href="01_root_causes.md">Open Root Causes Markdown</a>
          </div>
        </section>
        """

    css = """
    :root{--bg:#0b1220;--panel:#111a2c;--card:#111827;--card2:#0f172a;--border:#243044;--text:#f8fafc;--muted:#b6c4d6;--blue:#38bdf8;--yellow:#facc15;--red:#fb7185;--green:#22c55e;--purple:#a78bfa}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Segoe UI,Inter,Arial,sans-serif;color:var(--text);background:radial-gradient(circle at top right,#18213a 0,#0b1220 42%,#070d19 100%);line-height:1.55}a{color:inherit;text-decoration:none}
    .app{display:flex;min-height:100vh}.sidebar{position:sticky;top:0;width:270px;min-height:100vh;padding:28px 22px;background:rgba(15,23,42,.95);border-right:1px solid var(--border)}.logo-wrap{text-align:center;margin-bottom:22px}.logo-wrap img{width:72px;height:72px;object-fit:contain;display:block;margin:0 auto 6px}.logo-wrap small{color:#7dd3fc}.logo-fallback{width:64px;height:64px;margin:0 auto 6px;border-radius:18px;display:grid;place-items:center;background:linear-gradient(135deg,#60a5fa,#a78bfa);font-weight:900}.brand{text-align:center;margin-bottom:28px}.brand h1{font-size:28px;margin:0}.brand p{margin:4px 0 0;color:var(--muted);font-size:13px}nav a{display:flex;gap:10px;align-items:center;padding:12px 14px;border-radius:12px;color:#e5eefb;margin:6px 0}nav a:hover,nav a.active{background:#1b2740}.side-note{position:absolute;bottom:24px;color:var(--muted);font-size:12px}
    .content{flex:1;padding:42px;max-width:1760px}.hero-grid{display:grid;grid-template-columns:minmax(0,2fr) minmax(360px,1.1fr);gap:28px}.panel{background:linear-gradient(180deg,rgba(17,26,44,.98),rgba(15,23,42,.98));border:1px solid var(--border);border-radius:24px;padding:28px;box-shadow:0 20px 60px rgba(0,0,0,.18)}.hero h2{font-size:48px;line-height:1.04;margin:10px 0 12px}.lead{font-size:16px;color:#d8e3f0}.pill{display:inline-flex;border:1px solid var(--border);border-radius:999px;padding:6px 14px;color:var(--muted);font-size:13px;text-transform:uppercase;letter-spacing:.05em}.pill.ok{color:#bbf7d0}.pill.warn{color:#fde68a}.pill.bad{color:#fecaca}.muted{color:var(--muted)}.hero-stats,.summary-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:24px}.summary-grid{grid-template-columns:2fr repeat(3,1fr)}.summary-main{border:1px solid var(--border);border-radius:16px;padding:18px;background:#0d1424}.summary-main h3{margin-top:0}
    .metric-card{border:1px solid var(--border);border-radius:16px;padding:18px;background:#0d1424}.metric-top{display:flex;gap:8px;color:var(--muted);font-size:13px}.metric-value{font-size:30px;font-weight:900;margin-top:8px}.metric-label{color:#e5eefb}.metric-sub{color:var(--muted);font-size:13px}.health-panel{display:flex;gap:26px;align-items:center}.ring{width:160px;height:160px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(var(--yellow) calc(var(--value)*1%),#253044 0);position:relative;flex:0 0 auto}.ring::before{content:"";position:absolute;inset:18px;border-radius:50%;background:#0f172a}.ring span{position:relative;font-size:44px;font-weight:900}.ring small{position:relative;color:var(--muted);font-size:12px;margin-top:-48px}.section{margin-top:30px}.section-head{margin-bottom:16px}.section h2{margin:0 0 6px;font-size:28px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.grid.four{grid-template-columns:repeat(4,minmax(0,1fr))}
    .recommendation{border:1px solid var(--border);border-radius:18px;padding:20px;background:#0d1424;margin-bottom:18px}.action-list{padding-left:0;list-style:none}.action-list li{display:flex;gap:14px;margin:12px 0;padding:14px;border:1px solid var(--border);border-radius:14px;background:#0d1424}.rank{width:28px;height:28px;display:grid;place-items:center;border-radius:999px;background:#243044;color:#fff;font-weight:800;flex:0 0 auto}.action-list p{margin:4px 0 0;color:var(--muted)}
    .cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.root-card{position:relative;overflow:hidden;background:#111a2c;border:1px solid var(--border);border-radius:22px;padding:24px}.root-card h3{margin:0 0 8px}.severity-line{position:absolute;top:0;left:0;right:0;height:5px;background:var(--purple)}.root-card.critical .severity-line{background:var(--red)}.root-card.warning .severity-line{background:var(--yellow)}.root-card.maintenance .severity-line{background:var(--blue)}.badges{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}.badges span{padding:5px 10px;border-radius:999px;background:#253044;color:#dbeafe;font-size:12px}.impact-bar{height:9px;background:#253044;border-radius:999px;overflow:hidden;margin:12px 0 18px}.impact-bar i{display:block;height:100%;background:linear-gradient(90deg,var(--blue),var(--purple))}details{margin-top:14px;color:var(--muted)}details ul{padding-left:20px;max-height:210px;overflow:auto}.notes li{margin:8px 0}.link-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.link-grid a{border:1px solid var(--border);border-radius:14px;background:#0d1424;padding:16px;color:#7dd3fc}.explain-box{margin-top:16px;border:1px solid var(--border);border-radius:16px;background:#0b1220;padding:14px}.explain-box summary{cursor:pointer;font-weight:900;color:#e5eefb}.explain-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}.explain-item{border:1px solid var(--border);border-radius:14px;background:#0d1424;padding:12px}.explain-item h4{margin:0 0 6px;font-size:12px;color:#9fc2ff;text-transform:uppercase;letter-spacing:.04em}.explain-item p{margin:0;color:#cbd5e1;line-height:1.45}@media(max-width:900px){.explain-grid{grid-template-columns:1fr}}.footer{margin:34px 0 10px;color:var(--muted);font-size:13px}.forecast{display:grid;gap:14px}.forecast-step{display:flex;gap:16px;border:1px solid var(--border);border-radius:18px;background:#0d1424;padding:18px}.forecast-number{width:34px;height:34px;border-radius:999px;background:#243044;display:grid;place-items:center;font-weight:900;flex:0 0 auto}.forecast-body{flex:1}.explain{margin-top:16px;border-top:1px solid var(--border);padding-top:12px}.explain h4{margin:12px 0 4px}.trend-note{margin-top:18px}
    @media(max-width:1100px){.app{display:block}.sidebar{position:relative;width:auto;min-height:auto}.side-note{position:static;margin-top:20px}.hero-grid,.cards,.grid,.grid.four,.link-grid,.summary-grid{grid-template-columns:1fr}.content{padding:22px}.hero h2{font-size:34px}}
    """

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{esc(project_name)} - HADocs</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>{css}</style>
</head>
<body>
  <div class="app">
    {render_sidebar()}
    <main class="content">
      {render_hero()}
      {render_executive()}
      {render_installation()}
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
        <p class="muted">Root-cause penalty: {esc(root_cause_penalty)}. This makes large installations feel fairer while keeping serious issues visible.</p>
      </section>
      {render_health_forecast()}
      {render_actions()}
      {render_root_cards()}
      {render_health_notes()}
      {render_history()}
      {render_output_links()}
      <p class="footer">Generated {esc(now)} • HADocs runs locally • No cloud upload • No AI calls</p>
    </main>
  </div>
</body>
</html>"""

    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html_doc, encoding="utf-8")

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


def generate_incidents_v2_comparison(
    out,
    legacy_incidents,
    incidents_v2,
    now,
):
    """Write a side-by-side comparison of legacy and evidence-based incidents."""

    severity_order = {
        "critical": 0,
        "warning": 1,
        "maintenance": 2,
        "info": 3,
    }

    def severity_of(item):
        return str(getattr(item, "severity", "info") or "info").lower()

    def entity_ids(item):
        return set(getattr(item, "affected_entities", []) or [])

    legacy_problem_entities = {
        entity_id
        for incident in legacy_incidents
        for entity_id in entity_ids(incident)
    }
    v2_problem_entities = {
        entity_id
        for incident in incidents_v2
        for entity_id in entity_ids(incident)
    }

    suppressed_entities = sorted(
        legacy_problem_entities - v2_problem_entities
    )
    newly_prioritized_entities = sorted(
        v2_problem_entities - legacy_problem_entities
    )

    legacy_by_severity = Counter(
        severity_of(incident)
        for incident in legacy_incidents
    )
    v2_by_severity = Counter(
        severity_of(incident)
        for incident in incidents_v2
    )

    lines = [
        "# 18 Incidents v2 comparison",
        "",
        f"Generated: {now}",
        "",
        "This report compares the legacy count-based incident engine with "
        "the evidence-based Incidents v2 engine.",
        "",
        "Incidents v2 is comparison-only at this stage. The existing dashboard, "
        "history, executive summary, and official Health Score still use the "
        "legacy incident engine.",
        "",
        "## Summary",
        "",
        f"- Legacy raw incidents: `{len(legacy_incidents)}`",
        f"- Incidents v2: `{len(incidents_v2)}`",
        f"- Legacy affected entities: `{len(legacy_problem_entities)}`",
        f"- V2 affected entities: `{len(v2_problem_entities)}`",
        f"- Suppressed legacy-only entities: `{len(suppressed_entities)}`",
        f"- Newly prioritized by v2: `{len(newly_prioritized_entities)}`",
        "",
        "## Severity comparison",
        "",
        "| Severity | Legacy | Incidents v2 |",
        "|---|---:|---:|",
    ]

    for severity in ("critical", "warning", "maintenance", "info"):
        lines.append(
            f"| {severity} | "
            f"{legacy_by_severity.get(severity, 0)} | "
            f"{v2_by_severity.get(severity, 0)} |"
        )

    lines += [
        "",
        "## Evidence-based incidents",
        "",
    ]

    if not incidents_v2:
        lines.append("No evidence-based incidents detected.")
        lines.append("")
    else:
        for incident in sorted(
            incidents_v2,
            key=lambda item: (
                severity_order.get(severity_of(item), 9),
                -int(getattr(item, "confidence", 0) or 0),
                str(getattr(item, "root_cause", "")).lower(),
            ),
        ):
            evidence = list(getattr(incident, "evidence", []) or [])
            affected_entities = list(
                getattr(incident, "affected_entities", []) or []
            )
            affected_devices = list(
                getattr(incident, "affected_devices", []) or []
            )

            lines += [
                f"### {getattr(incident, 'root_cause', 'Unknown root cause')}",
                "",
                f"- Title: {getattr(incident, 'title', '')}",
                f"- Category: `{getattr(incident, 'category', '')}`",
                f"- Severity: `{severity_of(incident)}`",
                f"- Confidence: `{getattr(incident, 'confidence', 0)}%`",
                f"- Affected entities: `{len(affected_entities)}`",
                f"- Affected devices: `{len(affected_devices)}`",
                f"- Integrations: `{', '.join(getattr(incident, 'affected_integrations', []) or [])}`",
                "",
            ]

            if evidence:
                lines += ["#### Evidence", ""]
                for item in evidence:
                    lines.append(f"- {item}")
                lines.append("")

            recommendation = getattr(incident, "recommendation", "")
            if recommendation:
                lines += [
                    "#### Recommendation",
                    "",
                    recommendation,
                    "",
                ]

            if affected_entities:
                lines += ["#### Affected entities", ""]
                for entity_id in affected_entities[:30]:
                    lines.append(f"- `{entity_id}`")
                if len(affected_entities) > 30:
                    lines.append(
                        f"- ...and {len(affected_entities) - 30} more"
                    )
                lines.append("")

    lines += [
        "## Suppressed legacy-only entities",
        "",
        "These entities were treated as incident symptoms by the legacy engine "
        "but were not included by Incidents v2.",
        "",
    ]

    if suppressed_entities:
        for entity_id in suppressed_entities[:100]:
            lines.append(f"- `{entity_id}`")
        if len(suppressed_entities) > 100:
            lines.append(
                f"- ...and {len(suppressed_entities) - 100} more"
            )
    else:
        lines.append("None.")

    lines += [
        "",
        "## Newly prioritized by Incidents v2",
        "",
    ]

    if newly_prioritized_entities:
        for entity_id in newly_prioritized_entities[:100]:
            lines.append(f"- `{entity_id}`")
        if len(newly_prioritized_entities) > 100:
            lines.append(
                f"- ...and {len(newly_prioritized_entities) - 100} more"
            )
    else:
        lines.append("None.")

    lines.append("")
    write_md(out / "18_incidents_v2_comparison.md", lines)


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
    for area in sorted(model.areas.values(), key=lambda a: display_area(a.name)):
        filename = f"{area_filename(area.name, slugify)}.md"
        index.append(f"- [{display_area(area.name)}]({filename}) — {len(area.devices)} devices, {len(area.entities)} entities")
        lines = [f"# {display_area(area.name)}", "", f"Generated: {now}", "", "## Devices", ""]
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
