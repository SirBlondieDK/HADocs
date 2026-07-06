from __future__ import annotations

from pathlib import Path

GENERATOR = Path("src/hadocs/reports/generator.py")


def patch_css(text: str) -> str:
    if ".explain-box" in text:
        return text

    css = (
        ".explain-box{margin-top:16px;border:1px solid var(--border);border-radius:16px;"
        "background:#0b1220;padding:14px}"
        ".explain-box summary{cursor:pointer;font-weight:900;color:#e5eefb}"
        ".explain-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}"
        ".explain-item{border:1px solid var(--border);border-radius:14px;background:#0d1424;padding:12px}"
        ".explain-item h4{margin:0 0 6px;font-size:12px;color:#9fc2ff;text-transform:uppercase;letter-spacing:.04em}"
        ".explain-item p{margin:0;color:#cbd5e1;line-height:1.45}"
        "@media(max-width:900px){.explain-grid{grid-template-columns:1fr}}"
    )

    if ".footer{" in text:
        return text.replace(".footer{", css + ".footer{", 1)
    if "</style>" in text:
        return text.replace("</style>", css + "</style>", 1)
    return text


def patch_root_cards(text: str) -> str:
    if "Explain this</summary>" in text:
        return text

    old = """              <p>{esc(reason_of(incident))}</p>
              {child_html}
              {entity_html}
            </article>"""

    new = """              <p>{esc(reason_of(incident))}</p>

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
            </article>"""

    if old not in text:
        raise RuntimeError("Could not find current root-card HTML block. The generator.py layout has changed.")

    return text.replace(old, new, 1)


def main() -> None:
    if not GENERATOR.exists():
        raise SystemExit("Run from repository root, e.g. C:\\HomeAssistantDocs")

    text = GENERATOR.read_text(encoding="utf-8")
    text = patch_css(text)
    text = patch_root_cards(text)
    GENERATOR.write_text(text, encoding="utf-8")

    print("Direct Explain This patch applied.")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  py -3.14 main.py")
    print("")
    print("Then open output/index.html and expand Explain this on a Root Cause card.")
    print("")
    print("Commit:")
    print("  git add src/hadocs/reports/generator.py docs/V014_EXPLAIN_THIS_DIRECT_FIX.md tools/apply_v014_explain_this_direct_fix.py")
    print('  git commit -m "Show Explain This on root cause cards"')
    print("  git push")


if __name__ == "__main__":
    main()
