# Skill: asset containers — the topology, the endpoint, the socket

The asset is the primary object; its container is how a stage is run for it
locally, and the engine is the support layer. One image, one resident container per ticker of the basket, differing only by
`ASSET=<TICKER>`, every service written out in `docker-compose.yml` under two anchors: `x-service` is what
every service is — `build`, `image`, `init`, `user`, the bind mount, the `5g` ceiling — and
`x-server` adds the one `command: python -m module_monitoring.serve` the dashboard and the
assets share, which is why the one-off build service stays outside it. The dashboard
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
`../module_monitoring/skills/skill_devops_panel.md`.

## The topology

| service | image | role | lifetime |
|---|---|---|---|
| `pipeline` | the `x-service` anchor and nothing else — no `command:`, so `run --rm -T` supplies one | `run --rm -T` one-offs for the basket-wide targets, the ones the Makefile does not fan out; a download stays sequential there because a venue's per-IP limit is budgeted per process | one-off |
| `dashboard` | the `x-server` anchor, plus `ports:` | the same server in its dashboard role, published on `127.0.0.1:${PORT}` only | resident |
| `asset-<ticker>` × one per ticker of `TICKERS` | the `x-server` anchor, plus `environment: {ASSET: <TICKER>, OMP_NUM_THREADS: 1}` | the same server in its asset role | resident |
| `devops` | the `x-service` anchor, plus its own `command:`, `group_add:` and the two mounts | the DevOps panel's server: the one container that holds the docker socket | resident |

`init: true` on every service: a Python process as PID 1 has no SIGTERM
handler, so `docker compose down` would wait out the stop timeout and kill a
stage mid-write; under a resident it also reaps the stages `exec` leaves
behind. `5g` sits above DuckDB's `4GB` ceiling and bounds a runaway allocation
outside DuckDB. Every service carries it, because every service can open a
database: `data-status` and `ml-status` do it inside the one-off, and only the
dashboard carries the ceiling without ever opening one. `build: .` sits on the
same anchor, so every service knows how to make the image it runs and a bare
clone builds instead of reaching for a registry; the tag is one, so
`docker images` still shows one image.
Concurrency is bounded by `JOBS`. One mechanism only — no
`mem_limit` beside it, no reservation, no CPU quota, and no restart policy,
because a failure is reported, not hidden. Every container keeps the `.:/app`
bind mount — `devops` respells `.:/app` beside the socket because a service's
`volumes:` replaces the anchor's key rather than extending it, and takes the host's
docker group through `group_add` so it reads the socket without being root; the raw
store stays central and Lean-exact. The one mount carries the code and the
`store_*` roots together — the local simplification; the `store_*` grammar, not
the runtime, keeps them apart (`skill_pre_aws_solution.md` § Docker is compute,
not storage). Every process binds
`0.0.0.0` on the internal port 8900 — `CONTAINER_PORT` in `module_monitoring/config.py`, with no
argument: the server is docker-only; `PORT` is only the host side of the
dashboard's mapping, so a stage run with another `PORT` never recreates a
resident. Every container runs as the host user — `user: ${UID:-1000}:${GID:-1000}`,
fed by the Makefile's `COMPOSE_ENV` — so nothing it writes is root-owned.

`make docker-up` builds the image if needed, starts the dashboard and the
residents, and opens the page; `make on` is its presentation alias, `make off`
that of `make docker-down`. `make docker-all` then runs the whole chain through them,
download to snapshots. Locally, every per-asset stage runs inside its asset's container: the
fan-out does an idempotent `up -d`, then `docker compose exec -T asset-<ticker>
sh -c 'python -m module_<x>.<stage> --tickers $ASSET'` — ingest one container at
a time, the ML stages `JOBS` at a time — so the container the tab measures is
the one doing the work. The residency is the fan-out's, not the stage's: the
command inside the quotes is the whole one-off form and runs the same outside any
container, and that one macro line is the only place a resident is assumed for
compute; `record.py` already tolerates a container that is gone. Replacing
exec-into-resident with a one-off launch is one line and touches no stage; the
panel would then measure a one-off instead of the resident. The direction is
`skill_pre_aws_solution.md`. `ASSET` is read by that command line and by `serve.py`
choosing its role; it is never the default of `build_ticker_parser`, and no
stage module reads it. The `COMPOSE` macro never gains `-f` or `COMPOSE_FILE`: one
compose file, every service visible in it. Adding an asset is one line in
`TICKERS` and three lines under `x-server`.

## The server

`module_monitoring/serve.py`, one file, two roles chosen by `ASSET`. The
dashboard role serves the static page, `GET /containers` — the registry:
`generated_at_utc`, `poll_interval_seconds` and `tickers` from
`module_data.config.TICKERS` — and `GET /containers/<TICKER>/status`, proxied to
`http://asset-<ticker>:8900/status`. The asset role answers `GET /status`.

The asset role never opens DuckDB: the database takes one whole-file lock per
process, so a second opener fails at once. The endpoint reads what is already
measured — the two snapshots' rows and blocks for its symbol, and `stat` of
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
`../module_monitoring/skills/skill_devops_panel.md`. What belongs here is what
the containers themselves owe it — the endpoint contract and the down semantics
above.
