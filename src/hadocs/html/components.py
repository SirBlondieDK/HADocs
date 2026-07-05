import html

from src.hadocs.explain.engine import explain_incident


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def severity_color(severity: str) -> str:
    return {
        "critical": "var(--red)",
        "warning": "var(--yellow)",
        "maintenance": "var(--blue)",
        "info": "var(--purple)",
    }.get(severity, "var(--blue)")


def health_ring(score: int) -> str:
    score = max(0, min(100, int(score)))
    radius = 54
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1 - score / 100)
    color = "var(--green)" if score >= 85 else "var(--yellow)" if score >= 60 else "var(--red)"
    return f"""
<svg width="170" height="170" viewBox="0 0 170 170" role="img" aria-label="Health score {score}">
  <circle cx="85" cy="85" r="{radius}" fill="none" stroke="rgba(255,255,255,.09)" stroke-width="16"/>
  <circle cx="85" cy="85" r="{radius}" fill="none" stroke="{color}" stroke-width="16"
          stroke-linecap="round"
          stroke-dasharray="{circumference:.2f}"
          stroke-dashoffset="{offset:.2f}"
          transform="rotate(-90 85 85)"/>
  <text x="85" y="84" text-anchor="middle" dominant-baseline="middle" class="ring-number" fill="currentColor">{score}</text>
  <text x="85" y="112" text-anchor="middle" dominant-baseline="middle" class="ring-label">HEALTH</text>
</svg>
"""


def metric(label: str, value: str, extra: str = "") -> str:
    return f"""
<div class="metric">
  <div class="value">{esc(value)}</div>
  <div class="label">{esc(label)}</div>
  {extra}
</div>
"""


def severity_badge(severity: str) -> str:
    return f'<span class="badge {esc(severity)}">{esc(severity.upper())}</span>'


def explanation_block(incident) -> str:
    explanation = explain_incident(incident)
    steps = "".join(f"<li>{esc(step)}</li>" for step in explanation["what_to_try_first"])
    return f"""
<details class="explain">
  <summary>Explain this</summary>
  <h4>{esc(explanation["title"])}</h4>
  <p><strong>What it means:</strong> {esc(explanation["what_it_means"])}</p>
  <p><strong>Why it matters:</strong> {esc(explanation["why_it_matters"])}</p>
  <p><strong>Try first:</strong></p>
  <ol>{steps}</ol>
</details>
"""


def root_cause_card(incident) -> str:
    children = ""
    if getattr(incident, "child_incidents", None):
        top = incident.child_incidents[:5]
        lis = "\n".join(f"<li>{esc(child.root_cause)} — {len(child.affected_entities)} affected</li>" for child in top)
        more = ""
        if len(incident.child_incidents) > len(top):
            more = f"<li>...and {len(incident.child_incidents) - len(top)} more</li>"
        children = f"""
<div class="children">
  <strong>Child incidents</strong>
  <ul>{lis}{more}</ul>
</div>
"""
    affected = len(getattr(incident, "affected_entities", []))
    devices = len(getattr(incident, "affected_devices", []))
    gain = getattr(incident, "estimated_score_gain", 0)
    minutes = getattr(incident, "estimated_repair_minutes", 0)

    return f"""
<article class="card root-card searchable" style="--severity:{severity_color(incident.severity)}"
         data-search="{esc(incident.root_cause)} {esc(incident.title)} {esc(incident.category)} {esc(incident.severity)}">
  <h3>{esc(incident.root_cause)}</h3>
  <p class="summary">{esc(incident.title)}</p>
  <div class="badge-row">
    {severity_badge(incident.severity)}
    <span class="badge">{affected} entities</span>
    <span class="badge">{devices} devices</span>
    <span class="badge">+{gain} score</span>
    <span class="badge">~{minutes} min</span>
  </div>
  <div class="progress" title="{affected} affected entities">
    <span style="--width:{min(100, max(4, affected / 2))}%"></span>
  </div>
  <p>{esc(incident.recommendation)}</p>
  {explanation_block(incident)}
  {children}
</article>
"""


def action_row(action) -> str:
    stars = "★" * action.priority + "☆" * max(0, 5 - action.priority)
    return f"""
<tr class="searchable" data-search="{esc(action.title)} {esc(action.reason)}">
  <td>{esc(stars)}</td>
  <td>{esc(action.title)}</td>
  <td>+{esc(action.estimated_score_gain)}</td>
  <td>{esc(action.estimated_repair_minutes)} min</td>
  <td>{esc(action.reason)}</td>
</tr>
"""
