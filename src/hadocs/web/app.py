from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


from src.hadocs.core.device_overrides import (
    device_override_to_mapping,
    load_device_overrides_file,
    override_from_mapping,
    remove_device_override,
    resolve_device_overrides_file,
    upsert_device_override,
)
from src.hadocs.utils.config import load_config
from src.hadocs.web.api.devices import load_device_summaries

HOST = "0.0.0.0"
PORT = 8099

OUTPUT_DIRECTORY = Path(
    os.environ.get("HADOCS_OUTPUT_DIR", "/share/hadocs")
).resolve()

OPTIONS_FILE = Path("/data/options.json")

WEB_DIRECTORY = Path(__file__).resolve().parent
STATIC_DIRECTORY = WEB_DIRECTORY / "static"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_addon_options() -> dict[str, Any]:
    if not OPTIONS_FILE.exists():
        return {}

    try:
        data = json.loads(OPTIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


class ScanManager:
    """Run one HADocs scan at a time and retain its current status and log."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._started_at: str | None = None
        self._finished_at: str | None = None
        self._exit_code: int | None = None
        self._error: str | None = None
        self._log_lines: list[str] = []

    def status(self) -> dict[str, Any]:
        with self._lock:
            report_available = (OUTPUT_DIRECTORY / "index.html").is_file()

            return {
                "running": self._running,
                "started_at": self._started_at,
                "finished_at": self._finished_at,
                "exit_code": self._exit_code,
                "error": self._error,
                "report_available": report_available,
                "output_directory": str(OUTPUT_DIRECTORY),
            }

    def logs(self) -> list[str]:
        with self._lock:
            return list(self._log_lines)

    def start(self) -> bool:
        with self._lock:
            if self._running:
                return False

            self._running = True
            self._started_at = utc_now()
            self._finished_at = None
            self._exit_code = None
            self._error = None
            self._log_lines = [
                f"[{self._started_at}] Starting HADocs scan..."
            ]

        thread = threading.Thread(
            target=self._run,
            name="hadocs-scan",
            daemon=True,
        )
        thread.start()
        return True

    def _append_log(self, line: str) -> None:
        with self._lock:
            self._log_lines.append(line.rstrip())

            # Prevent an indefinitely growing in-memory log.
            if len(self._log_lines) > 2000:
                self._log_lines = self._log_lines[-2000:]

    def _run(self) -> None:
        exit_code = 1
        error: str | None = None

        try:
            OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "src.hadocs.cli.main",
                    "generate",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=os.environ.copy(),
            )

            if process.stdout is not None:
                for line in process.stdout:
                    self._append_log(line)

            exit_code = process.wait()

            if exit_code == 0:
                self._append_log("HADocs scan completed successfully.")
            else:
                self._append_log(
                    f"HADocs scan failed with exit code {exit_code}."
                )

        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            self._append_log(f"Scan error: {error}")

        finally:
            with self._lock:
                self._running = False
                self._finished_at = utc_now()
                self._exit_code = exit_code
                self._error = error


SCAN_MANAGER = ScanManager()


class HadocsRequestHandler(BaseHTTPRequestHandler):
    server_version = "HADocsWeb/0.4.0"

    def do_GET(self) -> None:
        path = self._request_path()

        if path in {"", "/"}:
            self._serve_web_file("index.html")
            return

        if path.startswith("/static/"):
            relative_name = path.removeprefix("/static/")
            self._serve_web_file(relative_name)
            return

        if path == "/api/status":
            self._send_json(SCAN_MANAGER.status())
            return

        if path == "/api/logs":
            self._send_json({"logs": SCAN_MANAGER.logs()})
            return

        if path == "/api/health":
            self._send_json({"status": "ok"})
            return

        if path == "/api/summary":
            self._send_json(self._load_report_summary())
            return

        if path == "/api/device-overrides":
            try:
                self._send_json(self._load_device_overrides())
            except (OSError, ValueError) as exc:
                self._send_json(
                    {"error": f"Unable to load device overrides: {exc}"},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )
            return

        if path == "/api/devices":
            self._send_json({"devices": self._load_devices()})
            return

        if path == "/report":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "./report/index.html")
            self.end_headers()
            return

        if path.startswith("/report/"):
            self._serve_report_file(path)
            return

        self._send_json(
            {"error": "Not found"},
            status=HTTPStatus.NOT_FOUND,
        )

    def do_POST(self) -> None:
        path = self._request_path()

        if path == "/api/scan":
            if not SCAN_MANAGER.start():
                self._send_json(
                    {
                        "error": "A scan is already running",
                        "status": SCAN_MANAGER.status(),
                    },
                    status=HTTPStatus.CONFLICT,
                )
                return

            self._send_json(
                {
                    "message": "Scan started",
                    "status": SCAN_MANAGER.status(),
                },
                status=HTTPStatus.ACCEPTED,
            )
            return

        if path == "/api/device-overrides":
            try:
                payload = self._read_json_body()
                override = override_from_mapping(payload)
                override_file = resolve_device_overrides_file(load_config())
                overrides = upsert_device_override(override_file, override)
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                self._send_json(
                    {"error": f"Unable to save Device Override: {exc}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            self._send_json(
                {
                    "message": "Device Override saved",
                    "count": len(overrides),
                    "override": device_override_to_mapping(override),
                },
                status=HTTPStatus.OK,
            )
            return

        self._send_json(
            {"error": "Not found"},
            status=HTTPStatus.NOT_FOUND,
        )

    def do_DELETE(self) -> None:
        path = self._request_path()
        prefix = "/api/device-overrides/"

        if not path.startswith(prefix):
            self._send_json(
                {"error": "Not found"},
                status=HTTPStatus.NOT_FOUND,
            )
            return

        device_id = unquote(path.removeprefix(prefix)).strip()
        if not device_id:
            self._send_json(
                {"error": "Missing device ID"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            override_file = resolve_device_overrides_file(load_config())
            before = load_device_overrides_file(override_file)
            existed = any(item.device_id == device_id for item in before)
            overrides = remove_device_override(override_file, device_id)
        except (OSError, ValueError) as exc:
            self._send_json(
                {"error": f"Unable to delete Device Override: {exc}"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        if not existed:
            self._send_json(
                {"error": "Device Override not found"},
                status=HTTPStatus.NOT_FOUND,
            )
            return

        self._send_json(
            {
                "message": "Device Override deleted",
                "count": len(overrides),
                "device_id": device_id,
            }
        )

    def log_message(self, format: str, *args: object) -> None:
        print(
            f"[HADocs Web] {self.address_string()} "
            f"- {format % args}",
            flush=True,
        )

    def _request_path(self) -> str:
        path = urlparse(self.path).path
        return unquote(path).rstrip("/") or "/"


    def _load_report_summary(self) -> dict[str, Any]:
        knowledge_directory = OUTPUT_DIRECTORY / "knowledge"

        def read_json(name: str, fallback: Any) -> Any:
            path = knowledge_directory / name
            if not path.is_file():
                return fallback
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return fallback

        health = read_json("health.json", {})
        inventory = read_json("inventory.json", {})
        incidents = read_json("incidents.json", [])
        recommendations = read_json("recommendations.json", [])

        return {
            "available": (OUTPUT_DIRECTORY / "index.html").is_file(),
            "health": health if isinstance(health, dict) else {},
            "inventory": inventory if isinstance(inventory, dict) else {},
            "incidents": incidents if isinstance(incidents, list) else [],
            "recommendations": (
                recommendations if isinstance(recommendations, list) else []
            ),
        }

    def _read_json_body(self) -> dict[str, Any]:
        content_length = self.headers.get("Content-Length", "0")
        try:
            length = int(content_length)
        except ValueError as exc:
            raise ValueError("Invalid Content-Length") from exc

        if length <= 0:
            raise ValueError("Request body is empty")
        if length > 1_000_000:
            raise ValueError("Request body is too large")

        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _load_devices(self) -> list[dict[str, Any]]:
        """Return devices using the stable DeviceSummary API contract."""
        index_path = OUTPUT_DIRECTORY / "explorer" / "search_index.json"
        return load_device_summaries(index_path)

    def _load_device_overrides(self) -> dict[str, Any]:
        """Load overrides and enrich device IDs with names from the latest scan."""
        config = load_config()
        override_file = resolve_device_overrides_file(config)
        overrides = load_device_overrides_file(override_file)
        device_names = self._load_device_names()

        items: list[dict[str, Any]] = []
        for override in overrides:
            item = device_override_to_mapping(override)
            device_id = str(item.get("device_id") or "")
            if not item.get("device_name") and device_id in device_names:
                item["device_name"] = device_names[device_id]
            items.append(item)

        return {
            "file": str(override_file),
            "count": len(items),
            "overrides": items,
        }

    def _load_device_names(self) -> dict[str, str]:
        """Return device ID -> friendly name from Explorer's generated index."""
        index_path = OUTPUT_DIRECTORY / "explorer" / "search_index.json"
        if not index_path.is_file():
            return {}

        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

        if not isinstance(payload, list):
            return {}

        result: dict[str, str] = {}
        for item in payload:
            if not isinstance(item, dict) or item.get("type") != "device":
                continue
            device_id = str(item.get("id") or "").strip()
            title = str(item.get("title") or "").strip()
            if device_id and title:
                result[device_id] = title
        return result

    def _serve_web_file(self, relative_name: str) -> None:
        requested_file = (STATIC_DIRECTORY / relative_name).resolve()

        try:
            requested_file.relative_to(STATIC_DIRECTORY)
        except ValueError:
            self._send_json(
                {"error": "Invalid static file path"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        if not requested_file.is_file():
            self._send_json(
                {"error": "Static file not found"},
                status=HTTPStatus.NOT_FOUND,
            )
            return

        try:
            content = requested_file.read_bytes()
        except OSError as exc:
            self._send_json(
                {"error": f"Unable to read static file: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        content_type = self._content_type(requested_file.suffix.lower())

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _serve_report_file(self, request_path: str) -> None:
        relative_name = request_path.removeprefix("/report/")
        requested_file = (OUTPUT_DIRECTORY / relative_name).resolve()

        try:
            requested_file.relative_to(OUTPUT_DIRECTORY)
        except ValueError:
            self._send_json(
                {"error": "Invalid report path"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        if requested_file.is_dir():
            requested_file = requested_file / "index.html"

        if not requested_file.is_file():
            self._send_json(
                {"error": "Report file not found"},
                status=HTTPStatus.NOT_FOUND,
            )
            return

        content_type = self._content_type(requested_file.suffix.lower())

        try:
            content = requested_file.read_bytes()
        except OSError as exc:
            self._send_json(
                {"error": f"Unable to read report: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    @staticmethod
    def _content_type(suffix: str) -> str:
        return {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".md": "text/markdown; charset=utf-8",
            ".csv": "text/csv; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".ico": "image/x-icon",
        }.get(suffix, "application/octet-stream")

    def _send_json(
        self,
        payload: dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)


def main() -> int:
    options = load_addon_options()
    scan_on_start = bool(options.get("scan_on_start", False))

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer(
        (HOST, PORT),
        HadocsRequestHandler,
    )

    print(
        f"[HADocs] Web application listening on {HOST}:{PORT}",
        flush=True,
    )
    print(
        f"[HADocs] Report directory: {OUTPUT_DIRECTORY}",
        flush=True,
    )

    if scan_on_start:
        print("[HADocs] scan_on_start enabled", flush=True)
        SCAN_MANAGER.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())