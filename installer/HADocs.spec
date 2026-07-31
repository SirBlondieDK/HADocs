# HADocs PyInstaller spec
# Run from repository root:
# py -3.14 -m PyInstaller installer/HADocs.spec --clean --noconfirm

from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "src"
MAIN = ROOT / "main.py"

if not MAIN.exists():
    raise FileNotFoundError(f"main.py not found at {MAIN}. Run PyInstaller from the repository root.")

datas = []
for migration in sorted((SRC / "hadocs" / "hask_database" / "sql").glob("*.sql")):
    datas.append((str(migration), "hadocs/hask_database/sql"))

for source, destination in (
    (SRC / "hadocs" / "hudd" / "data" / "hudd.sqlite", "hadocs/hudd/data"),
    (SRC / "hadocs" / "hudd" / "data" / "masterlist.txt", "hadocs/hudd/data"),
    (SRC / "hadocs" / "hudd" / "schema" / "schema.sql", "hadocs/hudd/schema"),
):
    datas.append((str(source), destination))

for migration in sorted((SRC / "hadocs" / "hudd" / "migrations").glob("*.sql")):
    datas.append((str(migration), "hadocs/hudd/migrations"))

for artifact in sorted((SRC / "hadocs" / "knowledge" / "hask_bundle" / "0.2.0").glob("*.json")):
    datas.append((str(artifact), "hadocs/knowledge/hask_bundle/0.2.0"))

for asset in sorted((SRC / "hadocs" / "web" / "static").glob("*")):
    if asset.is_file():
        datas.append((str(asset), "hadocs/web/static"))

# Include project package explicitly for reliability.
pathex = [str(SRC)]

a = Analysis(
    [str(MAIN)],
    pathex=pathex,
    binaries=[],
    datas=datas,
    hiddenimports=[
        "hadocs",
        "hadocs.cli.main",
        "hadocs.application.database_status",
        "hadocs.application.operational_database",
        "hadocs.application.hask_preview",
        "hadocs.hask_database",
        "hadocs.gui.app",
        "hadocs.gui.modern_app",
        "hadocs.gui.output_actions",
        "hadocs.api.client",
        "hadocs.reports.generator",
        "hadocs.html.explorer",
        "hadocs.knowledge.exporter",
        "hadocs.explain.engine",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "tests",
        "hadocs.metadata_collector",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

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
    console=True,
    disable_windowed_traceback=False,
    icon=None,
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
