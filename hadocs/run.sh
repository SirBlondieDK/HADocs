#!/bin/sh
set -eu

echo "[HADocs] Starting Home Assistant scan"

PROJECT_NAME="$(
python - <<'PY'
import json
from pathlib import Path

path = Path("/data/options.json")
options = {}

if path.exists():
    options = json.loads(path.read_text(encoding="utf-8"))

print(options.get("project_name", "My Smart Home"))
PY
)"

OUTPUT_DIRECTORY="$(
python - <<'PY'
import json
from pathlib import Path

path = Path("/data/options.json")
options = {}

if path.exists():
    options = json.loads(path.read_text(encoding="utf-8"))

print(options.get("output_directory", "/share/hadocs"))
PY
)"

if [ -z "${SUPERVISOR_TOKEN:-}" ]; then
    echo "[HADocs] ERROR: SUPERVISOR_TOKEN is unavailable"
    exit 1
fi

mkdir -p "${OUTPUT_DIRECTORY}"
mkdir -p /data/cache

export HADOCS_HA_URL="http://supervisor/core"
export HADOCS_TOKEN="${SUPERVISOR_TOKEN}"
export HADOCS_PROJECT_NAME="${PROJECT_NAME}"
export HADOCS_OUTPUT_DIR="${OUTPUT_DIRECTORY}"
export HADOCS_CACHE_DIR="/data/cache"
export HADOCS_CONFIG_FILE="/data/config.json"

echo "[HADocs] Project: ${PROJECT_NAME}"
echo "[HADocs] Output: ${OUTPUT_DIRECTORY}"

python -m src.hadocs.cli.main generate

echo "[HADocs] Scan completed successfully"
echo "[HADocs] Reports written to ${OUTPUT_DIRECTORY}"