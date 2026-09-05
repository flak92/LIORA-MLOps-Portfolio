# Skill: asset containers — the topology, the endpoint, the socket

The asset is the primary object; its container is how a stage is run for it
locally, and the engine is the support layer. Four images, one per module repository — `liora-module-<domain>`,
built from `./<9NN>-module_<domain>` alone —; three runners — `data`, `features`, `ml`, one per
module of the chain, a role and a one-off each, each in its module's image — and one resident container per ticker
of the basket, in the monitoring module's image, differing only by
`ASSET=<TICKER>`; every service written out in `docker-compose.yml` under three anchors: `x-store-environment` is
the store contract every service carries — the four `STORE_*_DIR` and the thread cap —, `x-service` is what
every service is — `init`, `user`, the store environment and the four store mounts, each service adding its module's
`build` and `image` — and
`x-server` adds the one `command: python -m module_monitoring.serve` the dashboard and the
assets share, which is why the runners stay outside it. The project is named `liora` in the file, so a
container is `liora-<service>-1` on every host. The dashboard
reaches them only through its own proxy: no asset container publishes a port.
*The repository shows the destination, not the road*: no restart policy, no healthcheck.

**The socket rule, and its one scope.** Managing containers, networks and
volumes needs the Docker Engine API, and the honest way to it is the socket, so
the rule that forbade it is not bent but scoped: `/var/run/docker.sock` is
mounted in **exactly one container, `devops`**, whose single responsibility
is docker management and monitoring. It is never mounted in the dashboard, never
in an asset container, and never for a badge. No third-party socket proxy — that
is a dependency — and no TCP daemon endpoint, which is weaker than the socket.
What that contains is the **mount**: root-equivalent access lives in one service
that publishes no port. What it does not contain is **reach** — the dashboard
proxies `/devops/*` to it, so anything that can reach the dashboard's loopback
origin can reach the Engine through it, a browser tab on another site included.
Stated, not mitigated. The panel's own contract is
`module_monitoring/skills/skill_devops_panel.md`.

## The topology

| service | image | role | lifetime |
|---|---|---|---|
| `data`, `features`, `ml` — one runner per module of the chain | the `x-service` anchor plus the module's `build: ./<9NN>-module_<domain>` and `image: liora-module-<domain>` — no `command:`, so `run --rm -T` supplies one; `ml` alone adds the `5g` ceiling | every stage of its module: a per-asset stage as one one-off container per asset through the `fanout` macro, a basket-wide stage once through `basket`, the one-asset promotion a hand starts with `ASSET=`; a download stays one process per venue because a venue's per-IP limit is budgeted per process | one-off |
| `dashboard` | the `x-server` anchor with the monitoring module's `build:` and `image:`, plus `ports:` and a respelled `volumes:` — the anchor's four store mounts and the repository's drawing read-only below its web root, `./sub_module_dx:/app/module_monitoring/sub_module_dx:ro` | the same server in its dashboard role, published on `127.0.0.1:${PORT}` only | resident |
| `asset-<ticker>` × one per ticker of `TICKERS` | the `x-server` anchor with the monitoring module's `image:`, plus an `environment:` that merges `<<: *store_environment` with `ASSET: <TICKER>` | the same server in its asset role | resident |
| `devops` | the `x-service` anchor with the monitoring module's `image:`, plus its own `command:`, `group_add:` and the one mount, the socket | the DevOps panel's server: the one container that holds the docker socket | resident |

`init: true` on every service: a Python process as PID 1 has no SIGTERM
handler, so `docker compose down` would wait out the stop timeout and kill a
stage mid-write, and a one-off's PID 1 reaps whatever its stage leaves behind.
`5g` sits above DuckDB's `4GB` ceiling and bounds a runaway allocation
outside DuckDB; the `ml` runner alone carries it, the one task — HPO and
XGBoost — that allocates above that ceiling; `data` and `features` open a database
under its own `memory_limit` and allocate nothing outside it, and the residents
compute nothing. `build: ./<9NN>-module_<domain>` and `image: liora-module-<domain>` sit on
each module's runner and on `dashboard`; `asset-<ticker>` and `devops` name the image `dashboard` builds, so a
bare recursive clone builds instead of reaching for a registry; `docker images` shows four, and each
`Dockerfile` copies its package onto `python:3.12-slim` with the module's own pins.
Concurrency is bounded by `JOBS`. One mechanism only — no
`mem_limit` beside it, no reservation, no CPU quota, and no restart policy,
because a failure is reported, not hidden. Every container carries the four
`/store/<content>` mounts and no code mount: the image carries its module's package under `/app`, and
the stores are the one thing a container reaches on the host. Because a service's `volumes:` replaces
the anchor's key rather than extending it, `devops` respells it to the socket alone, dropping the store
mounts it never reads, and takes the host's docker group through `group_add` so it reads the socket
without being root, and `dashboard` respells the four to add the repository's drawing read-only below
its web root; the raw store stays central and Lean-exact. The store contract is the env-named path,
and code and state never share a mount (`skill_pre_aws_solution.md` § Docker is compute,
not storage). Every process binds
`0.0.0.0` on the internal port 8900 — `CONTAINER_PORT` in `module_monitoring/config.py`, with no
argument: the server is docker-only. `PORT` is only the host side of the
dashboard's mapping, measured at invocation, never hardcoded — the Makefile asks
for the port the dashboard already publishes, else the first free port from 8900
upward, because another project on the same host — or a checkout of LIORA run
under `COMPOSE_PROJECT_NAME=` — may hold 8900
(`skill_pre_aws_solution.md` § What stays as it is, and why, the row on compose
names); `PORT=n` overrides it, `make on` prints the address, and no document
states the host port as a number. The measurement is a look, not a lock: a port
taken between the look and the bind fails the start, and the next `make on`
looks again — stated, not mitigated. A stage run with another `PORT` never
recreates a resident, and a checkout without the rule keeps assuming 8900 and
fails its own start the day this one holds it. Every container runs as the host user — `user: ${UID:-1000}:${GID:-1000}`,
fed by the Makefile's `COMPOSE_ENV` — so nothing it writes is root-owned.

`make on` builds the images if needed, starts the dashboard and the residents, and
opens the page; `make off` takes everything down. `make all` runs the whole chain,
download to snapshots, every stage in a one-off container of its module's runner:
the `fanout` macro is `docker compose run --rm -T <runner> python -m
module_<x>.<stage> --tickers <TICKER>` once per asset — ingest one container at a
time, the ML stages `JOBS` at a time — and `basket` the same once for the whole
basket. No resident is assumed for compute: a resident only serves, the panel
measures the one-off doing the work while it runs, and `record.py` measures a
stage from outside and knows no container. The direction is
`skill_pre_aws_solution.md`. `ASSET` is read by `serve.py` choosing its role and by
nothing else — the fan-out passes `--tickers <TICKER>` from `TICKER_LIST`; `build_ticker_parser` has no default — every launcher names
the assets — and no stage module reads `ASSET`. The `COMPOSE` macro never gains `-f` or `COMPOSE_FILE`: one
compose file, every service visible in it. Adding an asset is one line in
`TICKERS` and one `asset-<ticker>` block under `x-server`, both in Orchestration; nothing
changes in a module repository.

**The seat.** The `x-service` anchor is one task definition parameterised by `--tickers`,
each resident a service of the container runtime kept running on the one Linux container
instance (Amazon ECS on Amazon EC2): `asset-<ticker>` is the resident's `ASSET` override, the
`fanout` macro's `run --rm` already a task run per stage per asset — nothing left to
edit — the four store mounts the volume, each module's image the task's image, the `ml` runner's
`5g` the task's memory, `init` and `user` the task definition's own keys. `skill_pre_aws_solution.md` § The mapping table and
§ The retrain runtime is a ladder.

## The server

`module_monitoring/serve.py`, one file, two roles chosen by `ASSET`. Of the
dashboard role's routes, two concern the asset containers: `GET /containers` —
the registry: `generated_at_utc`, `poll_interval_seconds` and `tickers`, the
asset folders of `store_assets_artifacts/` — and `GET /containers/<TICKER>/status`,
proxied to `http://asset-<ticker>:8900/status`. The asset role answers
`GET /status`. A folder without an `asset-<ticker>` block answers 503 through the
proxy: the compose block is what makes a listed asset reachable.

The asset role never opens DuckDB: the database takes one whole-file lock per
process, so a second opener fails at once. The endpoint reads what is already
measured — the data and ML snapshots' rows and blocks for its symbol, and `stat` of
the database — and what only the container can see:
its own cgroup (`memory.current`, `memory.peak`, `memory.max` or `MemTotal`
when unlimited, `cpu.stat usage_usec`).

## The endpoint contract

The envelope carries `ticker`, `generated_at_utc` and `started_at_utc`; the
blocks `data`, `artifacts` and `footprint` carry the keys registered in
`glossary.md` § Container status endpoint. `data` and `artifacts` are `null`
when the snapshots hold nothing for the asset, and equally when the asset folder
no longer holds the object the snapshot describes — the database for `data`, the
artifact set for `artifacts`. Both snapshots are tracked, so a fresh clone
carries them and neither object: it answers `no data yet` and `no run yet`
instead of someone else's numbers. The CPU rate the tab shows is the delta of two polls over
`cpu_count` — presentation arithmetic, never published. No hash: git holds the
identity.

**Down semantics.** Cannot connect, name does not resolve, or the exchange
fails after the request is sent — HTTP 503 with no body; a ticker outside the
basket — 404. The page decides on the status code alone: any non-200 renders
the container `down` and every other cell as a dash, never the previous
numbers. `Cache-Control: no-store` from the proxy. A stopped container renders
`down` after Docker's resolver gives up on the vanished alias, not after the
socket timeout — stated, not mitigated.

## The panel

The asset containers are presented by the DevOps panel, not by a tab of the
status page: its columns, its badges and its poll are
`module_monitoring/skills/skill_devops_panel.md`. What belongs here is what
the containers themselves owe it — the endpoint contract and the down semantics
above.
