
from __future__ import annotations

from pathlib import Path

GENERATOR = Path("src/hadocs/reports/generator.py")


def patch_css(text: str) -> str:
    if ".explain-box" in text:
        return text

    css = (
        ".explain-box{margin-top:16px;border:1px solid var(--border);border-radius:16px;"
        "background:#0b1220;padding:14px}"
        ".explain-box summary{cursor:pointer;font-weight:800;color:#e5eefb}"
        ".explain-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}"
        ".explain-item{border:1px solid var(--border);border-radius:14px;background:#0d1424;padding:12px}"
        ".explain-item h4{margin:0 0 6px;font-size:13px;color:#9fc2ff;text-transform:uppercase;letter-spacing:.04em}"
        ".explain-item p{margin:0;color:#cbd5e1;line-height:1.45}"
        "@media(max-width:900px){.explain-grid{grid-template-columns:1fr}}"
    )

    if ".footer{" in text:
        return text.replace(".footer{", css + ".footer{", 1)
    return text.replace("</style>", css + "</style>", 1)


def patch_helper(text: str) -> str:
    if "def explain_root_cause_text" in text:
        return text

    helper = '''
    def explain_root_cause_text(incident):
        root = root_of(incident)
        root_l = str(root).lower()
        entities = len(list_of(get(incident, "affected_entities", [])))
        devices = len(list_of(get(incident, "affected_devices", [])))
        children = get(incident, "child_count", 0)
        gain = get(incident, "estimated_score_gain", 0)
        minutes = get(incident, "estimated_repair_minutes", 5)

        if "mobile" in root_l or "app" in root_l:
            why = "One or more Home Assistant Companion App devices appear offline or have stopped updating."
            verify = "Open the Companion App on the affected devices and confirm that they can reach Home Assistant."
            fix = "Refresh or restart the Companion App, verify network access, and check background update permissions."
        elif "mqtt" in root_l:
            why = "MQTT is a central message bus. When it is unhealthy, many sensors and integrations can become unavailable at once."
            verify = "Open the MQTT integration and broker logs. Confirm clients are connected and messages are flowing."
            fix = "Restart the MQTT broker, verify credentials, and reconnect affected clients."
        elif "frigate" in root_l:
            why = "Frigate provides camera and object-detection entities. If it is unavailable, camera-related entities can fail together."
            verify = "Open Frigate and check service status, logs, camera streams and detector health."
            fix = "Restart Frigate, verify camera streams, and check hardware acceleration or detector availability."
        elif "icloud" in root_l:
            why = "iCloud entities depend on account authentication and cloud availability."
            verify = "Check the iCloud integration for reauthentication prompts or account errors."
            fix = "Reauthenticate iCloud and verify that tracked devices update again."
        elif "tuya" in root_l:
            why = "Tuya devices depend on integration connectivity. Cloud, local network, or pairing issues can affect multiple entities."
            verify = "Check the Tuya integration and confirm affected devices are online in Tuya or on the local network."
            fix = "Reload the Tuya integration, power-cycle affected devices, and verify credentials/connectivity."
        else:
            why = f"HADocs detected that several symptoms point back to the same root cause: {root}."
            verify = "Open the related integration or device in Home Assistant and check logs, availability and recent changes."
            fix = "Fix the parent integration or device first, then rescan to confirm child incidents disappear."

        impact = (
            f"This root cause affects {entities} entities, {devices} devices and has {children} child incidents. "
            f"Fixing it may improve Health Score by +{gain}."
        )
        time = f"Estimated repair time: about {minutes} minutes."
        return why, impact, verify, fix, time

'''

    if "    def render_root_cards" in text:
        return text.replace("    def render_root_cards", helper + "\n    def render_root_cards", 1)

    raise RuntimeError("Could not find render_root_cards in generator.py")


def patch_loop(text: str) -> str:
    if "explain_why, explain_impact, explain_verify, explain_fix, explain_time = explain_root_cause_text(incident)" in text:
        return text

    candidates = [
        "for incident in visible[:18]:\n            sev = severity_of(incident)",
        "for incident in shown[:18]:\n            sev = severity_of(incident)",
        "for incident in incidents[:18]:\n            sev = severity_of(incident)",
    ]

    insert = (
        "for incident in visible[:18]:\n"
        "            explain_why, explain_impact, explain_verify, explain_fix, explain_time = explain_root_cause_text(incident)\n"
        "            sev = severity_of(incident)"
    )

    for candidate in candidates:
        if candidate in text:
            return text.replace(candidate, insert if "visible[:18]" in candidate else insert.replace("visible[:18]", candidate.split(" in ")[1].split(":")[0]), 1)

    raise RuntimeError("Could not find root card incident loop")


def patch_card(text: str) -> str:
    if "Explain this</summary>" in text:
        return text

    explain_html = '''
              <details class="explain-box">
                <summary>Explain this</summary>
                <div class="explain-grid">
                  <div class="explain-item">
                    <h4>Why this happened</h4>
                    <p>{esc(explain_why)}</p>
                  </div>
                  <div class="explain-item">
                    <h4>Impact</h4>
                    <p>{esc(explain_impact)}</p>
                  </div>
                  <div class="explain-item">
                    <h4>How to verify</h4>
                    <p>{esc(explain_verify)}</p>
                  </div>
                  <div class="explain-item">
                    <h4>Suggested fix</h4>
                    <p>{esc(explain_fix)}</p>
                  </div>
                </div>
                <p class="muted">{esc(explain_time)}</p>
              </details>
'''

    if "{child_html}" in text:
        return text.replace("{child_html}", explain_html + "\n              {child_html}", 1)

    return text.replace("            </article>", explain_html + "\n            </article>", 1)


def main() -> None:
    if not GENERATOR.exists():
        raise SystemExit("Run this from the repository root, e.g. C:\\HomeAssistantDocs")

    text = GENERATOR.read_text(encoding="utf-8")
    text = patch_css(text)
    text = patch_helper(text)
    text = patch_loop(text)
    text = patch_card(text)
    GENERATOR.write_text(text, encoding="utf-8")

    print("Explain This fix applied.")
    print("Run: py -3.14 -m pytest")
    print("Run: py -3.14 main.py")
    print("Then open output/index.html and expand a Root Cause card.")
    print('Commit: git add src/hadocs/reports/generator.py docs/V014_EXPLAIN_THIS_FIX.md tools/apply_v014_explain_this_fix.py')
    print('Commit: git commit -m "Add Explain This to root cause cards"')
    print("Push: git push")


if __name__ == "__main__":
    main()
