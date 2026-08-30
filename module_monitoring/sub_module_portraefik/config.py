"""Engine API paths and the sub-module's own constants — the only place this sub-module builds a path.

The socket is the boundary this sub-module exists to own: it is mounted in this
container and in no other, and every path below is a path of the Docker Engine
API, not of this repository. The API version is pinned at the daemon's own
minimum rather than its current one, so an upgrade of the engine does not move
the contract underneath the panel.
"""

from __future__ import annotations

import json
import urllib.parse

DOCKER_SOCKET_PATH = "/var/run/docker.sock"
ENGINE_API_VERSION = "v1.44"
ENGINE_EXCHANGE_TIMEOUT_SECONDS = 5     # bounds each socket operation of the Engine exchange, not the exchange
ENGINE_HOST_HEADER = "localhost"        # the socket carries no host; http.client still needs the header

COMPOSE_PROJECT_LABEL = "com.docker.compose.project"
COMPOSE_SERVICE_LABEL = "com.docker.compose.service"

# the whole allowlist: every other Engine mutation is outside this contract
CONTAINER_ACTIONS = ("start", "stop", "restart")

EVENT_TAIL_MINUTES = 60                 # the tail is bounded by time; an unbounded /events grows without limit
EVENT_TAIL_LIMIT = 40                   # and by count, because the page holds them and nothing persists them
NANOSECONDS_PER_SECOND = 1_000_000_000


def engine_path(path: str) -> str:
    """One Engine route under the pinned API version."""
    return f"/{ENGINE_API_VERSION}{path}"


def containers_path() -> str:
    """Every container on the host, stopped ones included — foreign containers are visible, never actionable."""
    return engine_path("/containers/json?all=true")


def container_path(container_id: str) -> str:
    return engine_path(f"/containers/{container_id}/json")


def container_stats_path(container_id: str) -> str:
    """One sample, not a stream: the page differences two polls the way it does for an asset's cgroup."""
    return engine_path(f"/containers/{container_id}/stats?stream=false&one-shot=true")


def container_action_path(container_id: str, action: str) -> str:
    return engine_path(f"/containers/{container_id}/{action}")


def networks_path() -> str:
    return engine_path("/networks")


def network_path(network_id: str) -> str:
    return engine_path(f"/networks/{network_id}")


def system_df_path() -> str:
    """Volumes with their sizes: /volumes reports no size, /system/df carries UsageData."""
    return engine_path("/system/df")


def image_path(image: str) -> str:
    return engine_path(f"/images/{urllib.parse.quote(image, safe='')}/json")


def events_path(since_epoch_seconds: int, until_epoch_seconds: int, project: str) -> str:
    """A bounded window, so the answer terminates and its size is a function of the window, not of uptime;
    and bounded to this project, because a host's other stacks bury its own events in their health checks."""
    query = urllib.parse.urlencode({
        "since": since_epoch_seconds,
        "until": until_epoch_seconds,
        "filters": json.dumps({"label": [f"{COMPOSE_PROJECT_LABEL}={project}"]}),
    })
    return engine_path(f"/events?{query}")
