# Skill: Pre-AWS solution — local boundaries with a standard cloud equivalent

How a local academic repository is designed so that its local contracts — where
a function lives, who writes a file, what a stage takes as its parameter, how a
container is started — could later be mapped almost directly onto the standard
primitives of a cloud, here Amazon Web Services (AWS), without redrawing the
domain pipeline. It is not a deployment guide. The principle is `AGENTS.md`
§ Pre-AWS architectural direction; the names are `glossary.md` § Pre-AWS
direction; how a name is derived is `skill_self_explaining_naming.md`. *The
repository shows the destination, not the road*: the mapping is described here
and built nowhere — no infrastructure code, no storage adapter, no cloud noun in
a path. *Read forward*, below, means read as that mapping would read it: the
same object seated elsewhere, nothing moved. Every rule this document leans on
that is already written elsewhere is cited by path and section, never restated;
what is new here is the classification, the non-goals, the seats, the volume
and the copy, the ladder, the databases, the rebuild condition, one day told
forward, the mapping table with its verdicts, the rejected forms and the review
of the tree.

## Project status

LIORA is an academic, portfolio and research demonstration of an MLOps and
quant-research architecture. It is not a production trading system, not an AWS
deployment and not a production MLOps platform. The runtime is local — a venv,
or one `python:3.12-slim` image under docker compose, driven by a Makefile — and
the goal is a correct dataflow with visible responsibilities. The stance is
`AGENTS.md` § Values, *Academic, not production*; what it is and is not is
`../module_ml/skills/methodology_ml.md` § 12.

## The minimum demonstration

The proof of the architecture is the whole chain running end to end on a very
small representative basket: `BTC` today, optionally one to three more. Scale is
`ASSET=<TICKER>`, never hundreds of assets in a demonstration repository; a
basket grows by one line in `TICKERS` and one block under the compose anchor
(`../README.md` § The basket says how; this section says why it is enough). A
second asset proves the architecture; the hundredth proves nothing more.

## Non-goals, and the one rule behind them

Not built here, and not to be added because production would have it:

- no full automated test suite, no linter, no coverage gate, no CI/CD, no
  workflow, no framework;
- no security hardening, no production IAM, no secrets architecture, no network
  isolation;
- no high availability, no multi-AZ, no disaster recovery, no SLA, no
  autoscaling;
- no distributed locking, no production retries, no guardrails beyond the seven
  the mathematics requires (`AGENTS.md` § Values);
- no full observability platform, no Kubernetes, no API gateway;
- no infrastructure code: if `infra/` exists it is shaped by responsibility —
  compute, storage, orchestration, monitoring — its resources named
  `<project>-<environment>-<resource-role>`, `<project>` being `mlops-portfolio`
  as the image spells it, the role a deployment-view primitive id with `_` read
  as `-`; no second list of roles, no `dev` or `prod` in a name before it does.

**The rule.** A mechanism that exists only because production AWS would require
it, and that the academic logic does not need, is not implemented locally; its
future equivalent is described in this document instead. Stated, not mitigated.

## Every object is classified before it is placed

A name says what the object is before it says anything else, and the object sits
beside the objects of its class. Twelve classes, each with what answers to it
today:

| class | what it is | in this repository |
|---|---|---|
| SOURCE | an external observation fetched as it came | `module_data/download_binance.py`, `module_data/download_bybit.py` |
| INGEST | raw evidence materialised, unchanged, into the asset's database | `module_data/ingest.py` — the two venue tables |
| CANONICAL | the one research series built from the evidence, and its aggregations | `module_data/ingest.py` — `CANONICAL_INSERT`; `module_data/lean.py`, the raw format it is read from; `module_features/bars.py`, the tables of the same series on every timeframe of the register |
| STORAGE | where state lives, and the descriptors that name it | the `store_*` roots; every path descriptor of a `config.py` |
| FEATURE | the catalogue, a pure function of the canonical series | `module_features/catalogue.py`, `module_features/indicators.py` |
| LABEL | Y, resolved on the canonical path | `module_ml/labels.py` |
| MODEL | the two searches, the fit, the folds, the shared IO, and the hand's copy that fixes an asset's columns | `module_ml/hpo.py`, `module_ml/feature_set_search.py`, `module_ml/feature_set_promote.py`, `module_ml/train.py`, `module_ml/model.py`, `module_ml/validation.py`, `module_ml/dataset.py`, `module_features/dataset.py` |
| STRATEGY | the research evaluation of the predictions | `module_ml/strategy.py` |
| ORCHESTRATION | ordering and launching the stages — not `orchestration_seconds` of `glossary.md` § Run record, the wall time between two stages | the Makefile |
| MONITORING | measuring the runtime and presenting what the modules measured | `module_data/status.py`, `module_ml/status.py`, `module_monitoring/serve.py`, `module_monitoring/record.py`, the page scripts |
| STRATEGY EXECUTION | taking research artifacts and market data into a running strategy | absent here — described: `module_trading/`, its own container on the strategy host (§ Infrastructure seats) |
| INFRASTRUCTURE | the image, the topology, the engine's own views | `Dockerfile`, `docker-compose.yml`, `module_monitoring/sub_module_devops/`, `module_monitoring/sub_module_dx/` |

Group by who writes the state and how long it lives — never by "written
together", "same library", "same author" or "convenient". A name that does not
let a reader place the object without opening it is questioned; the eight
questions are `skill_self_explaining_naming.md` § The naming review. What is
forbidden: a module named for a cloud resource (`module_s3`, `module_ecs`), a
`worker`, a `processor`, a `helper` — a class token, never a mechanism token.

## Module boundaries are extraction boundaries

The mechanism is `AGENTS.md` § Architecture shape: each `module_*` is an
extractable bounded context. Read forward, each is the seam a separately run
container would sit on — never a cloud "service" of its own, and never a module
named for one.

- `module_data` — external market data → raw → canonical: the venues, the
  normalisation, the Lean raw format, ingest, the canonical OHLCV and the data
  quality needed to confirm it; no ML.
  `../module_data/skills/skill_candle_canonicalisation.md` § 1.
- `module_features` — canonical → the bars of the register → the feature
  catalogue, one parquet per timeframe; it receives a finished canonical object
  and asks nothing about a venue (`../module_features/README_module_features.md`
  § Where the responsibility stops). **That line is the future data-storage →
  feature-compute boundary.** Its one write across it is `bars.py`, named in
  § What stays as it is below.
- `module_ml` — the catalogue parquets and the canonical path → labels → search
  → model → predictions → strategy evaluation; its inputs are the catalogue and
  the canonical series, and nothing it writes crosses upward
  (`../module_ml/README_module_ml.md` § Where the responsibility stops).
- `module_monitoring` — existing state → representation, and nothing of the
  research process (`../module_monitoring/README_module_monitoring.md` § Where
  the responsibility stops). A status stage is MONITORING work owned by the
  module whose state it measures: `AGENTS.md` § Architecture shape.
- QuantConnect Lean — a format here, not a runtime. `module_data/lean.py` is the
  one external-format boundary, and the raw tree is written Lean-exact so a Lean
  backtest could read it directly
  (`../module_data/skills/skill_candle_canonicalisation.md` § 13); that is the
  whole of Lean's presence. No Lean runtime, container or dependency exists in
  this repository; § Infrastructure seats gives it its seat, and the deployment
view of the drawing draws it absent. Strategy execution, if it ever
  exists, is `module_trading/` — its own container beside `module_ml`, never
  inside it; the register keeps one Lean row, `glossary.md` § Market object.

## Infrastructure seats

Nothing here is built, tested or guarded for the move: the chain proves itself
by running (`AGENTS.md` § Values), and each seat proves a boundary by naming
what it would be a rename of. The seat of each thing is the cheapest that keeps
its boundary — one host, one volume, one image, no cluster, no queue, no
database process, no front until a reader outside the host appears — the
*Minimalism* of `AGENTS.md` § Values applied to infrastructure, and the reason
each row of § Rejected forms is refused.

One container raises four questions, and a different service answers each:

| question | layer | here today | elsewhere |
|---|---|---|---|
| where does the image live? | the image registry | `make docker-build` — `build: .` on the anchor, so a bare clone builds instead of reaching for a registry (`skill_asset_containers.md` § The topology) | a container image in a registry (Amazon ECR) |
| who runs the containers, and keeps the residents running? | the container service | `docker compose` — `run --rm -T` for a one-off, `up -d` for a resident | the service that runs the tasks (Amazon ECS) |
| on what machine does it physically run? | the compute | the developer's Linux, or a remote host reached through the tunnel (`../README.md` § Quickstart) | one Linux container instance with a durable volume, registered with the service above (Amazon EC2) |
| who decides what runs, when, and in what order? | the work orchestration | the Makefile — `all:`, `features-all:` and `ml-all:` the order, a hand typing `make docker-all` the when, no schedule | a state machine for the order (AWS Step Functions) and a schedule for the when (Amazon EventBridge Scheduler); no job queue |

The sentence to remember: the registry stores the image, the service runs it,
the instance hosts it, and the state machine says *now the next*.

Three questions choose each layer's form, and the tree answers each:

| question | answer here | what it decides |
|---|---|---|
| does a stage need the host's disk between runs? | yes: the database file under its whole-file lock, the raw ZIPs and the artifacts at one path, read and written through `.:/app` by every stage (`AGENTS.md` § Pre-AWS architectural direction, *Storage is separate from compute*) | a task on a host that holds a volume, never a task without a host — the instance (Amazon ECS on Amazon EC2), not the form without one (AWS Fargate) |
| how many hosts, how many services? | one host; four services — `pipeline`, `dashboard`, `asset-<ticker>`, `devops` (`skill_asset_containers.md` § The topology) | the container service on that host, not a cluster — Amazon ECS, not Amazon EKS |
| where does the host take the image from? | one image for every role, `mlops-portfolio-1m-pipeline`, the command and `ASSET` deciding the role (§ Docker is compute, not storage) | one registry, one image, its tag the commit it was built from (Amazon ECR) |

The task host and the store volume — one Linux container instance every asset's
runs share (Amazon ECS on Amazon EC2) and its durable disk mounted at `/app`
(Amazon EBS), every asset's folder and the other `store_*` roots. Today:
`.:/app`. The move: `.:/app` read as `<volume>:/app` in both lines; no stage
notices. A second asset is one more folder on the same volume. A rename.

The service that runs the tasks (Amazon ECS on Amazon EC2), the state machine
(AWS Step Functions) and the schedule (Amazon EventBridge Scheduler). Today:
`run --rm -T pipeline …`, the one line of `dockerfanout`, `all:`, `features-all:`
and `ml-all:`, `xargs -P $(JOBS)`, `RUN_ID`, a hand typing `make docker-all`. The move: one
task definition, run per stage with the command overridden and per asset with
`ASSET=<TICKER>` overridden — the exec into a resident becoming a task run, the
one edit § The mapping table names, where a mechanism changes and not a name;
the stages as states, a Map over `TICKERS` as wide as `JOBS`, `run_id` as the
execution name; the schedule judged in its own row. A second asset is one more
iteration of the Map, never a second definition. A rename.

The databases — one file per asset, `<TICKER>_research_ohlcv.duckdb`, the two
venue tables, the canonical table and its three aggregations under one
whole-file lock (§ The databases). On the volume: the same file at the same
path, the same process, nothing to edit — both descriptors, `artifact_dir()`
and `research_ohlcv_duckdb()` in `module_data/config.py`, resolve unchanged —
and after the run a whole copy to the asset's version prefix (Amazon S3). A
second asset is one more file under its own lock. A rename.

The strategy host — a separate Linux instance running QuantConnect Lean (Amazon
EC2), reading the copy, its brokerage credentials read once at start from a
secrets store (AWS Secrets Manager). Today: the Lean-exact raw tree; strategy
execution, when it exists, is `module_trading/`, its own container. A second
asset is one more prefix it reads. Absent here — described.

The supporting seats — the image registry (Amazon ECR), logs and metrics (Amazon
CloudWatch) as the recorder writes them, the readers behind the tunnel
(`../README.md` § Quickstart) — are their rows read forward: the one image; the
recorder's files when `RECORD` is set; `dashboard`, `devops` and
`asset-<ticker>` kept running on the task host behind a port-forward. A second
asset is one more `asset-<ticker>`. A rename.

Why the service on an instance and no other form: this repository agreed that a
container is compute and never the owner of state — the `store_*` roots on a
disk, one writer under a whole-file lock, `.:/app` the one mount — and Amazon
ECS on Amazon EC2 is the one form in which that agreement moves as a rename (a
host, a volume, a launcher) and not a rebuild; a task without a host, or on a
host the provider holds, takes the disk and the socket away, and a cluster adds
what one host does not need.

## The asset is a namespace, not infrastructure

`ASSET=<TICKER>` — `--tickers <TICKER>` at the process boundary — selects the raw
leaves, the canonical database, the features, the labels, the parameters, the
model and strategy evaluations, the asset README, the asset's rows of the two
snapshots and of the run record. No module, file, function, branch or service
definition is named for a ticker: `asset-<ticker>` is one instance of the asset
container, parameterised by `ASSET`, and adding an asset is one entry in
`TICKERS` and one block under the compose anchor — `AGENTS.md` § Canonical
vocabulary, *Rule-derived structure*. A ticker may name a convenience alias in
the Makefile, with its sunset note, never a target another file depends on.

## The asset folder is a prefix, read forward

`store_assets_artifacts/<TICKER>/` is, read forward, one prefix per asset. Every
per-asset file carries the `<TICKER>_` prefix and a time series carries its grid
in timeframe slots — `BTC_features_ss-15-hh-dd-MM.parquet`
(`skill_sorting_files_naming_standard.md` § The timeframe slot standard); the
file-by-file manifest is `glossary.md` § Artifacts and is not copied here.
Canonical storage and artifact storage share the folder today, both in
`module_data/config.py` — `research_ohlcv_duckdb()` built on `artifact_dir()`,
re-exported by `module_features/config.py` and `module_ml/config.py`; read forward the folder is
`artifacts/<ticker>/<version>/` in the copy, each key the descriptor's path
relative to `STORE_ASSETS_ARTIFACTS_DIR`: nothing to edit, no folder move. A new
local store is `store_<object>/`, never a bare `data/`, `artifacts/` or
`canonical/` (`AGENTS.md` § Rejected vocabulary). The raw tree is the model
case: written once, one UTC day per object, deleted to correct, its presence the
condition that skips a download (`../module_data/README_module_data.md` §
Stages; `../module_data/skills/skill_candle_canonicalisation.md` § 3) —
venue-major and lower case because Lean demands it (`AGENTS.md` § Architecture
shape). Read forward, the stores correspond to four prefixes —
`raw/<venue>/<symbol>/<day>`, written once; `artifacts/<ticker>/<version>/`, the
version the execution name; `runs/<run_id>/`; `status/` — a correspondence (§
The volume is the home, the store is the copy), not a local layout.

## The databases

The databases are one file per asset, `<TICKER>_research_ohlcv.duckdb` — six
tables, one writer at a time
(`../module_data/skills/skill_candle_canonicalisation.md` § 13, § 15), an
embedded engine under a whole-file lock (`skill_asset_containers.md` § The
server). Its ceiling is per process: `5g` above `4GB`
(`skill_asset_containers.md` § The topology; `DUCKDB_MEMORY_LIMIT` in
`module_data/config.py`), the sum of the concurrent ceilings being what has to
fit the host (`skill_determinism.md`, *A stage that is the only writer to a
shared resource stays sequential*). Read forward nothing changes: the same file
on the store volume, the same process, and after the run a whole copy to
`artifacts/<ticker>/<version>/`, a closed file.

A managed database earns its place at one threshold — the promotion threshold —
and not before: a second writer holding the file at the same time as the first,
or a query across assets. Neither exists: `data-ingest` is sequential, the ML
writer is one stage, and no table carries a `symbol` column (`glossary.md` §
Market object); a database process before then is § The chief antipattern, and
what would move past the threshold is the question of
`skill_database_promotion.md` (`AGENTS.md` § Skills absent here, described).

## Docker is compute, not storage

`../module_data/skills/skill_candle_canonicalisation.md` § 15 states it for the
database; it holds for every store. A container is never the owner of an asset's
state: it reads input, computes, writes output and may disappear; state stays in
the DuckDB file, the parquets, the JSONs and the raw ZIPs, under paths a
`config.py` names. The image, `mlops-portfolio-1m-pipeline`, is one runtime
package for every role — the command and `ASSET` decide the role, and no ticker
is in its name. It is a dependency layer (`Dockerfile`); the four `/store/<content>` mounts are
the store contract, and the `.:/app` mount carries the code (the image's, once
the image carries the code — § The retrain runtime is a ladder) and still
shadows the state under the `store_*` roots (`store_status/` among them, the
copy's prefixes) at `/app/store_<content>` — kept apart by the `store_*` grammar,
not by the runtime. Baking the code into the image is worth doing together with
narrowing the mount to the four stores, because `.:/app` shadows it; the
snapshots have left `module_monitoring/`, so that prerequisite is met.

Compose services are named for their runtime role — `pipeline`, `dashboard`,
`asset-<ticker>`, `devops` (`skill_asset_containers.md` § The topology) — never
for a ticker, a tool or an author; container, network and volume names stay
compose-derived, never fixed, and the host port is measured, never fixed
(`skill_asset_containers.md` § The topology), so that checkouts of LIORA can
sit side by side on one host
(`../module_monitoring/skills/skill_devops_panel.md` § The guard);
no code depends on a container name — code knows `ASSET`, and every address is
built once, in `module_monitoring/config.py`.

## The volume is the home, the store is the copy

Locally the working tree is the only home: the `store_*` roots and the two
snapshots, reached through `.:/app`; nothing copies. Read forward the home is
the store volume, the task host's durable disk at `/app`, as `.:/app` is today,
so every descriptor resolves unchanged; object storage is the copy after the
run, written by no stage: after the last stage has exited, one orchestration
state, PublishStores, copies whole files to the four prefixes of § The asset
folder is a prefix, read forward — the raw day files written once, as the raw
tree already is (`../module_data/skills/skill_candle_canonicalisation.md` § 3);
the asset folder, database included, under the execution name as its version;
the run record; the three snapshots. A stage never reads the copy: it knows a
path, not a bucket, and `AGENTS.md` § Rejected vocabulary refuses the constant
that would teach it one; the readers on the host read the home; only the
strategy host reads the copy. PublishStores is absent here — described: its row
of § The mapping table has no local counterpart, and the forms refused are §
Rejected forms.

## The resident container is a local mechanism

`asset-<ticker>` exists to answer `/status`; compute borrows it so the panel
measures the container doing the work (`skill_asset_containers.md` § The
topology). Every stage is a one-off process, `python -m <module>.<stage>
--tickers <TICKER>`, or the equivalent `docker compose run --rm -T pipeline …`;
no stage module reads `ASSET` — it belongs to the container, to `serve.py`
choosing its role and to the recorder; no stage holds state between invocations,
binds a port or assumes a resident peer. The residency assumption for compute
lives in one macro line, `dockerfanout` in the Makefile, and nowhere else, and
`record.py` already tolerates a container that is gone. Read forward that one
line is a task run with an `ASSET=<TICKER>` override on the one task definition,
and no stage notices. Two stages are the reduce over the basket rather than
asset-scoped stages: `module_data.status` and `module_ml.status` each write one
whole object for the basket, have exactly one writer and run only in the one-off
`pipeline`, never fanned out (`../module_data/README_module_data.md` § Stages,
`../module_ml/README_module_ml.md` § Stages); the asset README the second also
writes is an asset artifact of an asset-scoped part of that stage, the snapshot
a fold over completed asset artifacts. The download stays basket-wide and
sequential for a venue reason, not a namespace one (`skill_asset_containers.md`
§ The topology). If the basket ever outgrows a handful, the direction is a
per-asset status object and a reader-side fold, not a lock.

## The Makefile is the developer interface

The Makefile is the local developer interface and never a scheduler. A stage is
`<module>-<stage>` with a `docker-` twin (`AGENTS.md` § Canonical vocabulary,
the grammar table); the order is the visible list in `all:`, `features-all:` and
`ml-all:` (`../README.md` § Quickstart); no recipe branches on state, retries, sleeps or
waits for a condition — the `JOBS` measurement decides how wide a stage runs,
never whether. `JOBS`, `RECORD` and `RUN_ID` are the local spellings of three
parameters that orchestration owns — width, stage instrumentation, execution
identity — and no stage reads or derives any of them (`skill_determinism.md` for
width). The basket crosses in as data — `--tickers` on every stage command,
named by the launcher's `TICKERS` — never as a branch. One stage vocabulary
holds in every layer — the Makefile,
`stage_of()` in the recorder, the run record, the page, these documents — with
one seam named: the target `data-download` runs both download stages, so the
record spells them `data-download-binance` and `data-download-bybit`.

Read forward, the Makefile is a state machine whose states are the stages. The
test of a stage's width is whether it has a one-line state name; every stage of
the pipeline passes today (`monitoring-dx-update` redraws a tracked file on the
host and never runs elsewhere, so it is a tool, not a state):

| stage | the state it would be |
|---|---|
| `data-download` | DownloadMarketData |
| `data-ingest` | BuildCanonicalData |
| `features-bars` | AggregateBars |
| `features-catalogue` | GenerateFeatures |
| `ml-labels` | GenerateLabels |
| `ml-hpo` | SearchHyperparameters |
| `ml-train` | TrainModel |
| `ml-strategy` | EvaluateStrategy |
| `data-status`, `ml-status` | PublishStatus |
| `ml-feature-set-search` | SearchFeatureSet — started by a hand, outside the daily order; the same task run, detached locally in a tmux session |
| `ml-feature-set-promote` | PromoteFeatureSet — started by a hand for one asset, outside the daily order; the states of `ml-all` follow it |

A stage that needed two names, or a name with "and" in it, would be too wide.
Read forward the visible list is that machine's definition: `all:`, `features-all:`
and `ml-all:` its state order, `xargs -P $(JOBS)` its Map over `TICKERS` — 1 wide for
BuildCanonicalData, `JOBS` wide above it, measured, never a literal
(`skill_determinism.md`, *Width is measured at invocation*) — `RUN_ID` its
execution name, and PublishStores, no stage and so no row, the copy after the
last stage has exited.

## The retrain runtime is a ladder

Three phases, none built here, each named for what it changes; a phase skipped
is a redesign — the idiom without the lift has no volume for the database file,
and the image carrying the code without the idiom bakes a Makefile into an
image.

- **The lift.** The task host with its store volume, this tree checked out onto
  the volume, `docker compose` as it is, a hand typing `make docker-all` as
  here. Nothing in the compose file changes: the checkout sits on the volume, so
  `.:/app` already is the volume, and everything the Makefile assumes still
  holds.
- **The idiom.** One task definition registered with the service that runs the
  tasks; `.:/app` → `<volume>:/app` in the anchor's line and the one `devops`
  respells; the one line of `dockerfanout` → a task run per stage per asset,
  the one edit § The mapping table names; the stages as states, the Map, the
  execution name; the schedule starting the machine instead of a hand;
  PublishStores after the last state; no condition state, because no predicate
  exists (§ The rebuild condition stays separable). The Makefile stays the
  developer interface and stops being what runs the day.
- **The image carries the code.** `Dockerfile` copies the tree, the registry
  holds the image, and the mount narrows to the `store_*` roots (§ Docker is
  compute, not storage). A run without a host is a sentence in the
  `run --rm -T pipeline` row of § The mapping table, never a phase.

## The rebuild condition stays separable

No event system exists and none is added. The shape the code keeps open is *new
data exists → evaluate a condition → does this asset need its artifacts rebuilt?
→ yes: run the asset's ML chain*. The condition is a per-asset, read-only
predicate over storage that returns an answer and launches nothing; detection
and compute are never one function. Today the only condition that changes what
work is done is object presence in the raw store — the downloaders' day skip;
every stage below rebuilds unconditionally by contract
(`../module_data/skills/skill_candle_canonicalisation.md` § 14,
`../module_ml/skills/methodology_ml.md` § 11), and the rerun table of
`methodology_ml.md` § 11 *is* the condition, read by a human.
`is_artifact_set_complete()` in `module_ml/config.py` is its completeness half,
never its freshness half. When a freshness predicate is written it is a question
in the owning module, beside the descriptors of what it compares —
`has_new_market_data(ticker)` and `requires_canonical_rebuild(ticker)` in
`module_data`, `requires_feature_rebuild(ticker)` and
`requires_model_rebuild(ticker)` in `module_ml` — never `should_run()`,
`check_update()` or `trigger()`, and never lifted out of the downloader's loop
before it is needed.

## Correlatable artifacts, without a version scheme

Every output ties to its asset by folder and `<TICKER>_` prefix, to its stage by
file name, to its configuration by the git commit
(`../module_ml/skills/methodology_ml.md` § 10) and, when a run is recorded, to
its execution by `run_id` in the run record (`glossary.md` § Run record). No run
id, `model_version`, hash or provenance envelope enters an artifact — two
settled refusals, `methodology_ml.md` § 10 and `skill_asset_containers.md` § The
endpoint contract. What keeps `artifacts/<ticker>/<version>/` a rename rather
than a redesign is one descriptor per artifact, built in one `config.py` and
consumed by descriptor everywhere, the recorder included. The `<version>` is the
execution name, `run_id`, and the active version — the one a reader reads — is
chosen where the reader is, never marked inside a file. A per-asset view of a
run is a subdivision inside one record — `run_id`, then the `tickers` field, the
service name, the manifest row and the log-name half — never one record per
asset. The run record's root-relative paths are the local form of object keys,
and its directory listing the local form of listing a prefix.

## The dependency picture

```
Binance / Bybit ──► module_data ──► RAW STORAGE ──► CANONICAL ASSET STORAGE ──┬──► module_ml ──► ASSET ARTIFACT STORAGE ──┬──► module_monitoring ──► dashboard
                                                                              │                                          └──► strategy execution   (absent here)
                                                                              └──► QuantConnect Lean backtest              (absent here)

                    orchestration — the Makefile locally — sits above every stage and inside none
```

The domain drawing is the lede of `../README.md`; this one adds only the storage
boxes and the two absent consumers.

## One day, told forward

One UTC day, in order. Each entry says what happens locally, what happens
elsewhere, and — `Never:` — the refusal that stands, cited where it stands.

1. **The day closes.** The window ends at the most recent UTC midnight; a day is
   written only when `is_full_utc_day()` holds. Locally: nothing runs by itself.
   Elsewhere: the same; the schedule is the only clock. Never: a watcher, an
   event bus (`glossary.md` § Pre-AWS direction).

2. **The schedule.** Once per `download_cadence_minutes`, a fixed offset after
   midnight UTC so that the day asked for is already full — `is_full_utc_day()`
   in `module_data/lean.py`. Locally: `make docker-all-record`, typed by hand,
   which expands `RUN_ID`. Elsewhere: the schedule starts one execution, named
   as `run_id`. Never: a scheduler (`glossary.md` § Pre-AWS direction).

3. **DownloadMarketData.** Two task runs of the one task definition, one per
   venue command, in one state; a day already on disk is skipped. Locally:
   `docker-data-download`. Elsewhere: the same, on the store volume. Never: a
   download fanned out per asset (`skill_asset_containers.md` § The topology).

4. **BuildCanonicalData.** `module_data.ingest --tickers <TICKER>`. Locally:
   `dockerfanout`, width 1. Elsewhere: a Map over `TICKERS`, width 1, each a
   task run with `ASSET=<TICKER>`. Never: a database process (§ The chief
   antipattern).

5. **PublishStatus, for data.** `module_data.status` writes `data_status.json`
   once for the basket. Locally: `docker-data-status` in `pipeline`. Elsewhere:
   the same task run, no `ASSET`. Never: a resident as a requirement of a stage
   (`glossary.md` § Pre-AWS direction).

6. **The rebuild condition — absent.** Nothing is asked: every state below runs
   unconditionally, the rerun table of `methodology_ml.md` § 11 read by a human.
   Locally: the same. Elsewhere: a choice state would ask the predicates of §
   The rebuild condition stays separable — absent here — described. Never: a
   function that both detects new data and trains (`glossary.md` § Pre-AWS
   direction).

7. **The research layer.** AggregateBars to EvaluateStrategy, the per-asset
   states each a Map over `TICKERS` as wide as `JOBS`; between the catalogue and
   the labels, **PublishStatus for features** — `module_features.status` writes
   `features_status.json` once for the basket. Locally: `dockerfanout` at
   `$(JOBS)`, the status in `pipeline`. Elsewhere: a task run per state per asset
   with `ASSET=<TICKER>`, the status a task run with none. Never: `ASSET` read by
   a stage module (`glossary.md` § Asset containers).

8. **PublishStatus for ML, then PublishStores.** `module_ml.status` writes
   `ml_status.json` and each `<TICKER>_README.md`; the run is over. Locally:
   `docker-ml-status`. Elsewhere: the same task run, then PublishStores copies
   the closed files whole to the four prefixes — absent here — described. Never:
   `s3://` in a path constant (`AGENTS.md` § Rejected vocabulary).

9. **Logs and metrics.** The recorder's files. Locally: with `RECORD`,
   `logs/<stage>_<docker_service>.log` and the 1 s samples in
   `store_run_records/<run_id>/`. Elsewhere: its row of § The mapping table —
   absent here — described. Never: a container number as a stage cost
   (`glossary.md` § Run record).

10. **The page, behind the tunnel.** Locally: `make on`, the address it prints, the
    tunnel (`../README.md` § Quickstart). Elsewhere: `dashboard`, `devops` and
    `asset-<ticker>` kept running on the task host, a port-forward where the
    tunnel stands. Never: a published port (`glossary.md` § Asset containers).

11. **The strategy host — absent.** Locally: the Lean-exact raw tree, no
    runtime. Elsewhere: a separate Linux instance running Lean reads the raw
    prefix and `artifacts/<ticker>/<version>/` from the copy, its credentials
    from a secrets store; `module_trading/` absent here — described. Never: a
    module named for a cloud resource (`AGENTS.md` § Rejected vocabulary).

12. **The day in the home and the copy, in no container.** Locally: the working
    tree and the page, every container exited
    (`../module_data/skills/skill_candle_canonicalisation.md` § 15). Elsewhere:
    the store volume, object storage under its four prefixes, the page. Never: a
    container as the home of an asset's state (`glossary.md` § Pre-AWS
    direction).

## The mapping table

The left column is what this repository has; the third, *the same responsibility
elsewhere*, the shape the same responsibility would take; the fourth, *the
move*, what the move is — a rename, one edit, or absent here — described. No
path in the elsewhere column is a proposal for a local directory. Where a cloud
proper noun is spoken is the closed list of `AGENTS.md` § Pre-AWS architectural
direction; a row whose move is absent here — described has no local counterpart,
and its primitive, if it has one, is drawn absent
(`../module_monitoring/skills/skill_developer_experience_drawing.md` § Two views
of one tree).

| this repository has | responsibility | the same responsibility elsewhere | the move |
|---|---|---|---|
| the one image, `mlops-portfolio-1m-pipeline` | COMPUTE — the runtime every stage runs in | a container image in a registry (Amazon ECR); it carries the code only once the ladder reaches the phase named for it, *the image carries the code* (§ The retrain runtime is a ladder), and until then the volume carries it | a rename |
| `docker compose run --rm -T pipeline python -m <module>.<stage>` | COMPUTE — one stage, one one-off process | one run of the one task definition, `pipeline`, with the command overridden to the stage (`RunTask`, Amazon ECS on Amazon EC2) on one Linux container instance shared by every asset's runs, the volume of the `.:/app` row mounted; the data-ingest task is that definition run with a `module_data` command, the ml-research task with a `module_features` or a `module_ml` one, never two definitions; AWS Fargate is the same task without the host, and so without the volume — a sentence here, never a phase | a rename |
| a per-asset stage, `--tickers <TICKER>`, inside `asset-<ticker>` — the one line `dockerfanout` | COMPUTE — one stage for one asset | the same run with `ASSET=<TICKER>` overridden, one per asset — BuildCanonicalData on the data-ingest task, AggregateBars to EvaluateStrategy on the ml-research task, whether the command is a `module_features` or a `module_ml` one; the resident it borrows locally is not borrowed there, and the exec into it becomes a task run — the one line where a mechanism changes and not a name | one edit |
| one compose service per ticker under one anchor, and the residents — `dashboard`, `devops`, `asset-<ticker>` — beside it | INFRASTRUCTURE — the parameter made visible | one task definition parameterised by `ASSET`, never a new unit per asset; `dashboard`, `devops` and one `asset-<ticker>` per ticker kept running on the same instance as services of the container runtime, one per service, as they are kept running here (Amazon ECS) | a rename |
| the Makefile's `all:`, `features-all:` and `ml-all:`, `xargs -P $(JOBS)`, `RUN_ID` | ORCHESTRATION — the explicit stage order, the width, the execution identity | a state machine whose states are the stages of § The Makefile is the developer interface, every fanned-out state a Map over `TICKERS` as wide as `JOBS`, and `run_id` as the execution name (AWS Step Functions) | a rename |
| `.:/app` — the one bind mount of every service, the code and the `store_*` roots at one path | STORAGE — the home of state | a durable block volume mounted at `/app` by every task and service of the instance — `.:/app` read as `<volume>:/app` in the anchor's line and the one `devops` respells, every `store_*` root and all three snapshots at the path its `config.py` builds today (Amazon EBS); never a network filesystem, never a task's own disk (§ The volume is the home, the store is the copy) | a rename |
| `store_raw_1m/cryptofuture/<venue>/minute/<symbol>/YYYYMMDD_trade.zip` | STORAGE — raw, immutable, one object per UTC day | the same tree on the volume, and its copy under `raw/<venue>/<symbol>/<day>` in object storage after the run, each day object written once (Amazon S3) | a rename |
| `store_assets_artifacts/<TICKER>/` | STORAGE — one prefix per asset | the same folder on the volume, and its copy under `artifacts/<ticker>/<version>/` in object storage after the run, the version the execution name, each key the descriptor's path relative to `STORE_ASSETS_ARTIFACTS_DIR` (Amazon S3) — nothing to edit in either descriptor | a rename |
| `<TICKER>_research_ohlcv.duckdb` | STORAGE — the canonical market object, one writer at a time | the same embedded file on the volume, opened by the same process under the same whole-file lock, copied whole to the asset's version prefix after the run — never a database process, never a shared network filesystem; a managed database (Amazon RDS) only past the threshold of § The databases | a rename |
| the parquets and JSONs of the asset folder | STORAGE — research artifacts | artifact objects under the same version prefix | a rename |
| a hand typing `make docker-all`, `download_cadence_minutes` of `data_status.json` being the only cadence the tree names; the downloaders' day-presence skip and the rerun table of `../module_ml/skills/methodology_ml.md` § 11, read by a human | ORCHESTRATION — the cadence and the rebuild condition, not yet code | a schedule that starts the machine once per `download_cadence_minutes`, a fixed offset after midnight UTC so that the day the download asks for is already full — `is_full_utc_day()` in `module_data/lean.py` (Amazon EventBridge Scheduler), and a condition state between BuildCanonicalData and AggregateBars that reads the volume and launches nothing (a Step Functions choice) — both absent, one primitive of the deployment view | absent here — described |
| `store_status/data_status.json`, `store_status/features_status.json`, `store_status/ml_status.json`, `store_run_records/<run_id>/` | STORAGE — status and run objects | the run record under `runs/<run_id>/` and the three snapshots under `status/`, copied from the store after the run, the page reading them from the status store as here — `store_status/` is already that prefix, read forward; the move off `module_monitoring/` turned the five points § What stays as it is, and why names, and answered the question `skill_status_prefix.md` asked (`AGENTS.md` § Skills absent here, described) | a rename |
| `logs/<stage>_<docker_service>.log` and the 1 s cgroup samples of a run | MONITORING — logs and resource metrics | log streams keyed by stage and container, and metrics (Amazon CloudWatch) — the recorder's files, written only when `RECORD` is set, are their described counterpart | absent here — described |
| the page files of `module_monitoring/`; the three snapshots are STORAGE (the row above) and reach the page through the `/store_status/<name>` route | MONITORING — the static dashboard | served by the reader service of the row below from the volume; static objects behind a content-delivery front (Amazon S3 with Amazon CloudFront) only when a reader outside the host appears — the front absent | absent here — described |
| the `/containers`, `/runs` and `/devops/*` routes; the tunnel, `ssh -L`, to the page | MONITORING — a small reader process | the `dashboard` service kept running on the instance, reaching the asset services and the panel by name as here, reached from outside by a port-forward where the tunnel stands today and by no public port | a rename |
| the Lean-exact raw tree; no Lean runtime | STRATEGY EXECUTION — absent | a separate container running QuantConnect Lean on its own Linux instance (Amazon EC2) — the strategy host: a lean-backtest task, or a container that stays running and trades live, reading the raw and asset prefixes from the copy and never the volume, its brokerage credentials read from the secret below when it starts | absent here — described |
| none — the venue downloads use public endpoints, and neither the dashboard nor the panel asks for a credential | STRATEGY EXECUTION — absent; the brokerage credentials a live strategy reads at start | a secret in a secrets store (AWS Secrets Manager), read once by the container running Lean when it starts | absent here — described |
| `sub_module_devops` — the one socket; `sub_module_dx` | INFRASTRUCTURE — the engine's views, the repository's view | the same socket on the instance, because the service that runs the tasks starts them through the host's own daemon; the provider's console and a repository view, not project code — the console a sentence inside this row, no primitive of its own | a rename |
| none — the copy after the run: every stage writes the working tree through `.:/app` and exits, and nothing copies | ORCHESTRATION — PublishStores, the copy after the run | a state after the last stage of a run has exited that copies each `store_*` root whole — `store_status/` among them — to their prefixes — `raw/<venue>/<symbol>/<day>`, `artifacts/<ticker>/<version>/`, `runs/<run_id>/`, `status/` — in object storage (Amazon S3), once per run, never a stage's own write, never mid-run (§ The volume is the home, the store is the copy) | absent here — described |

## Rejected forms

| form | why not |
|---|---|
| a shared network filesystem as the volume (Amazon EFS) | the database is one file under a whole-file lock (`skill_asset_containers.md` § The server), and a block device is where the lock holds; a filesystem shared between hosts would make the volume a second home instead of the home |
| a managed database now (Amazon RDS) | one writer at a time and no query across assets — § The databases names the threshold, and nothing has crossed it |
| object storage as the first home | the reading in which the asset folder was a future storage prefix and an asset's files existed on a task's disk for one run and nothing after it — a pull and a push around every stage, an adapter, the second backend nothing has earned (§ The chief antipattern); the prefix is the copy, never the home |
| a batch service (AWS Batch) | a queue and a job definition for stages that are already an ordered list; the state machine is the order, the service that runs the tasks is the container |
| a run without a host first (AWS Fargate) | no host, no volume, no file — a sentence in the `run --rm -T pipeline` row of § The mapping table, never a phase (§ The retrain runtime is a ladder) |
| a cluster for one host (Amazon EKS) | a control plane, nodes and manifests kept running for four services on one host — the *no Kubernetes* of § Non-goals, and the one rule behind them; the question *how many hosts, how many services?* of § Infrastructure seats answers one host |
| a task on a host the provider holds (Amazon ECS Managed Instances) | no bind mount to a path on a host this project holds, and no host daemon socket — `.:/app` on every service and `/var/run/docker.sock` in `devops` (`docker-compose.yml`; `skill_asset_containers.md`, *The socket rule, and its one scope*) are both a path on the host |
| a managed web service for the dashboard (AWS App Runner) | the page is published on loopback alone and reached through the tunnel (`../README.md` § Quickstart); a front is refused until a reader outside the host appears — the static dashboard row of § The mapping table |
| a stage as a function run from the image on an event (AWS Lambda) | a stage reads a store and writes a store on the disk the next stage reads (`AGENTS.md` § Pre-AWS architectural direction, *Compute owns no state*, *Storage is separate from compute*); the search and the training are not short functions, and no event exists to run one on (§ The rebuild condition stays separable) |

A host per asset and a database process are refused where named: `AGENTS.md`
§ Pre-AWS architectural direction, and § The chief antipattern.

## The chief antipattern

"How does AWS look? Copy it locally": a database server because the cloud would
have one, a queue because the cloud would have events, a retry layer because a
remote container run might fail, a `StorageManager` or a `CloudCompatibleStorageInterface` while
there is one filesystem. The order is the reverse: what responsibilities does
the system have → build the simplest local implementation of each → check that
the boundary between them has a natural cloud equivalent. A second storage
backend earns an abstraction; nothing earns it earlier. *Research logic over
tooling* (`AGENTS.md` § Values) is the general rule; this is its special case.

## KISS and YAGNI decide, and the final rule

When production realism and academic simplicity conflict, simplicity wins,
provided no boundary results that would hinder the migration. GOOD: a DuckDB
file per asset — trivial locally, the same file on a durable volume later,
copied whole to its version. BAD: a local PostgreSQL "because the cloud should
have a database".

## What stays as it is, and why

The tree as it stands, in four columns; a row disappears with the line it names.

| current | problem | Pre-AWS direction | change now? |
|---|---|---|---|
| `module_features/bars.py` opens `module_data`'s database read-write; every open downstream is read-only | one stored object, two writing modules, across the storage → feature-compute line | one durable writer at a time, sequenced by `features-all` and enforced by the whole-file lock; the aggregation tables are a pure, idempotent function of `ohlcv_1m_canonical`; a second database is forbidden by `../module_data/skills/skill_candle_canonicalisation.md` § 13 | no — described |
| every status stage takes `--tickers` and folds the assets the launcher named — the whole basket, from `pipeline` | one object per basket, safe only because it has one writer | a basket-wide object is produced only by the one-off vehicle, never fanned out; a per-asset object and a reader-side fold if the basket grows | no — described |
| the three snapshots are written into `store_status/` and tracked | status objects live in their own store beside the other three, never under a `module_*` | moved: STORAGE produced by DATA, FEATURE and ML compute, tracked as a property of the demonstration so a fresh clone opens on real numbers; the move turned the five points — the path constants (`DATA_STATUS_JSON_PATH`, `FEATURES_STATUS_JSON_PATH`, `ML_STATUS_JSON_PATH` under `STORE_STATUS_DIR`), the directory `serve.py` serves (its own package), the literal fetches (under `/store_status/`) — and met the prerequisite of narrowing the mount; the third snapshot arrived by the same route; `skill_status_prefix.md` (`AGENTS.md` § Skills absent here, described) is thereby answered | yes — done |
| `Dockerfile` copies no code; code and state both arrive through `.:/app` | the image is a dependency layer, not a compute artifact | said, not built: one mount is the local simplification; the phase *the image carries the code* of § The retrain runtime is a ladder is the image carrying the code and the mount carrying the state alone — `skill_image_contents.md` (`AGENTS.md` § Skills absent here, described) | no — described |
| `record.py` holds the map of every stage to the artifacts it leaves | pipeline-shape knowledge in the representation module | measurement may hold stage → artifact, never the stage order or a dependency between stages; a later condition reads this table rather than starting a second | no — described |
| a recorded run fails if any stage failed *or* the dashboard probe failed; finalising needs `docker` and `git` on the host | two facts in one number; the run cannot be finalised elsewhere | a local lifecycle verdict — the chain ran and the page represents it; an execution record finalised off the host judges on the exit codes alone, which are already in the record — a clause of `skill_stage_state_machine.md` (`AGENTS.md` § Skills absent here, described) | no — described |
| `module_monitoring/` is served wholesale, five routes and a proxy beside static files | one root is page and package; the status store is reached through one route | the page files are static objects of the package, the snapshots static objects of another store; the routes are a reader process | no — described |
| no callable "does this asset need a rebuild?" exists | the condition has no home; nothing is wrongly fused | keep compute unconditional; a future predicate is the `is_` / `has_` / `requires_` question above, never a lift of the downloader's loop | no — described |
| `docker-btc-all`, `docker-btc-lifecycle` | a ticker in a target name | detached from every document and page; retire when the basket grows, as their sunset notes say | no — described |
| compose project, container and network names derive from the directory | none | checkouts of LIORA can sit side by side on one host with the same service names; a fixed name would merge them, and the host port is measured for the same reason | no — described |
| the image is named `mlops-portfolio-1m-pipeline`, a name older than LIORA | none for the mapping: one runtime package, no ticker | kept; the name is one runtime package with no ticker, which is all the mapping needs; two checkouts that build one tag share whichever built last, so a rename is worth doing only under a tag no sibling builds | no — described |
| `centered_rsi14` is spelled the American way | the one identifier that breaks the British spelling of the prose | a stored column, an artifact key and a feature name — a contract with files on disk that moves only with every writer and reader in one commit | no — described |
| the drawing's `color` key is spelled the CSS way beside prose that says colour | one key against the British prose around it | the word of the CSS it feeds; fifteen keys of `visualisation_config.json`, the generator, the template and a redraw of the derived page would move together for one letter | no — described |
| `hpo` names the stage and the file; `hyperparameter_search_result` names the key | one term in two forms | a domain abbreviation `AGENTS.md` § Canonical vocabulary admits, spelled out where a key has no file name beside it — as UTC and OHLCV are | no — described |
| `module_ml.status` writes a basket snapshot and per-asset READMEs in one stage | two namespaces in one stage | each named: the README is an asset artifact of an asset-scoped part of that stage, the snapshot a fold over completed asset artifacts | no — described |
