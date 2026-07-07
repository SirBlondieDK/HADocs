from __future__ import annotations

from pathlib import Path
import base64

GENERATOR = Path("src/hadocs/reports/generator.py")
TEST = Path("tests/test_areas_report_display.py")
DOC = Path("docs/ISSUE_4_STEP2_AREAS_REPORT.md")

DOC_TEXT = base64.b64decode("IyBJc3N1ZSAjNCBTdGVwIDI6IEFyZWFzIFJlcG9ydCBQcmVzZW50YXRpb24KClVzZXMgYGRpc3BsYXlfYXJlYSgpYCBvbmx5IGluIGBnZW5lcmF0ZV9hcmVhcygpYC4KClRoaXMga2VlcHMgaW50ZXJuYWwgYXJlYSBJRHMsIGZpbGVuYW1lcywgc2x1Z2lmeSwgbW9kZWwgZGF0YSwgSGVhbHRoIEVuZ2luZSwgR1VJLCBhbmQgRGFzaGJvYXJkIHVudG91Y2hlZC4KCiMjIFRlc3QKCmBgYHBvd2Vyc2hlbGwKcHkgLTMuMTQgdG9vbHMvYXBwbHlfaXNzdWU0X3N0ZXAyX2FyZWFzX3JlcG9ydC5weQpweSAtMy4xNCAtbSBweXRlc3QKcm1kaXIgL3MgL3Egb3V0cHV0CnB5IC0zLjE0IG1haW4ucHkgZ2VuZXJhdGUKZmluZHN0ciAvcyAvaSAiX3VkZW5fb21yw6VkZSBfdWRlbl9vbXJhYWRlIHVkZW4gb21yYWFkZSBvbXLilJzDkWRlIiBvdXRwdXRcMDRfYXJlYXNcKi5tZApgYGAK").decode("utf-8")


def ensure_import(text: str) -> str:
    import_line = "from src.hadocs.utils.display import display_area\n"
    if import_line in text:
        return text

    lines = text.splitlines(True)
    pos = 0
    for i, line in enumerate(lines[:80]):
        if line.startswith("import ") or line.startswith("from "):
            pos = i + 1
    lines.insert(pos, import_line)
    return "".join(lines)


def patch_generate_areas(text: str) -> str:
    marker = "def generate_areas(out, model, now):"
    if marker not in text:
        raise SystemExit("Could not find generate_areas() in generator.py")

    start = text.index(marker)
    end = text.find("\ndef ", start + 1)
    if end == -1:
        end = len(text)

    block = text[start:end]

    block = block.replace(
        "for area in sorted(model.areas.values(), key=lambda a: a.name):",
        "for area in sorted(model.areas.values(), key=lambda a: display_area(a.name)):",
    )

    block = block.replace(
        'index.append(f"- [{area.name}]({filename}) — {len(area.devices)} devices, {len(area.entities)} entities")',
        'index.append(f"- [{display_area(area.name)}]({filename}) — {len(area.devices)} devices, {len(area.entities)} entities")',
    )

    block = block.replace(
        'lines = [f"# {area.name}", "", f"Generated: {now}", "", "## Devices", ""]',
        'lines = [f"# {display_area(area.name)}", "", f"Generated: {now}", "", "## Devices", ""]',
    )

    return text[:start] + block + text[end:]


def write_test() -> None:
    TEST.write_text(
        'from src.hadocs.utils.display import display_area\n\n\n'
        'def test_area_report_display_formatter_is_available():\n'
        '    assert display_area("_uden_område") == "No Area Assigned"\n',
        encoding="utf-8",
    )


def main() -> None:
    if not GENERATOR.exists():
        raise SystemExit("Run from repository root: C:\\HomeAssistantDocs")

    text = GENERATOR.read_text(encoding="utf-8")
    text = ensure_import(text)
    text = patch_generate_areas(text)
    GENERATOR.write_text(text, encoding="utf-8")

    write_test()
    DOC.write_text(DOC_TEXT, encoding="utf-8")

    print("Issue #4 step 2 applied: Areas report uses display_area().")
    print("")
    print("Run:")
    print("  py -3.14 -m pytest")
    print("  rmdir /s /q output")
    print("  py -3.14 main.py generate")
    print('  findstr /s /i "_uden_område _uden_omraade uden omraade omr├Ñde" output\\04_areas\\*.md')
    print("")
    print("Commit if green:")
    print("  git add src/hadocs/reports/generator.py tests/test_areas_report_display.py docs/ISSUE_4_STEP2_AREAS_REPORT.md tools/apply_issue4_step2_areas_report.py")
    print('  git commit -m "Use display formatter in areas report"')


if __name__ == "__main__":
    main()
