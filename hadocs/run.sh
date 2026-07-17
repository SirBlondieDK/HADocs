#!/bin/sh
set -eu

echo "[HADocs] Starting Home Assistant application"

eval "$(
python - <<'PY'
import json
import shlex
from pathlib import Path

path = Path("/data/options.json")
options = {}

if path.exists():
    options = json.loads(path.read_text(encoding="utf-8"))

project_name = options.get("project_name", "My Smart Home")
output_directory = options.get("output_directory", "/share/hadocs")

print(f"PROJECT_NAME={shlex.quote(str(project_name))}")
print(f"OUTPUT_DIRECTORY={shlex.quote(str(output_directory))}")
PY
)"

if [ -z "${SUPERVISOR_TOKEN:-}" ]; then
    echo "[HADocs] ERROR: SUPERVISOR_TOKEN is unavailable"
    exit 1
fi

mkdir -p "${OUTPUT_DIRECTORY}" /data/cache /config

export HADOCS_HA_URL="http://supervisor/core"
export HADOCS_TOKEN="${SUPERVISOR_TOKEN}"
export HADOCS_PROJECT_NAME="${PROJECT_NAME}"
export HADOCS_OUTPUT_DIR="${OUTPUT_DIRECTORY}"
export HADOCS_CACHE_DIR="/data/cache"
export HADOCS_CONFIG_FILE="/data/config.json"

echo "[HADocs] Project: ${PROJECT_NAME}"
echo "[HADocs] Output: ${OUTPUT_DIRECTORY}"
echo "[HADocs] Starting web application on port 8099"

exec python -m src.hadocs.web.app