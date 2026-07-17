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


HOST = "0.0.0.0"
PORT = 8099

OUTPUT_DIRECTORY = Path(
    os.environ.get("HADOCS_OUTPUT_DIR", "/share/hadocs")
).resolve()

OPTIONS_FILE = Path("/data/options.json")


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


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <title>HADocs</title>
    <style>
        :root {
            color-scheme: light dark;
            font-family:
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }

        body {
            margin: 0;
            padding: 24px;
            background: var(--primary-background-color, #111827);
            color: var(--primary-text-color, #f3f4f6);
        }

        main {
            width: min(900px, 100%);
            margin: 0 auto;
        }

        .header {
            margin-bottom: 24px;
        }

        .header h1 {
            margin: 0 0 6px;
        }

        .muted {
            opacity: 0.72;
        }

        .grid {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }

        .card {
            padding: 18px;
            border: 1px solid rgba(127, 127, 127, 0.3);
            border-radius: 14px;
            background: rgba(127, 127, 127, 0.08);
        }

        .card h2 {
            margin-top: 0;
            font-size: 1rem;
        }

        .value {
            margin: 8px 0 0;
            font-size: 1.25rem;
            font-weight: 700;
        }

        .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 20px;
        }

        button,
        .button {
            box-sizing: border-box;
            min-height: 44px;
            padding: 11px 18px;
            border: 0;
            border-radius: 10px;
            background: var(--primary-color, #03a9f4);
            color: white;
            font: inherit;
            font-weight: 650;
            text-decoration: none;
            cursor: pointer;
        }

        button:disabled,
        .button.disabled {
            opacity: 0.5;
            cursor: not-allowed;
            pointer-events: none;
        }

        pre {
            min-height: 220px;
            max-height: 420px;
            overflow: auto;
            padding: 16px;
            border-radius: 12px;
            background: #090d14;
            color: #d1fae5;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .success {
            color: #4ade80;
        }

        .error {
            color: #fb7185;
        }
    </style>
</head>
<body>
<main>
    <header class="header">
        <h1>📘 HADocs</h1>
        <div class="muted">
            Home Assistant documentation and health analysis
        </div>
    </header>

    <section class="grid">
        <article class="card">
            <h2>Status</h2>
            <p id="status" class="value">Loading…</p>
        </article>

        <article class="card">
            <h2>Last scan</h2>
            <p id="last-scan" class="value">—</p>
        </article>

        <article class="card">
            <h2>Report</h2>
            <p id="report-status" class="value">Checking…</p>
        </article>
    </section>

    <section class="actions">
        <button id="scan-button" type="button">
            Start new scan
        </button>

        <a
            id="report-button"
            class="button disabled"
            href="./report/index.html"
            target="_blank"
            rel="noopener"
        >
            Open report
        </a>
    </section>

    <section class="card">
        <h2>Scan log</h2>
        <pre id="logs">No scan log available.</pre>
    </section>
</main>

<script>
    const statusElement = document.getElementById("status");
    const lastScanElement = document.getElementById("last-scan");
    const reportStatusElement = document.getElementById("report-status");
    const scanButton = document.getElementById("scan-button");
    const reportButton = document.getElementById("report-button");
    const logsElement = document.getElementById("logs");

    function formatDate(value) {
        if (!value) {
            return "—";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return date.toLocaleString();
    }

    async function fetchJson(relativeUrl, options = undefined) {
        const response = await fetch(relativeUrl, options);
        const body = await response.json();

        if (!response.ok) {
            throw new Error(body.error || `HTTP ${response.status}`);
        }

        return body;
    }

    async function refresh() {
        try {
            const [status, logData] = await Promise.all([
                fetchJson("./api/status"),
                fetchJson("./api/logs"),
            ]);

            scanButton.disabled = status.running;

            if (status.running) {
                statusElement.textContent = "Scanning…";
                statusElement.className = "value";
                scanButton.textContent = "Scan running…";
            } else if (status.exit_code === 0) {
                statusElement.textContent = "Ready";
                statusElement.className = "value success";
                scanButton.textContent = "Start new scan";
            } else if (status.exit_code !== null) {
                statusElement.textContent = "Last scan failed";
                statusElement.className = "value error";
                scanButton.textContent = "Start new scan";
            } else {
                statusElement.textContent = "Ready";
                statusElement.className = "value";
                scanButton.textContent = "Start new scan";
            }

            lastScanElement.textContent = formatDate(
                status.finished_at || status.started_at
            );

            if (status.report_available) {
                reportStatusElement.textContent = "Available";
                reportStatusElement.className = "value success";
                reportButton.classList.remove("disabled");
            } else {
                reportStatusElement.textContent = "Not generated";
                reportStatusElement.className = "value";
                reportButton.classList.add("disabled");
            }

            logsElement.textContent = logData.logs.length
                ? logData.logs.join("\\n")
                : "No scan log available.";

            if (status.running) {
                logsElement.scrollTop = logsElement.scrollHeight;
            }
        } catch (error) {
            statusElement.textContent = "Connection error";
            statusElement.className = "value error";
            logsElement.textContent = String(error);
        }
    }

    scanButton.addEventListener("click", async () => {
        scanButton.disabled = true;

        try {
            await fetchJson("./api/scan", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: "{}",
            });
        } catch (error) {
            alert(String(error));
        }

        await refresh();
    });

    refresh();
    window.setInterval(refresh, 1500);
</script>
</body>
</html>
"""


class HadocsRequestHandler(BaseHTTPRequestHandler):
    server_version = "HADocsWeb/0.2.1"

    def do_GET(self) -> None:
        path = self._request_path()

        if path in {"", "/"}:
            self._send_html(INDEX_HTML)
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

        if path != "/api/scan":
            self._send_json(
                {"error": "Not found"},
                status=HTTPStatus.NOT_FOUND,
            )
            return

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

    def log_message(self, format: str, *args: object) -> None:
        print(
            f"[HADocs Web] {self.address_string()} "
            f"- {format % args}",
            flush=True,
        )

    def _request_path(self) -> str:
        path = urlparse(self.path).path
        return unquote(path).rstrip("/") or "/"

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

    def _send_html(
        self,
        content: str,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        encoded = content.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

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