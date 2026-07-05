import json
from pathlib import Path
import html

from src.hadocs.explorer.builder import build_explorer_data, build_search_index


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def explorer_css() -> str:
    return """
:root{--bg:#0b1020;--panel:#111827;--panel2:#172033;--text:#e5e7eb;--muted:#9ca3af;--border:#263244;--blue:#38bdf8;--purple:#a78bfa}
*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,system-ui,sans-serif;background:var(--bg);color:var(--text)}
.layout{display:grid;grid-template-columns:250px 1fr;min-height:100vh}
aside{border-right:1px solid var(--border);background:rgba(17,24,39,.85);padding:28px 20px;position:sticky;top:0;height:100vh}
.logo{width:42px;height:42px;border-radius:14px;background:linear-gradient(135deg,var(--blue),var(--purple));display:grid;place-items:center;font-weight:800}
.brand{display:flex;gap:12px;align-items:center;margin-bottom:28px}.brand h1{font-size:20px;margin:0}.brand p{font-size:12px;color:var(--muted);margin:2px 0 0}
nav a{display:block;color:var(--text);text-decoration:none;padding:11px 12px;border-radius:12px;margin:6px 0}nav a:hover,nav a.active{background:var(--panel2)}
main{padding:32px;max-width:1500px}.card{background:linear-gradient(180deg,rgba(23,32,51,.92),rgba(17,24,39,.92));border:1px solid var(--border);border-radius:22px;padding:22px;margin-bottom:20px}
h1{font-size:42px;margin:0 0 10px}.muted{color:var(--muted);line-height:1.55}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.metric{background:rgba(11,16,32,.55);border:1px solid var(--border);border-radius:18px;padding:16px}.metric .value{font-size:30px;font-weight:800}.metric .label{color:var(--muted);font-size:13px}
.search{width:100%;padding:14px 16px;border-radius:16px;background:rgba(11,16,32,.72);border:1px solid var(--border);color:var(--text);font-size:15px;margin-bottom:16px}
table{width:100%;border-collapse:collapse}th,td{padding:12px 14px;border-bottom:1px solid var(--border);text-align:left;font-size:14px}th{color:var(--muted)}
.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:rgba(255,255,255,.08);border:1px solid var(--border);color:var(--muted);font-size:12px}
.footer{color:var(--muted);font-size:13px;margin-top:30px}@media(max-width:1000px){.layout{grid-template-columns:1fr}aside{height:auto;position:relative}.grid{grid-template-columns:1fr}}
"""


def layout(title: str, active: str, body: str) -> str:
    links = [
        ("index.html", "Explorer", "dashboard"),
        ("devices.html", "Devices", "devices"),
        ("integrations.html", "Integrations", "integrations"),
        ("areas.html", "Areas", "areas"),
        ("entities.html", "Entities", "entities"),
        ("../index.html", "Main Dashboard", "main"),
    ]
    nav = "".join(
        f'<a class="{"active" if key == active else ""}" href="{href}">{label}</a>'
        for href, label, key in links
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{esc(title)} - HADocs Explorer</title><meta name="viewport" content="width=device-width, initial-scale=1">
<style>{explorer_css()}</style></head><body><div class="layout"><aside>
<div class="brand"><div class="logo">HA</div><div><h1>HADocs</h1><p>Explorer</p></div></div><nav>{nav}</nav>
</aside><main>{body}<p class="footer">Generated locally by HADocs Explorer. No cloud. No telemetry. No external scripts.</p></main></div>
<script>
const search=document.querySelector('#search');if(search){{search.addEventListener('input',()=>{{const q=search.value.toLowerCase().trim();document.querySelectorAll('[data-search]').forEach(row=>{{const text=(row.dataset.search||row.textContent||'').toLowerCase();row.style.display=!q||text.includes(q)?'':'none';}});}});}}
</script></body></html>"""


def metric(label, value):
    return f'<div class="metric"><div class="value">{esc(value)}</div><div class="label">{esc(label)}</div></div>'


def render_index(data: dict) -> str:
    c = data["counts"]
    body = f"""<section class="card"><h1>Explorer</h1><p class="muted">Browse your Home Assistant installation as a local documentation portal.</p>
<div class="grid">{metric("Devices", c["devices"])}{metric("Entities", c["entities"])}{metric("Integrations", c["integrations"])}{metric("Areas", c["areas"])}</div></section>
<section class="card"><h2>Start exploring</h2><p class="muted">Use the sidebar to browse devices, integrations, areas and entities. This is the foundation for future clickable relationship pages.</p></section>"""
    return layout("Explorer", "dashboard", body)


def table_page(title: str, active: str, headers: list[str], rows: list[list[str]]) -> str:
    header_html = "".join(f"<th>{esc(h)}</th>" for h in headers)
    row_html = ""
    for row in rows:
        search_text = " ".join(str(x) for x in row)
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        row_html += f'<tr data-search="{esc(search_text)}">{cells}</tr>\n'
    body = f"""<section class="card"><h1>{esc(title)}</h1><p class="muted">Search and browse {esc(title.lower())}.</p>
<input id="search" class="search" placeholder="Search {esc(title.lower())}...">
<table><thead><tr>{header_html}</tr></thead><tbody>{row_html}</tbody></table></section>"""
    return layout(title, active, body)


def render_devices(data):
    rows = [[esc(d["name"]), f'<span class="badge">{esc(d["classification"])}</span>', esc(d["manufacturer"]), esc(d["model"]), esc(d["area_id"]), str(d["entity_count"])] for d in data["devices"]]
    return table_page("Devices", "devices", ["Name", "Type", "Manufacturer", "Model", "Area", "Entities"], rows)


def render_integrations(data):
    rows = [[esc(i["name"]), str(i["device_count"]), str(i["entity_count"])] for i in data["integrations"]]
    return table_page("Integrations", "integrations", ["Integration", "Devices", "Entities"], rows)


def render_areas(data):
    rows = [[esc(a["name"]), esc(a["id"]), str(a["device_count"]), str(a["entity_count"])] for a in data["areas"]]
    return table_page("Areas", "areas", ["Area", "ID", "Devices", "Entities"], rows)


def render_entities(data):
    rows = [[f'<code>{esc(e["id"])}</code>', esc(e["name"]), esc(e["domain"]), esc(e["state"]), esc(e["platform"]), f'<span class="badge">{esc(e["importance"])}</span>'] for e in data["entities"][:2500]]
    return table_page("Entities", "entities", ["Entity ID", "Name", "Domain", "State", "Platform", "Importance"], rows)


def write_explorer(out: Path, model, graph=None) -> None:
    explorer_dir = out / "explorer"
    explorer_dir.mkdir(parents=True, exist_ok=True)
    data = build_explorer_data(model, graph)
    search_index = build_search_index(data)
    (explorer_dir / "index.html").write_text(render_index(data), encoding="utf-8")
    (explorer_dir / "devices.html").write_text(render_devices(data), encoding="utf-8")
    (explorer_dir / "integrations.html").write_text(render_integrations(data), encoding="utf-8")
    (explorer_dir / "areas.html").write_text(render_areas(data), encoding="utf-8")
    (explorer_dir / "entities.html").write_text(render_entities(data), encoding="utf-8")
    (explorer_dir / "search_index.json").write_text(json.dumps(search_index, indent=2, ensure_ascii=False), encoding="utf-8")
