"""Static configuration of module_monitoring: the run record's paths, the server's addresses and the
cadences — the one place this module builds a path or a URL.

A run record belongs to the basket, not to one asset: one directory per run under
`store_run_records/`, and every container of the run appends to the same two files inside it. The
cgroup and procfs paths are the exception AGENTS.md names and stay in `serve.py` and `record.py`,
beside the syscalls that read them; the per-asset artifact paths stay in the configs of the modules
that produce them.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from module_data.config import REPO_ROOT

# ---- the one server, its role chosen by ASSET
CONTAINER_PORT = 8900                    # the port every compose service listens on; PORT is only the host side of the dashboard mapping
BIND_ADDRESS = "0.0.0.0"                 # every interface of the container's own namespace; compose publishes the dashboard on 127.0.0.1
PIPELINE_SERVICE = "pipeline"            # the compose service a basket-wide stage runs in
PORTRAEFIK_SERVICE = "portraefik"        # the one compose service that holds the docker socket
DEVOPS_ROUTE_PREFIX = "/devops"          # the dashboard route the panel's API is proxied under
CONTAINER_POLL_INTERVAL_SECONDS = 5      # published to the page, which never carries a cadence of its own
RUN_SAMPLE_POINT_LIMIT = 900             # the timeline's stride: a long run is thinned, never truncated
ASSET_STATUS_FETCH_TIMEOUT_SECONDS = 2   # bounds each socket operation of the proxy, not the exchange
PANEL_FETCH_TIMEOUT_SECONDS = 10         # the panel answers after many Engine exchanges, so its bound is its own
DASHBOARD_READY_FETCH_TIMEOUT_SECONDS = 5   # the same bound for the readiness check that closes a run

# ---- the recorder's loop around a wrapped stage
SAMPLE_INTERVAL_SECONDS = 1.0
# /proc/<pid>/io is unreadable once the child is a zombie, so it is polled far faster than the
# samples are written: a stage shorter than one sample interval still leaves its byte counts
PROCESS_POLL_INTERVAL_SECONDS = 0.05
PIPE_READ_SIZE_BYTES = 65536
MICROSECONDS_PER_SECOND = 1_000_000

# ---- the run record: one directory per run of the chain, the whole basket inside it
STORE_RUN_RECORDS_DIR = REPO_ROOT / "store_run_records"


def run_dir(run_id: str) -> Path:
    """One directory per recorded run of the chain — a run is the basket's, never one asset's."""
    return STORE_RUN_RECORDS_DIR / run_id


def events_jsonl(run_id: str) -> Path:
    """One line per stage, appended by the stage itself from whichever container ran it."""
    return run_dir(run_id) / "events.jsonl"


def resources_jsonl(run_id: str) -> Path:
    """The 1 s container-wide samples, appended by every container of the run."""
    return run_dir(run_id) / "resources.jsonl"


def summary_json(run_id: str) -> Path:
    """The stage table and the run totals, written once when the run is finalized."""
    return run_dir(run_id) / "summary.json"


def manifest_json(run_id: str) -> Path:
    """What ran, where, on what host and how it ended, written beside the summary."""
    return run_dir(run_id) / "manifest.json"


def stage_log(run_id: str, stage: str, docker_service: str) -> Path:
    """One stage's output verbatim. The container is half the name because one stage name runs once
    per asset, and two containers opening one log would truncate each other."""
    return run_dir(run_id) / "logs" / f"{stage}_{docker_service}.log"


# ---- the compose services and their addresses
def asset_service(ticker: str) -> str:
    """The compose service that is one asset's container, as the file spells it under its anchor."""
    return f"asset-{ticker.lower()}"


def asset_status_url(ticker: str) -> str:
    """One asset's endpoint as the dashboard's proxy reaches it: service name, internal port."""
    return f"http://{asset_service(ticker)}:{CONTAINER_PORT}/status"


def portraefik_api_url(route: str) -> str:
    """The DevOps panel's API as the dashboard's proxy reaches it: service name, internal port."""
    return f"http://{PORTRAEFIK_SERVICE}:{CONTAINER_PORT}{route}"


def dashboard_registry_url(port: str) -> str:
    """The dashboard's registry as the host reaches it. Compose publishes it on loopback alone, on
    the host side of the mapping, which is why the port is asked for and never assumed."""
    return f"http://127.0.0.1:{port}/containers"


def dashboard_asset_status_url(port: str, ticker: str) -> str:
    """One asset proxied through the dashboard, from the host: the registry route plus the asset."""
    return f"{dashboard_registry_url(port)}/{ticker}/status"


# ---- the conversions the server and the recorder share
def to_utc_text(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def to_utc_datetime(text: str) -> datetime:
    """The snapshots write minutes as `YYYY-MM-DD HH:MM` and seconds as `… HH:MM:SS`, both UTC."""
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def to_int(text: str | None) -> int | None:
    return None if text is None else int(text)
