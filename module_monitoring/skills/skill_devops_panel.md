# Skill: the DevOps panel — the machines, and the one socket

Three personas, three entries. The status page carries the results a business
reader wants; the **DX** control opens the drawing a developer wants; the
**DevOps** control opens this panel — the containers, networks and volumes the
project actually runs on. *The repository shows the destination, not the road*:
the panel shows what the daemon reports and offers three verbs, and nothing else.

The panel is `module_monitoring/sub_module_portraefik/`. Its page is a static
file the dashboard already serves, like the drawing; only its API is a route.

## Why a sub-module, and why that name

`portraefik` is the owner's coinage — a blend of two brand names of tools this
repository deliberately does not use. Nothing of Portainer or Traefik is inside:
no routing, no reverse proxy, no third-party management UI. Rejected forms:
`sub_module_devops`, `sub_module_docker` (the register bans `module_docker` as a
stem, and `service` as a path segment).

It is nested rather than promoted for the reason the drawing is: the dashboard
serves its own directory, so the panel's page needs no route. It is the second
`sub_module_*` in this tree, and two is still a coincidence — the third mints
the convention or nothing does.

## The one socket, and what containment means

`/var/run/docker.sock` is mounted in `portraefik` and in no other container.
The dashboard holds no socket and makes no Engine call: it proxies `/devops/*`
to `portraefik` by service name over the compose network, the same mechanism
and the same `(status, body)` shape as `/containers/<TICKER>/status`. The scoped
repeal of the socket rule lives with the topology it changes,
`../../module_skills/skill_asset_containers.md`.

The containment is of the **mount**, not of the **reach**. Any client that can
reach the dashboard's loopback origin can reach the Engine through the proxy —
including a page on another site, because a simple cross-origin `POST` needs no
preflight. There is no auth, no token and no origin check in v1. Stated, not
mitigated.

`portraefik` runs as the host user like every other service and takes the host's
docker group through `group_add`, so it reads the socket without being root; the
Makefile measures that group the way it measures `UID` and `GID`.

## The API

The Engine is addressed at a pinned version, `v1.44` — the daemon's own declared
minimum, so upgrading the engine does not move the contract underneath the panel.

| route | answers |
|---|---|
| `GET /devops/api/machines` | every container the daemon reports, this project's first and marked `own_project`; state, uptime, image, ports, restarts, and one stats sample |
| `GET /devops/api/networks` | the networks, their driver and scope, and what is attached to each |
| `GET /devops/api/volumes` | named volumes with the sizes only `/system/df` reports, and the bind mounts this project's containers carry |
| `GET /devops/api/image` | the one image this project runs, named by the panel's own container rather than by a literal |
| `GET /devops/api/events` | this project's own daemon events over a bounded window, newest first |
| `POST /devops/api/machines/<id>/<action>` | `start`, `stop`, `restart` — the whole allowlist |

Both bounds on the event tail are deliberate: a window in minutes, because an
unbounded `/events` grows with the daemon's uptime rather than with the question;
and a project label filter, because a host's other stacks bury this project's
events under their health checks.

## The guard

An action is offered for a container of **this compose project** and refused for
every other, with the reason in the body:

```
403  {"action": "stop", "refused": true, "compose_project": "<theirs>",
      "reason": "stop is offered for this project's own containers; this one belongs to <theirs>"}
```

The project is read from the panel's own container labels at start, never
written as a literal: a host may run a sibling project whose services carry the
same names — `dashboard`, `asset-btc` — and only the `com.docker.compose.project`
label separates them. An action outside the allowlist and a container the daemon
does not know are both `404`.

Not in v1, each needing its own decision: `rm`, `exec`, `prune`, image
operations, compose up/down from the browser, log streaming.

## The views, and which number is the truer one

An asset container is measured twice, and the panel says which to believe. The
**asset containers** section reads each container's own `/status` through the
dashboard's proxy — the cgroup accounting measured from inside, page cache
included, against the ceiling that container actually runs under. The
**containers on this host** table reads the Engine's own accounting for every
container including foreign ones. For an asset, the cgroup figures are the truer
ones; the Engine's are what exists for a container that reports nothing.

Its columns and badges are the ones the asset-container view has always had:

| column / badge | label | source |
|---|---|---|
| asset | the ticker | a link into the selector |
| container | `up` / `down` | the proxy's status code |
| up since | `up since` | `started_at_utc` |
| memory | `memory` | `footprint.memory_bytes` against `memory_limit_bytes`, as a bar |
| peak | `peak` | `footprint.memory_peak_bytes` |
| CPU | `CPU` | two `cpu_usage_seconds` of one container run over the wall time between polls, over `cpu_count`; a dash until the second poll |
| data | `data` | the overview: `observation_lag_minutes`; the badge: `data.last_observation_utc` and the lag |
| rows | `rows` | `data.row_count`, `data.db_bytes` |
| window | `covered` / `not covered` | `data.research_window_covered` |
| trained | `trained <date>` | `artifacts.model_evaluation_modified_utc`; `artifacts no run yet` while the ML snapshot has no block, or the folder no longer holds the set |
| threshold | `met` / `fallback` | `artifacts.entry_edge_threshold_constraint_met` |
| measured | `measured` | `data.measurement_age_minutes` |
| cpu (badge) | `cpu <seconds>s on <n> cpus` | `footprint.cpu_usage_seconds`, `cpu_count` — the container's total so far |
| a symbol with no row, or an asset with no database | `no data yet` | `data: null` — never `down` |

`badge--warn` marks an observation or a measurement older than
`download_cadence_minutes` from the data snapshot — never a literal in the page;
`badge--down` a container whose endpoint did not answer 200.

## What the panel owes the reader

A container that does not answer renders `down` with dashes and never a previous
number, exactly as the tab it replaces did. The engine reports counters, not
rates: a CPU rate is this page's arithmetic over two polls, a dash until the
second, and a counter that went backwards is a container that restarted rather
than a negative rate. An action never renders optimistically — the panel re-reads
every view and shows the state the engine now reports. One action at a time, and
the buttons of a foreign container are disabled before the server ever has to
refuse them.

The panel polls only while it is visible, at the interval the server publishes;
no cadence is a literal in the page.

## What the business reader sees

One tab fewer and one button more. The status page keeps *Pipeline*, *Data
Quality*, *ML Research*, *ML Assets* and *Lifecycle*; **Containers** left the tab
row for this panel. The four result tabs are unchanged.
