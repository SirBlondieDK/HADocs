# HADocs PyInstaller spec
# Run from repository root:
# py -3.14 -m PyInstaller installer/HADocs.spec --clean --noconfirm

from pathlib import Path

ROOT = Path.cwd()
MAIN = ROOT / "main.py"

if not MAIN.exists():
    raise FileNotFoundError(f"main.py not found at {MAIN}. Run PyInstaller from the repository root.")

datas = []

for optional in ["docs", "README.md", "LICENSE", "config.example"]:
    p = ROOT / optional
    if p.exists():
        datas.append((str(p), optional if p.is_dir() else "."))

# Include project package explicitly for reliability.
pathex = [str(ROOT)]

a = Analysis(
    [str(MAIN)],
    pathex=pathex,
    binaries=[],
    datas=datas,
    hiddenimports=[
        "src",
        "src.hadocs",
        "src.hadocs.gui.app",
        "src.hadocs.gui.modern_app",
        "src.hadocs.gui.output_actions",
        "src.hadocs.api.client",
        "src.hadocs.reports.generator",
        "src.hadocs.html.explorer",
        "src.hadocs.knowledge.exporter",
        "src.hadocs.explain.engine",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "tests",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

icon_path = ROOT / "docs" / "images" / "icon.ico"
icon_arg = str(icon_path) if icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HADocs",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=icon_arg,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="HADocs",
)
