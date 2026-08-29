# Skill: asset containers — the topology, the endpoint, the tab

The asset and its container are the primary object; the engine is the support
layer. One image, one resident container per ticker of the basket, differing only by
`ASSET=<TICKER>`, every service written out in `docker-compose.yml` — the build, and the
dashboard and the assets under one anchor: `image`, `init`, `user`, `command: python -m
module_monitoring.serve`, the bind mount, the `5g` ceiling. The dashboard
reaches them only through its own proxy: no asset container publishes a port,
and no container mounts `/var/run/docker.sock` — root-equivalent access for a
badge. *The repository shows the destination, not the road*: no restart policy, no healthcheck, no socket.

## The topology

| service | image | role | lifetime |
|---|---|---|---|
| `pipeline` | `build: .`, `image: mlops-portfolio-1m-pipeline` — the one build | `run --rm -T` one-offs for the basket-wide stages: `data-download` (sequential — the venues' per-IP limits are budgeted per process), `ml-status` | one-off |
| `dashboard` | the anchor, plus `ports:` | the same server in its dashboard role, published on `127.0.0.1:${PORT}` only | resident |
| `asset-<ticker>` × one per ticker of `TICKERS` | the anchor, plus `environment: {ASSET: <TICKER>, OMP_NUM_THREADS: 1}` — no `build:`, so `docker images` shows one image | the same server in its asset role | resident |

`init: true` on every service: a Python process as PID 1 has no SIGTERM
handler, so `docker compose down` would wait out the stop timeout and kill a
stage mid-write; under a resident it also reaps the stages `exec` leaves
behind. `5g` sits above DuckDB's `4GB` ceiling and bounds a runaway allocation
outside DuckDB — the dashboard inherits it, harmlessly, opening no database;
concurrency is bounded by `JOBS`. One mechanism only — no
`mem_limit` beside it, no reservation, no CPU quota, and no restart policy,
because a failure is reported, not hidden. Every container keeps the `.:/app`
bind mount; the raw store stays central and Lean-exact. Every process binds
`0.0.0.0` on the internal port 8900 — `CONTAINER_PORT` in `serve.py`, with no
argument: the server is docker-only; `PORT` is only the host side of the
dashboard's mapping, so a stage run with another `PORT` never recreates a
resident. Every container runs as the host user — `user: ${UID:-1000}:${GID:-1000}`,
fed by the Makefile's `COMPOSE_ENV` — so nothing it writes is root-owned.

`make docker-up` builds the image if needed, starts the dashboard and the
residents, and opens the page. `make docker-all` then runs the whole chain through them,
download to snapshots. Every per-asset stage runs inside its asset's container: the
fan-out does an idempotent `up -d`, then `docker compose exec -T asset-<ticker>
sh -c 'python -m module_<x>.<stage> --tickers $ASSET'` — ingest one container at
a time, the ML stages `JOBS` at a time — so the container the tab measures is
the one doing the work. `ASSET` is read by that command line and by `serve.py`
choosing its role; it is never the default of `build_ticker_parser`, and the
engine never sees it. The `COMPOSE` macro never gains `-f` or `COMPOSE_FILE`: one
compose file, every service visible in it. Adding an asset is one line in
`TICKERS` and three lines under the anchor.

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
when the snapshots hold nothing for the asset; `db_bytes` is `null` while the
database is absent. The CPU rate the tab shows is the delta of two polls over
`cpu_count` — presentation arithmetic, never published. No hash: git holds the
identity.

**Down semantics.** Cannot connect, name does not resolve, or the exchange
fails after the request is sent — HTTP 503 with no body; a ticker outside the
basket — 404. The page decides on the status code alone: any non-200 renders
the container `down` and every other cell as a dash, never the previous
numbers. `Cache-Control: no-store` from the proxy. A stopped container renders
`down` after Docker's resolver gives up on the vanished alias, not after the
socket timeout — stated, not mitigated.

## The tab

The tab reads the registry and one endpoint per container through the proxy,
every `poll_interval_seconds` while it is visible and one poll at a time, and
shows an overview table — one row per asset container, magnitudes as bars —
then the selected container's badge row and its answer verbatim. The selector
is the page's pill group (`data-pills="container"`), its buttons following the
registry's `tickers`; the overview's ticker cells are links into it. `badge` is
the tab's element carrying one variable of an asset's state: `badge--warn` marks an
observation or a measurement older than `download_cadence_minutes` from the
data snapshot — never a literal in the page; `badge--down` a container whose
endpoint did not answer 200.

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
| trained | `trained <date>` | `artifacts.model_evaluation_modified_utc`; `artifacts no run yet` while the ML snapshot has no block |
| threshold | `met` / `fallback` | `artifacts.entry_edge_threshold_constraint_met` |
| measured | `measured` | `data.measurement_age_minutes` |
| cpu (badge) | `cpu <seconds>s on <n> cpus` | `footprint.cpu_usage_seconds`, `cpu_count` — the container's total so far |
| a symbol with no row | `no data yet` | `data: null` — never `down` |
