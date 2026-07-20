# Unicode / Encoding Audit

This is an audit only. It does not change project files.

## Text IO calls

Found `136` text/path related lines.

## Potential missing encoding

- `src\hadocs\collectors\homeassistant.py:39` — `        (cache / f"{name}.json").write_text(`
- `src\hadocs\gui\app.py:227` — `                img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")`
- `src\hadocs\gui\app.py:231` — `            img = Image.open(path).convert("RGBA")`
- `src\hadocs\gui\output_actions.py:47` — `        webbrowser.open(path.resolve().as_uri())`
- `src\hadocs\gui\output_actions.py:55` — `        subprocess.Popen(["open", str(path)])`
- `src\hadocs\gui\output_actions.py:58` — `    subprocess.Popen(["xdg-open", str(path)])`
- `tests\test_security.py:7` — `    (tmp_path / ".gitignore").write_text("config.json\nconfig.local.json\n.env\ncache/\noutput/\n*.zip\n")`
- `tools\apply_issue4_step2_areas_report.py:58` — `    TEST.write_text(`
- `tools\audit_unicode_encoding.py:13` — `    ".read_text(",`
- `tools\audit_unicode_encoding.py:14` — `    ".write_text(",`
- `tools\audit_unicode_encoding.py:15` — `    "open(",`
- `tools\audit_unicode_encoding.py:65` — `        return path.read_text(errors="replace")`
- `tools\audit_unicode_encoding.py:94` — `            if (".read_text(" in line or ".write_text(" in line or "open(" in line) and not has_explicit_encoding(line):`
- `tools\cleanup_project.py:68` — `    path.write_text(`
- `tools\fix_logo_and_log_window.py:105` — `                img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")`
- `tools\fix_logo_and_log_window.py:109` — `            img = Image.open(path).convert("RGBA")`

## Mojibake patterns in repository

- `src\hadocs\utils\display.py:10` — `    "_uden_omr├Ñde",`
- `src\hadocs\utils\display.py:14` — `    "uden omr├Ñde",`
- `tests\test_area_filename_display.py:11` — `    assert area_filename("_uden_omr├Ñde", fake_slugify) == "no_area"`
- `tests\test_display_utils.py:7` — `    assert is_unassigned_area("_uden_omr├Ñde")`
- `tools\apply_issue4_step2_areas_report.py:84` — `    print('  findstr /s /i "_uden_område _uden_omraade uden omraade omr├Ñde" output\\04_areas\\*.md')`
- `tools\apply_issue4_step3_area_filename.py:34` — `    assert area_filename("_uden_omr├Ñde", fake_slugify) == "no_area"`
- `tools\audit_unicode_encoding.py:20` — `    "ÔÇö",`
- `tools\audit_unicode_encoding.py:21` — `    "ÔÇô",`
- `tools\audit_unicode_encoding.py:22` — `    "ÔÇó",`
- `tools\audit_unicode_encoding.py:23` — `    "Ô£ô",`
- `tools\audit_unicode_encoding.py:24` — `    "ÔÜí",`
- `tools\audit_unicode_encoding.py:25` — `    "Ôÿà",`
- `tools\audit_unicode_encoding.py:26` — `    "Ôÿå",`
- `tools\audit_unicode_encoding.py:27` — `    "├ª",`
- `tools\audit_unicode_encoding.py:28` — `    "├©",`
- `tools\audit_unicode_encoding.py:29` — `    "├Ñ",`
- `tools\audit_unicode_encoding.py:30` — `    "├å",`
- `tools\audit_unicode_encoding.py:31` — `    "├ÿ",`
- `tools\audit_unicode_encoding.py:32` — `    "├à",`

