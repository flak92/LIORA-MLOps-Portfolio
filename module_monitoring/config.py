"""Static configuration of module_monitoring: the run record's directory, the snapshots' paths, the server's addresses
and the cadences — the one place this module builds a path or a URL.

A run record belongs to the basket, not to one asset: one directory per run under the run-records store, one file per
stage, written from outside every container by `record.py` and read here. The cgroup and procfs paths
are the exception AGENTS.md names and stay in `serve.py`, beside the syscalls that read them; the per-asset artifact
paths stay in the configs of the modules that produce them — this module reads the artifacts store only to list its
asset folders and to size an asset's database.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

# ---- the one server, its role chosen by ASSET
CONTAINER_PORT = 8900                    # the port every compose service listens on; PORT is only the host side of the dashboard mapping, measured by the Makefile
BIND_ADDRESS = "0.0.0.0"                 # every interface of the container's own namespace; compose publishes the dashboard on 127.0.0.1
DEVOPS_SERVICE = "devops"                # the one compose service that holds the docker socket
DEVOPS_ROUTE_PREFIX = "/devops"          # the dashboard route the panel's API is proxied under
CONTAINER_POLL_INTERVAL_SECONDS = 5      # published to the page, which never carries a cadence of its own
ASSET_STATUS_FETCH_TIMEOUT_SECONDS = 2   # bounds each socket operation of the proxy, not the exchange
PANEL_FETCH_TIMEOUT_SECONDS = 10         # the panel answers after many Engine exchanges, so its bound is its own

# ---- the units the endpoint converts with
MICROSECONDS_PER_SECOND = 1_000_000
# twice by extraction — identical in module_data/config.py, module_ml/config.py, sub_module_dx/config.py
# (module_skills/glossary.md § Twice by extraction)
BYTES_PER_KIBIBYTE = 1024

# ---- the run record: one directory per run of the chain, one file per stage, the whole basket inside it
# the three stores this module reads arrive as environment, one variable per store — the store contract; the snapshots
# are read where the modules that measured themselves wrote them, and served under one route prefix
STORE_RUN_RECORDS_DIR = Path(os.environ["STORE_RUN_RECORDS_DIR"])
# twice by extraction — the two store reads below are identical in module_data/config.py, module_features/config.py and
# module_ml/config.py, and the two snapshot paths are the writers' own, module_data/config.py and module_ml/config.py, read
# here (module_skills/glossary.md § Twice by extraction)
STORE_ASSETS_ARTIFACTS_DIR = Path(os.environ["STORE_ASSETS_ARTIFACTS_DIR"])   # the registry lists its asset folders
STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])
DATA_STATUS_JSON_PATH = STORE_STATUS_DIR / "data_status.json"
ML_STATUS_JSON_PATH = STORE_STATUS_DIR / "ml_status.json"
STORE_STATUS_ROUTE_SEGMENT = "store_status"          # the dashboard route /store_status/<name>: a snapshot served by its file name
MODULE_MONITORING_DIR = Path(__file__).resolve().parent   # the static page: this module's own directory is the web root


def store_status_file(name: str) -> Path:
    """One snapshot of the status store by its file name — the object the route /store_status/<name> serves."""
    return STORE_STATUS_DIR / name


def run_dir(run_id: str) -> Path:
    """One directory per recorded run of the chain — a run is the basket's, never one asset's; inside it one
    `<stage>.json` per stage, as record.py wrote them."""
    return STORE_RUN_RECORDS_DIR / run_id


def asset_databases(ticker: str) -> list[Path]:
    """The database files of one asset folder, as they lie there — the endpoint sizes what is there and names no descriptor of another module."""
    return sorted((STORE_ASSETS_ARTIFACTS_DIR / ticker).glob("*.duckdb"))


# ---- the compose services and their addresses
def asset_service(ticker: str) -> str:
    """The compose service that is one asset's container, as the file spells it under its anchor."""
    return f"asset-{ticker.lower()}"


def asset_status_url(ticker: str) -> str:
    """One asset's endpoint as the dashboard's proxy reaches it: service name, internal port."""
    return f"http://{asset_service(ticker)}:{CONTAINER_PORT}/status"


def devops_api_url(route: str) -> str:
    """The DevOps panel's API as the dashboard's proxy reaches it: service name, internal port."""
    return f"http://{DEVOPS_SERVICE}:{CONTAINER_PORT}{route}"


# ---- the conversions the server uses
def to_utc_text(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def to_utc_datetime(text: str) -> datetime:
    """The snapshots write minutes as `YYYY-MM-DD HH:MM` and seconds as `… HH:MM:SS`, both UTC."""
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def to_int(text: str | None) -> int | None:
    return None if text is None else int(text)
