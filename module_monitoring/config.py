"""Static configuration of module_monitoring: the run record's directory, the snapshots' paths, the server's addresses
and the cadences — the one place this module builds a path or a URL.

A run record belongs to the basket, not to one asset: one directory per run under the run-records store, one file per
stage, written from outside every container by `record.py` and read here. The per-asset artifact paths stay in the
configs of the modules that produce them — this module reads no artifacts store.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

# ---- the dashboard's server, and the panel it proxies to
CONTAINER_PORT = 8900                    # the port a server listens on inside its container; PORT is only the host side of the dashboard mapping, measured by the Makefile
BIND_ADDRESS = "0.0.0.0"                 # every interface of the container's own namespace; compose publishes the dashboard on 127.0.0.1
DEVOPS_SERVICE = "devops"                # the one compose service that holds the docker socket
DEVOPS_ROUTE_PREFIX = "/devops"          # the dashboard route the panel's API is proxied under
CONTAINER_POLL_INTERVAL_SECONDS = 5      # published to the page, which never carries a cadence of its own
PANEL_FETCH_TIMEOUT_SECONDS = 10         # the panel answers after many Engine exchanges, so its bound is its own

# ---- the run record: one directory per run of the chain, one file per stage, the whole basket inside it
# the two stores this module reads arrive as environment, one variable per store — the store contract; the snapshots
# are read where the modules that measured themselves wrote them, and served under one route prefix
STORE_RUN_RECORDS_DIR = Path(os.environ["STORE_RUN_RECORDS_DIR"])
# twice by extraction — the store read below is identical in module_data/config.py, module_features/config.py and
# module_ml/config.py (module_skills/glossary.md § Twice by extraction)
STORE_STATUS_DIR = Path(os.environ["STORE_STATUS_DIR"])
STORE_STATUS_ROUTE_SEGMENT = "store_status"          # the dashboard route /store_status/<name>: a snapshot served by its file name
MODULE_MONITORING_DIR = Path(__file__).resolve().parent   # the static page: this module's own directory is the web root


def store_status_file(name: str) -> Path:
    """One snapshot of the status store by its file name — the object the route /store_status/<name> serves."""
    return STORE_STATUS_DIR / name


def run_dir(run_id: str) -> Path:
    """One directory per recorded run of the chain — a run is the basket's, never one asset's; inside it one
    `<stage>.json` per stage, as record.py wrote them."""
    return STORE_RUN_RECORDS_DIR / run_id


# ---- the panel's address
def devops_api_url(route: str) -> str:
    """The DevOps panel's API as the dashboard's proxy reaches it: service name, internal port."""
    return f"http://{DEVOPS_SERVICE}:{CONTAINER_PORT}{route}"


# ---- the conversions the server uses
def to_utc_text(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M:%S")
