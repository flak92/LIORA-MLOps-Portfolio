# Skill: asset containers — the plan of the asset-centric epic

The asset and its container become the primary object; the engine becomes the
support layer. This document is the approved plan for getting there: the
step-zero resolutions, the asset folder contract, the registry decision, the
container topology, the engine changes, the migration ledger with its gates,
and the design of the phase that follows. It is read by whoever executes a
stage of the ledger, in the same way `skill_agent_first_development.md` is read
by whoever changes anything. The ledger and the risk table are the plan's own
and leave with the closing stage; the folder contract, the topology and the
appendices stay as the normative description of the container layer and as the
starting point of the next epic.

Ratified and not up for debate: one image, N containers differing only by
`ASSET=<TICKER>`, per-asset compose services generated from the asset
registry, never hand-written. Ratified on 2026-08-29 and equally binding: a
resident container per asset starts making sense exactly when the asset gains
a continuous process — a live data-ingest loop; until then the badges need no
network, the dashboard reads the asset's state from the volume, and the
down/stale semantics stay the same.

Provenance of the technical claims below: six of them were verified against
primary sources before the plan was approved — the DuckDB 1.5.4 file lock, the
compose override auto-load, `deploy.resources.limits` without swarm, service
DNS and `run -T` exit codes, the cgroup v2 files, the stdlib proxy — and all
six hold; their record is in Appendix A so nothing is proven twice.

## 0. The phase boundary

| | Phase 1 — this epic: containerise without continuous delivery | Phase 2 — a separate work order, opened when the owner declares Phase 1 stable |
|---|---|---|
| asset containers | generated **job templates**, run as `docker compose run --rm -T asset-<ticker> …`; per-asset limits apply to `run`; nothing resident | the per-asset delivery loop as the resident process |
| dashboard | the bare `http.server` it is today; the Containers tab reads the two committed snapshots on the volume | the frozen endpoint/proxy design (Appendix A) enters unchanged |
| liveness | no container badge — a job container is ephemeral, so liveness is not a signal; **measured staleness carries the truth** | `up` / `down` with the endpoint's status-code semantics |
| never, in either phase | mounting `/var/run/docker.sock` in any container — root-equivalent access for a badge; publishing N ports | |

Phase 1 contains no continuous data delivery, no ingest loop, no poller, no
resident per-asset container, no `serve.py`, no proxy, no route, no endpoint
contract, no socket — and this plan mints no name, service, act row or code
path that exists only to serve them: a name is minted on the day its referent
exists. Phase 2 opens on the owner's declaration, after every Phase 1 gate is
green and the basket has run job-per-stage for a period the owner chooses.

Properties at the end of Phase 1: modular (one folder per asset), scalable
(adding an asset = one folder + one config + one registry line, settled by a
check), generic (one engine, zero per-asset code), deterministic (bit-parity of
the regenerable artifacts), containerised (one image; every per-asset stage
runs in that asset's job container). `make conventions-check` is green after
every commit of the epic.

Ground truth the plan rests on, read from the tree at `2dd0a36`:

- Every symbol holds 2,970,720 canonical 1m rows, `2021-01-01 00:00` to
  `2026-08-25 23:59`, and every symbol's raw maximum on both venues equals the
  global maximum — so the per-asset grid end (§7) is a no-op on the data as it
  stands. Binance raw 29,707,200 rows, Bybit 27,589,891; about 118 MB per
  symbol; 41,260 day-ZIPs. Host: 4 cores, 7 GiB, Docker 29.1.3, Compose 2.40.3,
  cgroup v2, duckdb 1.5.4; the image has neither `git` nor `curl`.
- `ingest.py` is basket-wide by design, and `AGENTS.md:31` lists "the
  basket-wide ingest" among the guards the mathematics requires — repealing it
  is a Values-level amendment (§1). `bars.py` is the only writer of the ML
  layer and sequential for that reason. `labels.load_research_1m` asserts the
  full 1m grid inside the frozen research window per asset — the gate that
  replaces the basket-wide one.
- `module_ml/status.py:257-284` writes `ml_status.json` from the parsed
  `--tickers` only, and the generated README's own reproduce line ends with
  that call — a latent defect, fixed in stage 2.
- `module_data/status.py:228` writes with `Path.write_text` (not atomic) and
  `dataset.write_json` derives its temporary name from the target — so a
  fanned-out fold of a tracked snapshot would be a race, not a convergence.
  Both status stages stay sequential (§7).
- The dashboard serves `module_monitoring/` only, so a Phase 1 badge is
  derivable from the two snapshots and from nothing else; what a badge needs,
  the sequential status writers publish (§6).
- `pill` already names the selector-button component of the page.
- The one workflow does exactly two things and the count is the rule, so a
  generated file is produced at invocation or does not exist.

## 1. Step zero — the act

| # | enacted today | resolution | form |
|---|---|---|---|
| Z1 | row 2 `store_assets_artifacts/` — rejected `assets/`, `artifacts/` | **the name stays and row 2 stays as written**: its why is about spelling and category and is still true. The folder still holds the artifacts of one asset — the DuckDB is generated from the raw tree by `ingest` exactly as the parquets are generated from the DuckDB. `store_assets/` beside a static front end reads as web assets, one name for two concepts; a `data/` sub-folder would break row 8's contiguous `<TICKER>_*` block | two checkable block lines: `rejected_name store_assets \| path_segment \| 2 \| the store is store_assets_artifacts/` and `rejected_name data \| path_segment \| 8 \| a per-asset file carries the <TICKER>_ prefix; the folder is flat` — both green today |
| Z2 | row 9 "OHLCV lives only in DuckDB; the asset folder publishes no price series" — why: one home, every stage reads it there; a published copy nothing reads is weight without function | **the why survives with a changed address**: the DuckDB moves into the asset folder as `<TICKER>_research_ohlcv.duckdb` — still one home per asset's market object, every stage still reads it there, no copy is published, and the central file ceases to exist so no reader is left for it | row 9 amended to *OHLCV lives only in DuckDB, and that DuckDB is the asset's own: `<TICKER>_research_ohlcv.duckdb`. The asset folder publishes no copy of it.* Not: a per-asset OHLCV parquet, an `export` stage, a central `store_db/`, a `data/` sub-folder, `<TICKER>.duckdb`, `<TICKER>_db.duckdb`, a per-asset raw tree. Row 3 is repealed by number — the cell says *repealed by row 9's amendment* — and the block's `db` / `database` fix cells name row 9 and the per-asset file |
| Z3 | "ONE canonical DuckDB", and the basket-wide ingest | **one canonical DuckDB per asset.** The carriers: `AGENTS.md:31` (a Values-level repeal), `:64`, `:96`; `README.md:6-7, 22, 116, 128, 134-135`; `methodology_data.md:5, 10, 168, 173`; `methodology_ml.md:370, 383`; `glossary.md:31`; act rows 3 and 9, the manifest prose, block lines `db` / `database`; `EXAMPLE_TICKER_README.md:11-12`; `skill_computing_optimisation.md:21-22`; `visualisation_config.json:64-65`; `module_data/__init__.py:1`, `config.py:48`, `ingest.py` docstring and `:196-204`, `status.py:3, 118-120, 214`; `module_ml/config.py:12`, `bars.py:3-5, 54`, `features.py:94`, `labels.py:154`, `strategy.py:56`, `status.py:247` (and through it the ten `<TICKER>_README.md`); `index.html:10`; `.gitignore:4`; `Makefile:52` | a new row: enacted *per-asset ingest — the canonical grid end is that asset's own raw maximum*; not *a basket-wide ingest over one shared database*; why *the guard existed because one file forced one grid end; with one database per asset there is no shared resource left to protect, and the frozen window plus `labels.load_research_1m`'s full-grid assertion is what gates the research layer*. `AGENTS.md:31` drops the phrase in the same commit |

**When the rows land.** Approval of this plan is step zero. Every row and every
carrier — normative and code alike — lands in the commit that makes it true,
which is the act's own rule (*a new decision enters this act in the commit
that enacts it*) and the contract's (`AGENTS.md:6`). An act-only first pull
request would have made the contract describe a tree that does not exist for
the length of two pull requests.

Vocabulary discipline (row 25): no coinage. The directory is *the asset folder*
(the act's term) and the running thing is *the asset container* (Docker's term;
in Phase 1 the job container a stage runs in); `capsule` is recorded once, as a
rejected form, and is not banned. The status chip is a *badge* (`pill` is the
selector component). Compose services are `asset-<ticker lowercase>`. The
generator module is `module_containers/`.

## 2. The asset folder contract

`store_assets_artifacts/<TICKER>/` holds **ten manifest files**, three of them
tracked, plus the asset's database — resident in the folder, outside the
manifest. The listing is `LC_COLLATE=C` order; `<TICKER>_README.md` keeps its
row-14 exemption (ninth under `en_US.UTF-8` once the folder holds ten files —
the row's parenthetical moves from eighth); every other new name sorts
identically by byte and by locale.

| file | holds | written by | tracked |
|---|---|---|---|
| `<TICKER>_README.md` | what the folder holds and what came out of it | `module_ml/status.py` | yes |
| `<TICKER>_config.json` | **new — the asset's hand-written input**: its registration in the folder (§3) and the engine overrides it takes. No schema, no key set, no unknown-key refusal: a key enters on the day a stage reads it and an asset sets it. All ten are `{}` | hand-written | **yes** |
| `<TICKER>_features_ss-15-hh-dd-MM.parquet` | X, 15m | `features.py` | no |
| `<TICKER>_features_ss-mm-01-dd-MM.parquet` | X, 1h | `features.py` | no |
| `<TICKER>_features_ss-mm-04-dd-MM.parquet` | X, 4h | `features.py` | no |
| `<TICKER>_label_events_ss-15-hh-dd-MM.parquet` | Y | `labels.py` | no |
| `<TICKER>_model_evaluation.json` | classification per fold | `train.py` | no |
| `<TICKER>_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-sample probabilities | `train.py` | no |
| `<TICKER>_parameters.json` | the a-priori configuration and the search result — derived, written by `hpo.py` | `hpo.py` | yes |
| `<TICKER>_strategy_evaluation.json` | threshold, PnL, equity curve | `strategy.py` | no |
| resident, not in the manifest: `<TICKER>_research_ohlcv.duckdb` (with its `.wal` during a write and `.tmp/` when DuckDB spills) | the market object's one home for this asset: `ohlcv_1m_binance`, `ohlcv_1m_bybit`, `ohlcv_1m_canonical`, `ohlcv_{15m,1h,4h}_canonical` | `ingest.py`, `bars.py` | no |

The database is not a manifest entry, and the act row says why: `FILE_MANIFEST`
drives the README's size column, the README is promised byte-reproducible for
an unchanged experiment, and a size that moves with every top-up would break
that promise on a tracked file. The four manifest sites — the act's manifest
section, the register's Artifacts table, `FILE_MANIFEST`, the store guide — go
from nine to ten files in one commit (stage 1) and gain the resident-database
sentence in stage 2.

`<TICKER>_config.json` sits beside `<TICKER>_parameters.json` because the input
cannot be a section of the parameters file: `hpo.py` writes that file, and
*derived, never drafted* forbids hand-editing it. Row 10 is amended to *two
files per asset, one drafted and one derived*; `<TICKER>_indicators.json`
stays rejected as a third file — a section, on the day one is needed. The key
families the epic intends for the config — venues, date bounds, barrier
parameters, indicator selection — are recorded in the act row; none has a
per-asset reader today, so none is minted.

Refusals kept from the first draft: no `data/` sub-folder (row 8); the raw
store stays central and Lean-exact (row 6; both downloaders already take
`--tickers`); every container keeps the `.:/app` bind mount — a per-folder
mount would be a precautionary guard. New path descriptors, in the modules'
`config.py` and nowhere else: `asset_config_json(ticker)` (mirroring
`asset_readme_md`) and `research_ohlcv_duckdb(ticker)` (the stem the central
file carried).

## 3. The asset registry

| option | for | against | decided |
|---|---|---|---|
| **A. `TICKERS` stays the tracked list in `module_data/config.py`; `<TICKER>_config.json` is the folder-side registration; a ninth check settles that the two agree** | one local definition and a predictable derivation (`AGENTS.md` § Canonical vocabulary): the folder, the raw leaf, every artifact path and now the compose service derive from one tuple; the definition of the experiment stays in the git index; the basket order stays a decision, so the two snapshots keep their row order; the act declares, the verifier settles | adding an asset is one folder, one config and one line | **A** |
| B. directories as truth via `iterdir()` | one folder and one config, literally | reads the working tree, which `check_conventions.py:83-87` refused in writing; an untracked folder joins the basket unseen by the index-based check; I/O behind a constant name; the basket order silently becomes alphabetical | rejected form |

The check is the ninth function of `check_conventions.py`, `ticker_registry`:
`TICKERS` equals the set of folders holding `<TICKER>_config.json`, both ways.
It reads `module_data.config.TICKERS` — stdlib-only, the same import the
Makefile already makes without the virtual environment — and the check still
carries no list of its own. `ticker_manifest`, with the new
`ticker_tracked_file` row, bounds each folder to exactly README, config and
parameters. `ASSET` is not made the default of `ticker_parser`: the fan-out
passes `--tickers` explicitly on every path, `module_data/config.py` stays a
file of plain values, and an environment variable does not become an implicit
input to nine stages. In Phase 1 `ASSET` is the one field that makes one
generated job template differ from the next and is read by no code — the act
row says so; the Phase 2 endpoint is its reader.

## 4. The data path

| option | for | against | verdict |
|---|---|---|---|
| **C. the dashboard reads the asset's state from the volume** — the two committed snapshots, extended by the sequential status writers | zero networking, zero new process; the page keeps reading two snapshots by literal name; the down/stale semantics are carried by measured staleness | no liveness signal — which in Phase 1 is not a signal at all | **Phase 1's law** |
| **A. a dashboard-side stdlib proxy to a resident per-asset endpoint** | meets "over the compose network" literally; one origin, no CORS, loopback stays; no dependency | needs a resident process per asset, which exists only when the asset has a continuous delivery loop | **Phase 2's law** — frozen in Appendix A with its verification record; enters unchanged |
| B. publish N ports | no proxy | port sprawl, CORS, N origins | rejected |

The requirement that the dashboard retrieve an asset's data from that asset's
container over the compose network is re-phased to Phase 2, coupled to
continuous delivery. Every mechanism of option A — the proxy, the lock
analysis, the down semantics, the exception set — is carried over frozen.

## 5. Topology, the generated compose file, `module_containers/`, the names

### One image, N job templates, two services

| service | image | role | lifetime |
|---|---|---|---|
| `pipeline` (stays) | `build: .` and `image: mlops-portfolio-1m-pipeline` — the name `USER_AGENT` already carries; the one build | `run --rm -T` one-offs for the basket-wide stages: `data-download` (sequential — the venues' per-IP limits are budgeted per process), `data-status`, `ml-status`; `init: true` | one-off |
| `dashboard` | `image: mlops-portfolio-1m-pipeline` | `python -m http.server ${PORT} --bind 0.0.0.0 --directory module_monitoring` — unchanged; `init: true`; published on `127.0.0.1:${PORT}` | long-running; the only service `docker-up` starts, as today |
| `asset-<ticker>` × N — generated job templates | `image: mlops-portfolio-1m-pipeline`, no `build:` — so `docker images` shows one image | `environment: {ASSET: <TICKER>}`, `init: true`, `deploy.resources.limits.memory: 5g`, no `command:` — the template is never started by `up`; every per-asset stage runs as `docker compose run --rm -T asset-<ticker> python -m module_<x>.<stage> --tickers <TICKER>`, the exact shape of today's twins with a per-asset service name | exists while a stage runs |

`init: true` wherever a process runs: a stage as PID 1 has no SIGTERM handler,
so `docker compose down` or an interrupt would wait out the stop timeout and
kill it mid-write; one compose key, no code. The memory limit: Compose v2
applies `deploy.resources.limits` to `run` containers on a plain invocation
and never with `--compatibility`; one mechanism only, never `mem_limit` beside
it, no `reservations`, no CPU quota — determinism already comes from the frozen
thread caps. `5g` sits above DuckDB's unchanged `4GB` ceiling:
`DUCKDB_MEMORY_LIMIT` stays as it is and `module_data/config.py` stays plain
values. What the limit bounds is a runaway non-DuckDB allocation; what bounds
concurrency is `JOBS`, as today. No resident containers means no idle cost, no
restart policy and no liveness.

### The generated file: `docker-compose.override.yml`

| option | for | against | decided |
|---|---|---|---|
| **A. `docker-compose.override.yml`, gitignored, regenerated by `containers-generate` before every compose target** | compose loads it by itself — no `-f` plumbing; regenerated at every use, so it cannot drift — no `--check`, no workflow step; an ecosystem-fixed name | the ten job templates are not in the tracked tree, so the picture cannot draw them — said in the act row's why and in the `docker-compose.yml` description of `visualisation_config.json` | **A** |
| B. a committed generated file plus a `--check` in the workflow | visible | a third thing in the one workflow | no |
| C. `docker-compose.assets.yml` passed with `-f` | explicit | `assets` is a rejected segment; plumbing in every target | no |
| D. ten hand-written blocks | tracked, drawn | the same knowledge ten times; generation is ratified | no |

Verified: with no `-f` and no `COMPOSE_FILE`, compose appends exactly one
override found beside the base, in the fixed preference `compose.override.yml`,
`compose.override.yaml`, `docker-compose.override.yml`,
`docker-compose.override.yaml`; a service defined only there is added. The
legacy name is guaranteed by compose-go's `DefaultOverrideFileNames` (v2.9.1,
pinned by the binary) and documented only as `compose.override.yaml` — the one
implementation-defined dependency of the design, recorded. Invariants, stated
in the act row and in the Makefile: the `COMPOSE` macro never gains `-f` or
`COMPOSE_FILE`; exactly one override file; no `compose.yaml` base; the override
defines new services only. The generating recipe ends with its own proof:
`docker compose config --services` must list every `asset-*`, or the target
fails.

Makefile wiring that keeps `make help` intact (its grep needs `target: ##` on
one line): one added rule line naming every `docker-*` target as depending on
`containers-generate` — a prerequisite line without `##` is invisible to the
help grep and to the checker's target pattern — `containers-generate` in
`.PHONY`, the block line `make_stage_prefix containers-`, and a docker fan-out
macro that reads the service names from the generator's own descriptor
(`ASSET_SERVICE_LIST`, a `python3 -c` beside `TICKER_LIST`) — never a
lowercasing at the point of use.

### `module_containers/` — the generator, a twin of `module_visualisation/`

| file | responsibility | imports |
|---|---|---|
| `config.py` | the compose vocabulary in one place: `ASSET_CONTAINER_IMAGE`, `ASSET_CONTAINER_MEMORY_LIMIT_GIB`, `service_name(ticker)`, the job-template dict | stdlib and `module_data.config` (stdlib) |
| `generate.py` | registry in, `docker-compose.override.yml` out (atomic write, sorted keys, `\n` endings), then the `config --services` proof | stdlib |

Non-runtime in Phase 1: nothing imports it while the pipeline runs. The
module map in `AGENTS.md` becomes *six project modules — three runtime modules
in dataflow order, and three non-runtime modules*, and `story_map` gains
`"module_containers/": "S1"` in the same commit, because the generator refuses
a tracked path that belongs to no story.

### The names of Phase 1 — each enters the act in the commit that enacts it

| enacted | not | why |
|---|---|---|
| *the asset folder*; *the asset container* — in Phase 1 the job container a stage runs in | `capsule` (recorded, not banned), `pill` as a folder name | established terms; a coinage costs every reader a translation |
| compose services `asset-<ticker lowercase>`, generated job templates; `dashboard` and `pipeline` stay | `asset-BTC`, `asset_btc`, `btc`, `container-btc`, retiring `pipeline`, a resident `command:` | not DNS, which is case-insensitive: a `build:` service without `image:` takes `<project>-<service>` as its image name and image references are lowercase; the hyphen because the name is also a DNS label; the generator lowercases at the boundary as `lean.py` does |
| `image: mlops-portfolio-1m-pipeline`, built once by `pipeline` | eleven `build: .` services | "one image, N containers" must be true in `docker images` |
| `init: true` on every generated job template, on `pipeline` and on `dashboard` | a bare Python PID 1, a `signal.signal(SIGTERM…)` handler, a `restart:` policy | above |
| `module_containers/` | `module_compose`, `module_docker` (a twin named after the tool), `module_capsule`, `module_asset`, the generator folded into `module_visualisation`, an endpoint inside this module | one responsibility with a stable boundary |
| `docker-compose.override.yml`, generated and gitignored; make target `containers-generate` | a committed override with a `--check`, `docker-compose.assets.yml`, `docker-containers-generate` (circular: the generator runs on the host before compose reads what it wrote) | above |
| `<TICKER>_config.json`; `TICKERS` stays the list; the check `ticker_registry` | `<TICKER>_indicators.json`, an `iterdir()` registry, a schema with no reader, `ASSET` as the parser default | §§2–3 |
| `<TICKER>_research_ohlcv.duckdb`, resident, not a manifest entry | a `data/` sub-folder, `<TICKER>.duckdb`, `<TICKER>_db.duckdb`, a README size line for it | §2 |
| per-asset ingest; `ml-bars` fans out; `data-download` stays sequential | a basket-wide ingest; a fanned-out download | §1 Z3; the venues' per-IP limits |
| `ASSET` — the container environment carries exactly one project name, a ticker in capitals; the contract's enumerated collision scopes gain *container environment variables* | `TICKER`, `SYMBOL`, a per-asset `.env`, mounting `/var/run/docker.sock` in any container | the container is the asset; the register carries the equation *ASSET (environment) = ticker (code, key, folder)*; the socket is root-equivalent access for a badge |
| `badge`; `badge--warn` marks a stale measurement | `pill` (bound to the selector component), `chip`, `tile`, `stat`, `badge--down` (Phase 2), reusing the `.warn` cell utility on a badge | established terminology; `.warn` is a table-cell utility set by `appendCell` and stays single-class |
| tab *Containers*; `module_monitoring/containers.js`; `DATA_STATUS` beside `ML_STATUS` as the page's two payload globals | `asset_containers.js`, a second fetch of `data_status.json` | `<subject>.js` beside `data.js`; one fetch feeds every tab |
| snapshot keys: per-symbol `last_observation_utc` and `db_bytes` in `data_status.json`; per-asset `manifest_complete` and `model_evaluation_modified_utc` in `ml_status.json` | `lag`, `fresh`, `stale`, `hash`, a per-asset timestamp in the README | the key grammar; the README stays byte-reproducible; the two snapshots are where the register one-liner already looks, so the keys are checked |
| the External-vocabularies row for docker compose extended: `run --rm -T`, `init`, `image`, `deploy.resources.limits`, `docker-compose.override.yml`, the DNS-label rule; owning files gain `module_containers/config.py` and `generate.py` | an unnamed boundary | the boundary table names every owning file |

Deferred to Phase 2, with no referent in Phase 1 and therefore not minted:
`module_monitoring/serve.py`; the routes; the endpoint keys and their
`unenforceable` row; the http.server and urllib boundary row and the `do_GET`
pre-sweep extension; `compose_network`; `badge--down`;
`asset_status_url(ticker)`; the runtime import of `module_containers.config`
by the dashboard. All are listed in Appendix A.

## 6. The Containers tab of Phase 1 — read from the volume

Same tab, same badge component, same honesty rules — every value derived from
the two committed snapshots the page already fetches; no new server, no new
process, no new fetch. A badge that cannot be derived from the snapshots
belongs to Phase 2, not to a workaround.

Untouched: the four tabs, `ml.js`, `asset.js`, the picture. Touched by
necessity and stated: `data.js` (`DATA_STATUS = status` beside `ML_STATUS`;
`db_bytes` moves from the envelope to the per-symbol rows and the Pipeline
meta line sums them client-side); `index.html` (one section); `style.css`
(`.badge`, `.badge--warn`).

Layout: the existing pill-group component as the asset selector, declared in
`index.html` (`data-pills="container"`) so `initPills(document)` binds it at
load and injected buttons work through the existing delegation — the buttons
follow `DATA_STATUS.symbols`, which is `TICKERS` order; one `.frame` per
selected asset with a row of badges, then that asset's two snapshot rows
verbatim in a `.box`.

| badge | shows | Phase 1 source | rule |
|---|---|---|---|
| data | `last_observation_utc`, and the observation lag as days and hours | the symbol's `canonical_source` row (stage 2 adds `last_observation_utc`); lag = client clock minus the last observation | `.badge--warn` above one day, the download cadence |
| rows | canonical 1m rows | the symbol's `symbols` row, `row_count` | — |
| window | `covered` / `not covered` | client-side: `window_start_utc` at or before `research_window.start_utc`, and `last_observation_utc` at or after `research_window.end_utc` minus one minute — exact, because the canonical grid has no holes by construction | presentation arithmetic, per the dashboard skill |
| artifacts | `complete` / `missing`, and the last train date | the asset's `manifest_complete` and `model_evaluation_modified_utc` in `ml_status.json` (stage 2 adds them in the sequential writer) | — |
| threshold | `met` / `fallback` | `strategy.entry_edge_threshold_constraint_met` | — |
| **measured** | the measurement age in hours | the two snapshots' `generated_at_utc` against the client clock — Phase 1's truth signal: a stale snapshot looks stale, never fresh | `.badge--warn` above `MEASUREMENT_AGE_WARN_THRESHOLD_MINUTES` — 1,440, the cadence the owner sets, a literal in `containers.js` (the browser's boundary) |
| container up / down | does not exist in Phase 1 — no residents, no socket | enters in Phase 2 with the endpoint's status-code semantics | — |
| a symbol with no snapshot row | `no data yet` | both snapshots | never `down` |

JavaScript, from the closed verb list: `buildContainerPills`,
`initContainers`, `renderContainer`, `buildBadge`, `formatDuration`,
`selectContainer`. Verification of stage 4: a headless render with every
badge present from the snapshots; a doctored old `generated_at_utc` renders
*measured* as `.badge--warn`; a symbol removed from the snapshot renders
`no data yet`; the four old tabs byte-identical in the DOM dump; the
JavaScript-verbs one-liner empty; the register one-liner `[]`. The
stopped-container drill leaves with the thing it tested and returns in Phase 2.

## 7. Engine changes, per stage

| stage | today | after |
|---|---|---|
| `download_*` | `--tickers`; sequential | unchanged; runs in `pipeline`, never fanned out |
| `ingest` | basket-wide, one database, grid end = the global raw maximum | `--tickers`; `research_ohlcv_duckdb(ticker)`; grid end = that asset's own raw maximum. The replacing invariant: within one asset the two venues share one grid end; across assets the ends may differ; the research layer is unaffected because its window is frozen and `labels.load_research_1m` refuses an asset whose grid does not cover it. Fan-out becomes legal |
| `data-status` | one scan of one database, written with `write_text` | one sequential process opening the ten databases in turn, read-only; `window_end_ms` stays the maximum across assets, so `expected`, `coverage_pct` and the gap counts keep grading every asset against the basket window — a lagging asset shows gaps, never 100 %; per-symbol rows gain `last_observation_utc` and `db_bytes`; the envelope `db_bytes` is retired (one name, one referent); the write becomes atomic with a per-process temporary name |
| `ml-bars` | the single sequential writer | one database per asset — fans out like the other ML stages; `skill_computing_optimisation.md` amended |
| `features`, `labels`, `hpo`, `train`, `strategy` | `STORE_DB_PATH` | `research_ohlcv_duckdb(ticker)` — one line each; nothing else changes, which is what bit-parity requires |
| `ml-status` | writes `ml_status.json` from the parsed tickers | `--tickers` scopes the READMEs only; the payload always folds over `TICKERS` with a complete artifact set — sequential; per-asset `manifest_complete` (every regenerable manifest file exists) and `model_evaluation_modified_utc` |
| Makefile | the `docker-*` twins run `pipeline` | per-asset twins `run --rm -T asset-<ticker> … --tickers <TICKER>`, fanned out by `xargs -P $(JOBS)` (exit 123 on any failure is the target's failure signal); `docker-data-download`, `docker-data-status` and `docker-ml-status` keep `run --rm -T pipeline`; `docker-up` unchanged; the `containers-generate` dependency line; `all` unchanged in order (row 17) |

Bit-parity of the regenerable artifacts holds structurally: the forward-fill
window is backward-only and per-symbol, so rows after `RESEARCH_END_MS` cannot
reach rows before it; `bars.py` bounds its aggregation to the research window;
`labels.py` and `strategy.py` apply the same bounds; `features.py` reads only
the bar tables. The two symbol-crossing sites in the tree are the union
maximum in `ingest.py` (now per asset) and the basket window end in
`status.py` (kept).

## 8. The migration ledger

Each stage is one pull request: a branch, commits with `make conventions-check`
green after every one, a push, and a review message (goal, what is in it, what
to attack, the state of the gate). A stage that depends on the previous stage's
validation starts after that pull request is accepted.

| # | branch | contents — every act row and carrier lands with the thing it names | the gate | rollback |
|---|---|---|---|---|
| 0 | `docs/asset-centric-plan` | this document; the picture regenerated | `conventions-check`; `visualisation-check`; a grep of §§0–10 for serve, route, proxy, poller, socket and resident finds only the phase-boundary statements and the appendix pointers | close the pull request |
| 1 | `feature/asset-registry` | ten `<TICKER>_config.json` holding `{}`; the `.gitignore` whitelist line; `asset_config_json`; the check `ticker_registry`; the act: row 10 amended, row 14's parenthetical, `ticker_tracked_file <TICKER>_config.json`, `enacted_path`, the two `rejected_name` lines of §1 Z1; the four manifest sites from nine to ten; the store guide | `conventions-check` green; `make data-status ml-status` leaves both snapshots byte-identical | revert; additive |
| 2 | `feature/duckdb-per-asset` | `research_ohlcv_duckdb`; ingest per asset; every reader; `status.py` sequential over ten databases with the two per-symbol keys and the atomic write; `data.js`; the `ml-status` fold fix with `manifest_complete` and `model_evaluation_modified_utc`; the register for the four keys; `bars` fan-out; act rows 3 (repealed by number) and 9, the per-asset-ingest row, the block fix cells; every Z3 carrier including `AGENTS.md:31` and `Makefile:52`; the README template line, so the ten READMEs regenerate; the resident-database sentence at the manifest sites; `.gitignore` keeps `store_db/` until stage 5 | precondition: per symbol, `max(timestamp_ms)` over both raw tables equals the global maximum (true today) — otherwise the forward-fill tail legitimately differs and only tier 1 binds. **Tier 1, all ten, minutes**: attach the central and the per-asset file read-only in one session and compare `count(*)` and `bit_xor(hash(timestamp_ms, open, high, low, close, volume, source, zero_volume))` over the research window, plus `count`, `min` and `max` of both venue tables per symbol. **Tier 2, BTC first**: `bars features labels train strategy status --tickers BTC` with the committed parameters — `hpo` excluded, because it reads parquets, never the database, and would rewrite two tracked files — then `sha256sum` of the six regenerable artifacts against the pre-migration hashes and `git diff --quiet -- store_assets_artifacts/`; then the nine. The snapshots gain keys, so their check is a keyed comparison of the ten blocks, not byte-parity — the exemption named. Cost: the rebuild about 0.2 core-hours (about 4 minutes at `JOBS=4`, I/O-bound), tier 2 about 0.03 core-hours per asset — measured on BTC and written into the pull request | the central file stays on disk, ignored and unread, until the owner deletes it; `git revert` restores the readers |
| 3 | `feature/module-containers` | `module_containers/{__init__,config,generate}.py`; `docker-compose.yml`: `pipeline` gains `image:` and `init`, `dashboard` gains `image:` and `init`, its command unchanged; `.gitignore` gains `docker-compose.override.yml`; the Makefile (`containers-generate`, the dependency line, `ASSET_SERVICE_LIST`, the per-asset `run --rm -T` twins); the act rows (module, services, image, init, override, prefix, `ASSET` with the socket rejection, the boundary row); the contract's module map and scope sentence; `story_map` and the descriptions; the picture | `make containers-generate` proves the load; `make docker-build` builds one image; `docker compose config` renders `memory: "5368709120"` for every `asset-*`; on a run container — `docker compose run -d asset-btc python -m module_ml.features --tickers BTC`, then `docker inspect --format '{{.HostConfig.Memory}} {{.HostConfig.Init}}'` on it — `5368709120 true`, and the parquets it writes are bit-identical; `make docker-ml-all` from a fresh clone after `docker-build` succeeds with nothing started by hand; `conventions-check` green | revert; the override is gitignored |
| 4 | `feature/containers-tab` | the `index.html` section; `containers.js`; `.badge` and `.badge--warn`; `DATA_STATUS` in `data.js`; the act rows for the badge, the tab and the script; the dashboard skill names the tab in one sentence — "reads two committed snapshots" stays true | the headless render of §6; the four old tabs byte-identical in the DOM dump; the JavaScript-verbs one-liner empty; the register one-liner `[]` | revert |
| 5 | `docs/containers-closing` | precondition: the owner has deleted `store_db/research_ohlcv.duckdb` — a manual step, never automated; `.gitignore` drops `store_db/`; this document trimmed to its normative part (the folder contract, the topology, the appendices); the README's topology paragraph; the picture | `conventions-check`; `visualisation-check` | — |

The invariant of the transition: a reader reads exactly one home. Stage 2
switches every reader in one commit and its gate covers all ten assets before
the merge; between that merge and the owner's deletion the central file is
ignored and unread — a backup, not a second home.

## 9. Risks, and the decisions taken

| risk | mitigation |
|---|---|
| Phase 2 leaking into Phase 1 | the grep clause of stage 0; a deferred name has no referent, so the reachability and manifest checks help; Appendix A is the only place those names appear |
| badge honesty without liveness | measured staleness is the designated truth signal — a stale snapshot must look stale; contract, not styling |
| a DuckDB lock between concurrent openers | one file per process; the only overlap possible is a human running `data-status` during `ingest`, as today |
| a race on a tracked snapshot | there is no fold: both status stages stay one sequential process; the write is atomic with a per-process temporary name |
| N job containers and memory | a `5g` limit above DuckDB's unchanged ceiling; concurrency bounded by `JOBS` |
| a half-migrated state | a one-commit reader switch and a two-tier per-asset gate before the merge |
| act churn, a contract that lies | no act-only pull request; every row lands with the thing it names |
| the override name is implementation-defined | `docker compose config --services` in the recipe fails loudly on a rename |
| limits verified from source, not on a running container | the stage-3 `docker inspect` on a run container |
| 1.18 GB untracked during the epic | `store_db/` stays ignored until the closing stage, after the deletion |
| a venue lags one symbol after the migration | expected and stated: that asset's series ends earlier, its `coverage_pct` drops against the basket window, and `covered` stays true while the frozen window is covered |
| the frozen Appendix A design rotting before Phase 2 | it ships here with its verification record; the Phase 2 work order starts from it, not from zero |

Decisions taken by the owner on 2026-08-29:

| decision | decided |
|---|---|
| step zero | approval of this plan settles Z1–Z3; every row lands with the code; no act-only pull request |
| registry | the `TICKERS` list with the `ticker_registry` check; the basket order kept |
| per-asset limits | memory `5g`, no CPU quota; "no limits" recorded as the rejected form |
| the plan's home | this document, trimmed in the closing stage |
| phasing | containerise first — generated job templates, badges read from the volume, no residents, no socket; continuous delivery and the frozen endpoint design later, in their own work order, opened on the owner's stability declaration |

## 10. Cut, deferred, rejected

Cut in review of the first draft: a closed config schema with an unknown-key
refusal and a feature-family registry; a status endpoint inside the generator
module; a per-asset data status file with a fanned-out fold; `iterdir()` as the
registry; `ASSET` as the parser default; an alphabetical basket order;
`exec -T`; eleven `build:` services; a CPU quota; a derived
`DUCKDB_MEMORY_LIMIT`; a `restart:` policy; a resource footprint block; a
parameters hash; a body on the 503 answer; a 404 branch; a second timestamp
name; a poll timer; an act-only step-zero pull request; the `methodology_`
family for this document; banning `capsule`.

Deferred to Phase 2, not cut: the endpoint and proxy design (Appendix A, frozen
with its verification record); resident asset containers; the container
`up` / `down` badge; `serve.py`, the routes, the endpoint keys, the http and
urllib boundary row; `badge--down`.

Rejected in both phases: publishing N ports; mounting `/var/run/docker.sock`
in any container.

## Appendix A — Phase 2: the frozen endpoint and proxy design

Enters when Phase 2 opens; nothing here is minted in Phase 1. The verified
claims it rests on:

1. **DuckDB 1.5.4 locking** — read in the source (the single-file block
   storage's open flags and the POSIX file system's `fcntl` call) and
   reproduced read-only on this repository's file: one whole-file lock per
   process at open, `F_RDLCK` for `read_only=True` and `F_WRLCK` otherwise,
   taken with one non-blocking `F_SETLK`; no retry, no timeout, no knob; any
   overlap fails immediately in both directions; the locks are kernel objects
   on the inode and cross containers over the shared bind mount; a read-only
   open of an absent file fails; nothing in 1.4.x or 1.5.x relaxes this, and
   the multi-process write paths (Quack, DuckLake) add a server process, which
   the dependency rule excludes. Frozen consequence: the endpoint never opens
   DuckDB; it reads the committed snapshots' rows for its symbol, the folder's
   artifacts and `os.stat`.
2. **The compose override auto-load** — as in §5.
3. **`deploy.resources.limits`** — applied by Compose v2 on a plain `up` or
   `run`, never with `--compatibility`.
4. **Service DNS** — a service is reachable by its name on the project network;
   lowercase because of the image-reference rule, not DNS; `run -T` and
   `exec -T` propagate exit codes; `exec` needs a running service.
5. **cgroup v2** — the container's files are readable as uid 1000;
   `memory.current` includes the page cache; the cgroup directory is resolved
   from `/proc/self/cgroup`; `memory.max` reads `max` when unlimited, in which
   case `MemTotal` is the ceiling. The footprint block stayed cut; the record
   is kept for the day it is wanted.
6. **The stdlib proxy** — `ThreadingHTTPServer` with a
   `SimpleHTTPRequestHandler` subclass, `directory=` injected through
   `functools.partial` (undocumented but sound: `socketserver.finish_request`
   accepts any callable); `protocol_version` left at `HTTP/1.0`; `do_GET` and
   `do_HEAD`; the exception order `HTTPError` first, then `OSError` and
   `http.client.HTTPException`, because `URLError` alone misses read-phase
   failures (CPython issue 89929); own headers only; GET and HEAD only;
   `timeout=` bounds each socket operation, not the exchange.

**Topology.** `module_monitoring/serve.py`, one file, two roles chosen by
`ASSET`. The dashboard role serves the static files, `GET /containers` — the
registry, served locally from `module_data.config.TICKERS`, carrying
`compose_network`, resolved once at start-up by resolving the service's own
name, so a page served from the host says *served outside the compose network*
instead of showing ten false `down`s — and `GET /containers/<TICKER>/status`,
proxied to `http://asset-<ticker>:${PORT}/status`. The asset role, with
`ASSET` set, answers `GET /status`. The asset service gains a `command:` — the
delivery loop and the endpoint — and becomes resident; `docker-up` starts
everything; `asset_status_url(ticker)` in `module_containers/config.py`
becomes that module's one runtime import, and the contract's module map is
re-worded to admit it.

**The endpoint contract.** The envelope carries `ticker` and
`generated_at_utc`, the register's one timestamp name. `data` carries the
measurement's own `generated_at_utc`, `row_count`, `last_observation_utc`,
`observation_lag_minutes` (is the market data behind?),
`measurement_age_minutes` (is anyone still measuring?), `db_bytes` and
`research_window_covered`; `null` renders as *no data yet*. `artifacts` carries
`manifest_complete`, `model_evaluation_modified_utc` and
`entry_edge_threshold_constraint_met`. No hash: git holds the identity. The
keys enter the register in a subsection of their own, with an `unenforceable`
line: no committed artifact carries them, so the register one-liner cannot
reach them; they are registered by review.

**Down semantics.** Cannot connect, name does not resolve, or the exchange
fails after the request was sent — HTTP 503 with no body. The page decides on
the status code alone; any non-200 renders the container badge `down` and every
other badge as a dash, never the previous numbers. There is no 404 branch: the
container knows one asset, so an unknown-ticker request cannot reach it. A
stopped container renders `down` after Docker's resolver gives up on the
vanished alias, not after the socket timeout — stated, not mitigated.
`Cache-Control: no-store` from the proxy; refresh on tab entry and on
selection; `measurement_age_minutes` says how old the numbers are.

**Names minted in Phase 2, with their rejected forms.** `serve.py` — not
`dashboard.py`, `proxy.py`, `server.py`; the routes `/containers` and
`/containers/<TICKER>/status` — not `/asset/status` beside
`/asset/<TICKER>/status`, one prefix admitting no reading in which `status` is
a ticker; `badge--down`; `compose_network`; the http.server and urllib boundary
row owned by `serve.py` (`ThreadingHTTPServer`, `SimpleHTTPRequestHandler`,
`do_GET`, `do_HEAD`, `send_response`, `send_header`, `end_headers`, `wfile`,
`directory=`, `urlopen`, `HTTPError`, `URLError`, `Cache-Control`), with the
act's pre-sweep grep extended by `do_GET` — a name on the forbidden side of the
I/O verb list that the `^def` one-liner cannot see; the DOM row extended by
`fetch`.

## Appendix B — Phase 2 charter

A charter, not a specification.

**Trigger.** The owner declares Phase 1 stable: every stage gate green, the
basket running job-per-stage for a period the owner chooses. The declaration
opens a new work order, and this appendix is its starting point.

**Scope.**

1. Continuous per-asset delivery — the resident process of each asset
   container: a loop that follows the venues' 1m feeds for its own asset into
   its own database on a cadence the work order defines; the Phase 1 job
   templates become resident services by gaining a `command:`.
2. The live endpoint and proxy — Appendix A enters unchanged, with the
   container `up` / `down` badge and the status-code semantics already
   verified.
3. Growing-timeframe transformations — scheduled stages that follow the
   growing 1m series across the 15m, 1h and 4h timeframes and overwrite the
   derived parquets on a defined cadence.

**Phase 2's step zero, named now and designed then: the live layer against the
frozen research window.** Today's artifacts are bound to the research window
and byte-reproducible for an unchanged experiment (`RESEARCH_END_UTC` is
frozen; the README carries no timestamp; the determinism skill makes identical
bytes the standard). A continuously overwritten parquet is neither. Before any
Phase 2 code: decide whether the live layer is a second, named family of
artifacts beside the frozen research ones — with its own manifest rows, its
own grammar for a moving window and its own truth signal — or whether the
research window itself moves; then amend the act, the methodology and the
determinism skill. Every carrier of *byte-reproducible* and *frozen research
window* is a Z-row of that step zero.

**Non-goals of the charter.** Designing the cadence, the transformation
schedule or the live-against-research split now; new dependencies; touching
Phase 1 stages 0 to 2; re-opening Z1–Z3.
