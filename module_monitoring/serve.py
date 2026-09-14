"""The one server of module_monitoring: the dashboard.

    the static page; GET /store_status/<name>, one snapshot as its writer left it;
    GET /runs, the recorded runs; GET /runs/<run_id>, one run as its stages left it;
    GET and POST /devops/*, the DevOps panel's API proxied to the one container that holds the socket
"""

from __future__ import annotations

import functools
import http.client
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import config


def to_json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, indent=1).encode("utf-8")


# twice by extraction
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_run_ids() -> list[str]:
    """Every recorded run, newest first — the run id sorts chronologically by design."""
    records = config.STORE_RUN_RECORDS_DIR
    return sorted((path.name for path in records.iterdir() if path.is_dir()), reverse=True) if records.exists() else []


def run_payload(run_id: str) -> dict:
    """One recorded run as the page reads it: every stage record the recorder left in the run's directory, in the
    order the stages started."""
    records = (load_json(path) for path in config.run_dir(run_id).glob("*.json"))
    stages = sorted((record for record in records if "started_at_utc" in record), key=lambda record: record["started_at_utc"])
    return {
        "run_id": run_id,
        "generated_at_utc": config.to_utc_text(datetime.now(tz=UTC)),
        "stages": stages,
    }


def runs_payload() -> dict:
    return {"generated_at_utc": config.to_utc_text(datetime.now(tz=UTC)), "run_ids": load_run_ids()}


def fetch_panel(method: str, route: str) -> tuple[int, bytes]:
    """The DevOps panel's API as (status code, body): an HTTP answer forwarded as it came, 503 with no body when the
    panel does not answer. The socket the panel holds stays in the panel: this process never opens it."""
    request = urllib.request.Request(config.devops_api_url(route), method=method,
                                     data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(request, timeout=config.PANEL_FETCH_TIMEOUT_SECONDS) as answer:
            return answer.status, answer.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except (OSError, http.client.HTTPException):
        return HTTPStatus.SERVICE_UNAVAILABLE, b""


def write_response(handler: BaseHTTPRequestHandler, status: int, body: bytes = b"") -> None:
    """One reply shape for every route: own headers only, and never cached."""
    handler.send_response(status)
    if body:
        handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


class DashboardHandler(SimpleHTTPRequestHandler):
    """The dashboard: the static page, the snapshots, the recorded runs, and the proxy to the DevOps panel's API.
    It holds no docker socket and makes no Engine call; the panel does both, alone."""

    def do_GET(self):
        segments = self.path.split("?")[0].split("/")
        if self.path.startswith(config.DEVOPS_ROUTE_PREFIX + "/"):
            write_response(self, *fetch_panel("GET", self.path.removeprefix(config.DEVOPS_ROUTE_PREFIX)))
        elif self.path == "/runs":
            write_response(self, HTTPStatus.OK, to_json_bytes(runs_payload()))
        elif len(segments) == 3 and segments[1] == "runs":
            if segments[2] in load_run_ids():
                write_response(self, HTTPStatus.OK, to_json_bytes(run_payload(segments[2])))
            else:
                write_response(self, HTTPStatus.NOT_FOUND)
        elif len(segments) == 3 and segments[1] == config.STORE_STATUS_ROUTE_SEGMENT:
            snapshot = config.store_status_file(segments[2])   # one path segment: the file name of a snapshot in the status store
            if snapshot.is_file():
                write_response(self, HTTPStatus.OK, snapshot.read_bytes())
            else:
                write_response(self, HTTPStatus.NOT_FOUND)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith(config.DEVOPS_ROUTE_PREFIX + "/"):
            write_response(self, *fetch_panel("POST", self.path.removeprefix(config.DEVOPS_ROUTE_PREFIX)))
        else:
            write_response(self, HTTPStatus.NOT_FOUND)


def main() -> int:
    handler = functools.partial(DashboardHandler, directory=str(config.MODULE_MONITORING_DIR))
    server = ThreadingHTTPServer((config.BIND_ADDRESS, config.CONTAINER_PORT), handler)
    print(f"dashboard at http://{config.BIND_ADDRESS}:{config.CONTAINER_PORT}/", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
