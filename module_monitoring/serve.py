"""The one server of module_monitoring, its role chosen by ASSET.

    dashboard role (ASSET unset)   the static page; GET /containers, the registry; GET /containers/<TICKER>/status, one asset proxied
    asset role (ASSET=<TICKER>)    GET /status — the container reporting itself: its snapshot rows, its database size, its own cgroup
"""

from __future__ import annotations

import functools
import http.client
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from module_data import config as data_config
from module_ml import config as ml_config

CONTAINER_POLL_INTERVAL_SECONDS = 5      # published to the page, which never carries a cadence of its own
ASSET_STATUS_FETCH_TIMEOUT_SECONDS = 2   # bounds each socket operation of the proxy, not the exchange
CONTAINER_PORT = 8900                    # the port every compose service listens on; PORT is only the host side of the dashboard mapping
BIND_ADDRESS = "0.0.0.0"                 # every interface of the container's own namespace; compose publishes the dashboard on 127.0.0.1
MICROSECONDS_PER_SECOND = 1_000_000
CGROUP_MOUNT_PATH = Path("/sys/fs/cgroup")
OWN_CGROUP_PROC_PATH = Path("/proc/self/cgroup")
HOST_MEMORY_PROC_PATH = Path("/proc/meminfo")


def to_utc_text(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def to_utc_datetime(text: str) -> datetime:
    """The snapshots write minutes as `YYYY-MM-DD HH:MM` and seconds as `… HH:MM:SS`, both UTC."""
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def to_int(text: str | None) -> int | None:
    return None if text is None else int(text)


def to_json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, indent=1).encode("utf-8")


def minutes_since(then: datetime) -> int:
    return max(0, (datetime.now(tz=UTC) - then) // timedelta(minutes=1))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def load_cgroup_dir() -> Path:
    """The container's own cgroup: under cgroup v2 /proc/self/cgroup holds one line, 0::/<path>."""
    return CGROUP_MOUNT_PATH / load_text(OWN_CGROUP_PROC_PATH).rpartition("::")[2].lstrip("/")


def load_host_memory_bytes() -> int:
    """MemTotal, the first line of /proc/meminfo — the ceiling when the cgroup sets none."""
    return int(load_text(HOST_MEMORY_PROC_PATH).split()[1]) * data_config.BYTES_PER_KIBIBYTE


def snapshot_row(rows: list[dict], symbol: str) -> dict | None:
    return next((row for row in rows if row["symbol"] == symbol), None)


def data_block(ticker: str, data_status: dict) -> dict | None:
    """The asset's rows of the data snapshot with the two ages the tab judges them by; None while the snapshot has no row for it."""
    symbol = data_config.symbol(ticker)
    symbol_row = snapshot_row(data_status["symbols"], symbol)
    canonical_row = snapshot_row(data_status["canonical_source"], symbol)
    if symbol_row is None or canonical_row is None:
        return None
    database = data_config.research_ohlcv_duckdb(ticker)
    last_observation = to_utc_datetime(canonical_row["last_observation_utc"])
    research_end = to_utc_datetime(ml_config.RESEARCH_END_UTC)
    return {
        "generated_at_utc": data_status["generated_at_utc"],
        "row_count": symbol_row["row_count"],
        "last_observation_utc": canonical_row["last_observation_utc"],
        "observation_lag_minutes": minutes_since(last_observation),
        "measurement_age_minutes": minutes_since(to_utc_datetime(data_status["generated_at_utc"])),
        "db_bytes": database.stat().st_size if database.exists() else None,
        # the grid has no holes, so its two ends decide coverage of the half-open research window
        "research_window_covered": (data_config.DATA_WINDOW_START_UTC <= ml_config.RESEARCH_START_UTC
                                    and last_observation >= research_end - timedelta(minutes=1)),
    }


def artifacts_block(ticker: str, ml_status: dict) -> dict | None:
    """The folder's facts the tab shows; None while the ML snapshot has no block for the asset."""
    for asset in ml_status["assets"]:
        if asset["ticker"] == ticker:
            return {**asset["artifacts"],
                    "entry_edge_threshold_constraint_met": asset["strategy"]["entry_edge_threshold_constraint_met"]}
    return None


def footprint_block() -> dict:
    """The container's own cgroup accounting: memory.current is what the kernel charges it, page cache included."""
    own = load_cgroup_dir()
    memory_max = load_text(own / "memory.max")
    cpu_stat = dict(line.split() for line in load_text(own / "cpu.stat").splitlines())
    return {
        "memory_bytes": to_int(load_text(own / "memory.current")),
        "memory_peak_bytes": to_int(load_text(own / "memory.peak")),
        "memory_limit_bytes": load_host_memory_bytes() if memory_max == "max" else to_int(memory_max),
        "cpu_usage_seconds": round(int(cpu_stat["usage_usec"]) / MICROSECONDS_PER_SECOND, 3),
        "cpu_count": os.cpu_count(),
    }


def status_payload(server: StatusServer, data_status: dict, ml_status: dict) -> dict:
    return {
        "ticker": server.ticker,
        "generated_at_utc": to_utc_text(datetime.now(tz=UTC)),
        "started_at_utc": server.started_at_utc,
        "data": data_block(server.ticker, data_status),
        "artifacts": artifacts_block(server.ticker, ml_status),
        "footprint": footprint_block(),
    }


def registry_payload() -> dict:
    return {
        "generated_at_utc": to_utc_text(datetime.now(tz=UTC)),
        "poll_interval_seconds": CONTAINER_POLL_INTERVAL_SECONDS,
        "tickers": data_config.TICKERS,
    }


def fetch_asset_status(ticker: str) -> tuple[int, bytes]:
    """One asset's endpoint as (status code, body): an HTTP answer forwarded as it came, 503 with no body when the container does not answer."""
    try:
        with urllib.request.urlopen(f"http://asset-{ticker.lower()}:{CONTAINER_PORT}/status",
                                    timeout=ASSET_STATUS_FETCH_TIMEOUT_SECONDS) as answer:
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


class AssetStatusHandler(BaseHTTPRequestHandler):
    """The asset role: one route, the container reporting itself."""

    def do_GET(self):
        if self.path != "/status":
            write_response(self, HTTPStatus.NOT_FOUND)
            return
        data_status = load_json(data_config.MODULE_MONITORING_DATA_STATUS_JSON_PATH)
        ml_status = load_json(ml_config.MODULE_MONITORING_ML_STATUS_JSON_PATH)
        write_response(self, HTTPStatus.OK, to_json_bytes(status_payload(self.server, data_status, ml_status)))


class DashboardHandler(SimpleHTTPRequestHandler):
    """The dashboard role: the static page, the registry, and the proxy to one asset's endpoint."""

    def do_GET(self):
        segments = self.path.split("/")
        if self.path == "/containers":
            write_response(self, HTTPStatus.OK, to_json_bytes(registry_payload()))
        elif len(segments) == 4 and segments[1] == "containers" and segments[3] == "status":
            if segments[2] in data_config.TICKERS:
                write_response(self, *fetch_asset_status(segments[2]))
            else:
                write_response(self, HTTPStatus.NOT_FOUND)
        else:
            super().do_GET()


class StatusServer(ThreadingHTTPServer):
    """The one server; its role is the presence of ASSET, its start the tab's `up since`."""

    def __init__(self, ticker: str | None):
        handler = (AssetStatusHandler if ticker
                   else functools.partial(DashboardHandler, directory=str(data_config.MODULE_MONITORING_DIR)))
        super().__init__((BIND_ADDRESS, CONTAINER_PORT), handler)
        self.ticker = ticker
        self.started_at_utc = to_utc_text(datetime.now(tz=UTC))


def main() -> int:
    ticker = os.environ.get("ASSET")
    server = StatusServer(ticker)
    print(f"{'asset ' + ticker if ticker else 'dashboard'} role at http://{BIND_ADDRESS}:{CONTAINER_PORT}/", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
