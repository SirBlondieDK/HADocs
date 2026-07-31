#!/bin/sh
set -eu

echo "[HADocs] Starting Home Assistant application"

eval "$(
python - <<'PY'
import json
import shlex
from pathlib import Path, PurePosixPath

path = Path("/data/options.json")
options = {}

if path.exists():
    options = json.loads(path.read_text(encoding="utf-8"))

project_name = options.get("project_name", "My Smart Home")
output_directory = options.get("output_directory", "/share/hadocs")

def boolean_option(name, default=False):
    value = options.get(name, default)
    if not isinstance(value, bool):
        raise SystemExit(f"[HADocs] ERROR: {name} must be true or false")
    return "true" if value else "false"

def persistent_path_option(name, default):
    value = options.get(name, default)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"[HADocs] ERROR: {name} must be a non-empty path")
    candidate = PurePosixPath(value.strip())
    if not candidate.is_absolute() or PurePosixPath("/config") not in candidate.parents:
        raise SystemExit(f"[HADocs] ERROR: {name} must be under /config")
    if ".." in candidate.parts:
        raise SystemExit(f"[HADocs] ERROR: {name} must not traverse parents")
    return str(candidate)

installation_ref = options.get(
    "hask_database_installation_ref", "home-assistant-app"
)
if not isinstance(installation_ref, str) or not installation_ref.strip():
    raise SystemExit(
        "[HADocs] ERROR: hask_database_installation_ref must be non-empty text"
    )

print(f"PROJECT_NAME={shlex.quote(str(project_name))}")
print(f"OUTPUT_DIRECTORY={shlex.quote(str(output_directory))}")
print(
    "DATABASE_INITIALIZE="
    + boolean_option("hask_database_initialize")
)
print(
    "DATABASE_ENABLED="
    + boolean_option("hask_database_enabled")
)
print(
    "DATABASE_PATH="
    + shlex.quote(
        persistent_path_option("hask_database_path", "/config/hadocs.db")
    )
)
print(f"DATABASE_INSTALLATION_REF={shlex.quote(installation_ref.strip())}")
print("HASK_ENABLED=" + boolean_option("hask_enabled"))
print("HASK_PREVIEW_ENABLED=" + boolean_option("hask_preview_enabled"))
print(
    "HASK_BUNDLE_PATH="
    + shlex.quote(
        persistent_path_option("hask_bundle_path", "/config/hask-bundle")
    )
)
print(
    "HASK_CANDIDATE_EVIDENCE_ENABLED="
    + boolean_option("hask_candidate_evidence_enabled")
)
print(
    "HASK_NATIVE_INTEGRATION_STATUS_ENABLED="
    + boolean_option("hask_native_integration_status_enabled")
)
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
export HADOCS_HASK_DATABASE_ENABLED="${DATABASE_ENABLED}"
export HADOCS_HASK_DATABASE_PATH="${DATABASE_PATH}"
export HADOCS_HASK_DATABASE_INSTALLATION_REF="${DATABASE_INSTALLATION_REF}"
export HADOCS_HASK_DATABASE_SECRET_BACKEND="posix_file"
export HADOCS_HASK_CREDENTIAL_STORE_PATH="/config/.hadocs/credentials"
export HADOCS_HASK_ENABLED="${HASK_ENABLED}"
export HADOCS_HASK_PREVIEW_ENABLED="${HASK_PREVIEW_ENABLED}"
export HADOCS_HASK_BUNDLE_PATH="${HASK_BUNDLE_PATH}"
export HADOCS_HASK_CANDIDATE_EVIDENCE_ENABLED="${HASK_CANDIDATE_EVIDENCE_ENABLED}"
export HADOCS_HASK_NATIVE_INTEGRATION_STATUS_ENABLED="${HASK_NATIVE_INTEGRATION_STATUS_ENABLED}"

if [ "${DATABASE_INITIALIZE}" = "true" ]; then
    echo "[HADocs] Validating operational database identity initialization"
    hadocs database init
fi

echo "[HADocs] Project: ${PROJECT_NAME}"
echo "[HADocs] Output: ${OUTPUT_DIRECTORY}"
echo "[HADocs] Starting web application on port 8099"

exec python -m hadocs.web.app
