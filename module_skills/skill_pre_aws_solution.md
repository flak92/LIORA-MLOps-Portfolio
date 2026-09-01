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
a path. Every rule this document leans on that is already written elsewhere is
cited by path and section, never restated; what is new here is the
classification, the non-goals and their rule, the rebuild condition, the
mapping table and the review of the tree.

## Project status

LIORA is an academic, portfolio and research demonstration of an MLOps and
quant-research architecture. It is not a production trading system, not an AWS
deployment and not a production MLOps platform. The runtime is local — a venv,
or one `python:3.12-slim` image under docker compose, driven by a Makefile — and
the goal is a correct dataflow with visible responsibilities. The stance is
`AGENTS.md` § Values, *Academic, not production*; the register it is written in
is `../module_ml/skills/methodology_ml.md` § 12.

## The minimum demonstration

The proof of the architecture is the whole chain running end to end on a very
small representative basket: `BTC` today, optionally one to three more. Scale is
`ASSET=<TICKER>`, never hundreds of assets in a demonstration repository; a
basket grows by one line in `TICKERS` and one block under the compose anchor
(`README.md` § The basket says how; this section says why it is enough). A
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
- no infrastructure code: if an `infra/` ever exists it is shaped by
  responsibility — compute, storage, orchestration, monitoring — and its
  resources are named `<project>-<environment>-<resource-role>`; no `dev` or
  `prod` enters this repository's names before it does.

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
| CANONICAL | the one research series built from the evidence, and its aggregations | `module_data/ingest.py` — `CANONICAL_INSERT`; `module_data/lean.py`, the raw format it is read from; `module_ml/bars.py`, the 15m/1h/4h tables of the same series |
| STORAGE | where state lives, and the descriptors that name it | the `store_*` roots; every path descriptor of a `config.py` |
| FEATURE | X, a pure function of the canonical series | `module_ml/features.py`, `module_ml/indicators.py` |
| LABEL | Y, resolved on the canonical path | `module_ml/labels.py` |
| MODEL | the search, the fit, the folds, the shared IO | `module_ml/hpo.py`, `module_ml/train.py`, `module_ml/model.py`, `module_ml/validation.py`, `module_ml/dataset.py` |
| STRATEGY | the research evaluation of the predictions | `module_ml/strategy.py` |
| ORCHESTRATION | ordering and launching the stages — not `orchestration_seconds` of `glossary.md` § Run record, the wall time between two stages | the Makefile |
| MONITORING | measuring the runtime and presenting what the modules measured | `module_data/status.py`, `module_ml/status.py`, `module_monitoring/serve.py`, `module_monitoring/record.py`, the page scripts |
| STRATEGY EXECUTION | taking research artifacts and market data into a running strategy | absent — a future `module_trading/`, its own container |
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
- `module_ml` — canonical → bars → features → labels → search → model →
  predictions → strategy evaluation; it receives a finished canonical object and
  asks nothing about a venue (`../module_ml/README_module_ml.md` § Where the
  responsibility stops). **That line is the future data-storage → ML-compute
  boundary.** Its one write across it is `bars.py`, named in § What stays as it
  is below.
- `module_monitoring` — existing state → representation, and nothing of the
  research process (`../module_monitoring/README_module_monitoring.md` § Where
  the responsibility stops). A status stage is MONITORING work owned by the
  module whose state it measures: `AGENTS.md` § Architecture shape.
- QuantConnect Lean — a format here, not a runtime. `module_data/lean.py` is the
  one external-format boundary, and the raw tree is written Lean-exact so a Lean
  backtest could read it directly
  (`../module_data/skills/skill_candle_canonicalisation.md` § 13); that is the
  whole of Lean's presence. No Lean runtime, container or dependency exists in
  this repository. Strategy execution, if it ever exists, is `module_trading/` —
  its own container beside `module_ml`, never inside it; the register keeps one
  Lean row, `glossary.md` § Market object.

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

## The asset folder is a future storage prefix

`store_assets_artifacts/<TICKER>/` is, read forward, one prefix per asset. Every
per-asset file carries the `<TICKER>_` prefix and a time series carries its grid
in timeframe slots — `BTC_features_ss-15-hh-dd-MM.parquet`
(`skill_sorting_files_naming_standard.md` § The timeframe slot standard); the
file-by-file manifest is `glossary.md` § Artifacts and is not copied here.
Canonical storage and artifact storage share the prefix today, ownership carried
by which module's `config.py` builds the name; a future split into a canonical
prefix and an artifact prefix is one edit to `artifact_dir()` and one to
`research_ohlcv_duckdb()`, not a folder move. A new local store is
`store_<object>/`, never a bare `data/`, `artifacts/` or `canonical/`
(`AGENTS.md` § Rejected vocabulary). The raw tree is the model case: written
once, one UTC day per object, deleted to correct, its presence the condition
that skips a download (`../module_data/README_module_data.md` § Stages;
`../module_data/skills/skill_candle_canonicalisation.md` § 3) — venue-major and
lower case because Lean demands it (`AGENTS.md` § Architecture shape). Read
forward, the stores correspond to `raw/<venue>/<symbol>/<day>`,
`canonical/<ticker>/`, `artifacts/<ticker>/`, `runs/<run_id>/` and `status/` —
a semantic correspondence, not a layout to adopt locally.

## Docker is compute, not storage

`../module_data/skills/skill_candle_canonicalisation.md` § 15 and
`../module_data/README_module_data.md` § Docker and the database state it for
the database; it holds for every store. A container is never the owner of an
asset's state: it reads input, computes, writes output and may disappear; state
stays in the DuckDB file, the parquets, the JSONs and the raw ZIPs, under paths a
`config.py` names. The image, `mlops-portfolio-1m-pipeline`, is one runtime
package for every role — the command and `ASSET` decide the role, and no ticker
is in its name. It is a dependency layer (`Dockerfile`), and the one `.:/app`
mount carries three things: the code (a future image), the durable state under
the `store_*` roots and the two tracked snapshots (future prefixes), and nothing
scratch — kept apart by the `store_*` grammar, not by the runtime. Scratch is the
operating system's (`tempfile` in `module_ml/dataset.py` and
`module_data/ingest.py`), named by no `config.py` and surviving no process. Keep
one mount: a read-only code mount beside per-store mounts is permission
isolation, a non-goal; baking the code into the image is only worth doing
together with narrowing the mount, because `.:/app` shadows it — and narrowing
needs the snapshots out of `module_monitoring/` first.

Compose services are named for their runtime role — `pipeline`, `dashboard`,
`asset-<ticker>`, `devops` — never for a ticker, a tool or an author. Container,
network and volume names stay compose-derived on purpose: checkouts of LIORA can
sit side by side on one host with the same service names
(`../module_monitoring/skills/skill_devops_panel.md` § The guard), and a fixed
project name or a named network would merge them into one project on one
network. No code depends on a
container name; code knows `ASSET`, and every address is built once, in
`module_monitoring/config.py`. The asset's database is the GOOD example of the
whole stance — one embedded file, one whole-file lock, one writer at a time
(`skill_asset_containers.md` § The server) — later one versioned object pulled
into a container's own disk and put back whole; never a database process, never
a shared mount, never a local PostgreSQL.

## The resident container is a local mechanism

`asset-<ticker>` exists to answer `/status`; compute borrows it so the panel
measures the container doing the work (`skill_asset_containers.md` § The
topology). Every stage is a one-off process, `python -m <module>.<stage>
--tickers <TICKER>`, or the equivalent `docker compose run --rm -T pipeline …`;
no stage module reads `ASSET` — it belongs to the container, to `serve.py`
choosing its role and to the recorder; no stage holds state between invocations,
binds a port or assumes a resident peer. The residency assumption for compute
lives in one macro line, `dockerfanout` in the Makefile, and nowhere else, and
`record.py` already tolerates a container that is gone. Two stages are the reduce
over the basket rather than asset-scoped stages: `module_data.status` and
`module_ml.status` each write one whole object for the basket, have exactly one
writer and run only in the one-off `pipeline`, never fanned out
(`../module_data/README_module_data.md` § Stages,
`../module_ml/README_module_ml.md` § Stages); the asset README the second also
writes is an asset artifact of an asset-scoped part of that stage, the snapshot a fold over
completed asset artifacts. The download stays basket-wide and sequential for a
venue reason, not a namespace one (`skill_asset_containers.md` § The topology).
If the basket ever outgrows a handful, the direction is a per-asset status object
and a reader-side fold, not a lock.

## The Makefile is the developer interface

The Makefile is the local developer interface and never a scheduler. A stage is
`<module>-<stage>` with a `docker-` twin (`AGENTS.md` § Canonical vocabulary,
the grammar table); the order is the visible list in `all:` and `ml-all:`
(`README.md` § Quickstart); no recipe branches on state, retries, sleeps or waits
for a condition — the `JOBS` measurement decides how wide a stage runs, never
whether. `JOBS`, `RECORD` and `RUN_ID` are the local spellings of three
parameters that orchestration owns — width, stage instrumentation, execution
identity — and no stage reads or derives any of them (`skill_determinism.md` for
width). The basket crosses in as data read once, by importing `TICKERS`, never
as a branch. One stage vocabulary holds in every layer — the Makefile,
`stage_of()` in the recorder, the run record, the page, these documents — with
one seam named: the target `data-download` runs both download stages, so the
record spells them `data-download-binance` and `data-download-bybit`.

Read forward, the Makefile is a state machine whose states are the stages. The
test of a stage's width is whether it has a one-line state name; every stage
passes today:

| stage | the state it would be |
|---|---|
| `data-download` | DownloadMarketData |
| `data-ingest` | BuildCanonicalData |
| `ml-bars` | AggregateBars |
| `ml-features` | GenerateFeatures |
| `ml-labels` | GenerateLabels |
| `ml-hpo` | SearchHyperparameters |
| `ml-train` | TrainModel |
| `ml-strategy` | EvaluateStrategy |
| `data-status`, `ml-status` | PublishStatus |

A stage that needed two names, or a name with "and" in it, would be too wide.

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
id, `model_version`, hash or provenance envelope enters an artifact — two settled
refusals, `methodology_ml.md` § 10 and `skill_asset_containers.md` § The
endpoint contract. What keeps a future `<prefix>/<ticker>/<version>/` a rename
rather than a redesign is one descriptor per artifact, built in one `config.py`
and consumed by descriptor everywhere, the recorder included. A per-asset view of
a run is a subdivision inside one record — `run_id`, then the `tickers` field,
the service name, the manifest row and the log-name half — never one record per
asset. The run record's root-relative paths are the local form of object keys,
and its directory listing the local form of listing a prefix.

## The dependency picture

```
Binance / Bybit ──► module_data ──► RAW STORAGE ──► CANONICAL ASSET STORAGE ──┬──► module_ml ──► ASSET ARTIFACT STORAGE ──┬──► module_monitoring ──► dashboard
                                                                              │                                          └──► strategy execution   (absent here)
                                                                              └──► QuantConnect Lean backtest              (absent here)

                    orchestration — the Makefile locally — sits above every stage and inside none
```

The domain drawing is the lede of `README.md`; this one adds only the storage
boxes and the two absent consumers.

## The mapping table

The left column is what this repository has; the right column is the shape the
same responsibility would take elsewhere. No path in the right column is a
proposal for a local directory. The cloud's proper nouns are spelled out here
and where the stance is stated — `AGENTS.md` § Pre-AWS architectural direction,
`README.md` § Architectural direction and this document's prose — and among the
tree's names they live in this column alone: never in a make target, a compose
service, a container environment variable, a payload key or a code comment, and
in no tracked path but this file's own `pre_aws` stem.

| this repository has | responsibility | the same responsibility elsewhere |
|---|---|---|
| the one image, `mlops-portfolio-1m-pipeline` | COMPUTE — the runtime every stage runs in | a container image in a registry (Amazon ECR) |
| `docker compose run --rm -T pipeline python -m <module>.<stage>` | COMPUTE — one stage, one one-off process | one container run (an Amazon ECS Task on AWS Fargate — a data-ingest or ml-research task) |
| a per-asset stage, `--tickers <TICKER>`, inside `asset-<ticker>` | COMPUTE — one stage for one asset | the same Task parameterised by `ASSET` (`RunTask` with `ASSET=BTC` — an asset-rebuild task) |
| one compose service per ticker under one anchor | INFRASTRUCTURE — the parameter made visible | one task definition parameterised by `ASSET`, never a new unit per asset |
| the Makefile's `all:` and `ml-all:` | ORCHESTRATION — the explicit stage order | a state machine whose states are the stages above (AWS Step Functions) |
| `store_raw_1m/cryptofuture/<venue>/minute/<symbol>/YYYYMMDD_trade.zip` | STORAGE — raw, immutable, one object per UTC day | raw objects under a venue and symbol prefix in object storage (Amazon S3) |
| `store_assets_artifacts/<TICKER>/` | STORAGE — one prefix per asset | one prefix per asset in object storage |
| `<TICKER>_research_ohlcv.duckdb` | STORAGE — the canonical market object, one writer at a time | a versioned object pulled into a Task's own disk and written back whole |
| the parquets and JSONs of the asset folder | STORAGE — research artifacts | artifact objects under the asset prefix |
| the downloaders' day-presence skip; the rerun table of `methodology_ml.md` § 11 | ORCHESTRATION — the rebuild condition, not yet code | an event rule and a condition state (Amazon EventBridge, a Step Functions choice) |
| `data_status.json`, `ml_status.json`, `store_run_records/<run_id>/` | STORAGE — status and run objects | status and run objects in object storage |
| `logs/<stage>_<docker_service>.log` and the 1 s cgroup samples of a run | MONITORING — logs and resource metrics | log streams keyed by stage and container, and metrics (Amazon CloudWatch) |
| the page files of `module_monitoring/` and the two snapshots | MONITORING — the static dashboard | static objects behind a content-delivery front (Amazon S3 with Amazon CloudFront) |
| the `/containers`, `/runs` and `/devops/*` routes | MONITORING — a small reader process | a container that stays running, not a static object |
| the Lean-exact raw tree; no Lean runtime | STRATEGY EXECUTION — absent | a separate container running QuantConnect Lean — a lean-backtest task, or a long-running service |
| `sub_module_devops`, `sub_module_dx` | INFRASTRUCTURE — the engine's views, the repository's view | a console and a repository view, not project code |

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
file per asset — trivial locally, one object pulled into a container's own disk later.
BAD: a local PostgreSQL "because the cloud should have a database".

Build the simplest local academic implementation whose architectural boundaries
would still make sense after replacing local storage, local Docker execution and
local orchestration with their standard cloud equivalents. Code shows logic and
responsibility first; the mapping decides where a boundary runs, never that a
cloud is built early. And for every name: a developer seeing only the object's
name should be able to infer what it owns, what it does and where it belongs —
standard generic domain terms locally, so that future cloud resources inherit
the same responsibility vocabulary without renaming the architecture.

## What stays as it is, and why

The tree as reviewed at commit `5ddc2fb`, in the commissioned columns. A row
disappears when the line it names does; the rows whose change was made are not
here, because they are no longer true.

| current | problem | Pre-AWS direction | change now? |
|---|---|---|---|
| `module_ml/bars.py` opens `module_data`'s database read-write; every other ML open is read-only | one stored object, two writing modules, across the storage → ML-compute line | one durable writer at a time, sequenced by `ml-all` and enforced by the whole-file lock; the three aggregation tables are a pure, idempotent function of `ohlcv_1m_canonical`; a second database is forbidden by `../module_data/skills/skill_candle_canonicalisation.md` § 13 | no — described |
| `module_data.status` takes no `--tickers`; `module_ml.status` accepts it and folds the basket regardless | one object per basket, safe only because it has one writer | a basket-wide object is produced only by the one-off vehicle, never fanned out; a per-asset object and a reader-side fold if the basket grows | no — described |
| the two snapshots are written into `module_monitoring/` and tracked | status objects live under a `module_*` and are the web root at once | classify, do not move: STORAGE produced by DATA and ML compute, tracked as a property of the demonstration so a fresh clone opens on real numbers; a future move turns four points — the two path constants, the directory `serve.py` serves, the two literal fetches — and is the prerequisite of ever narrowing the mount | no — described |
| `Dockerfile` copies no code; code and state both arrive through `.:/app` | the image is a dependency layer, not a compute artifact | said, not built: one mount is the local simplification; a future image carries the code and the mount carries the state | no — described |
| `record.py` holds the map of every stage to the artifacts it leaves | pipeline-shape knowledge in the representation module | measurement may hold stage → artifact, never the stage order or a dependency between stages; a later condition reads this table rather than starting a second | no — described |
| a recorded run fails if any stage failed *or* the dashboard probe failed; finalising needs `docker` and `git` on the host | two facts in one number; the run cannot be finalised elsewhere | a local lifecycle verdict — the chain ran and the page represents it; a future execution record judges on the exit codes alone, which are already in the record | no — described |
| `module_monitoring/` is served wholesale, four routes and a proxy beside static files | one root is page, package and status store | the files and the snapshots are static objects; the routes are a reader process | no — described |
| no callable "does this asset need a rebuild?" exists | the condition has no home; nothing is wrongly fused | keep compute unconditional; a future predicate is the `is_` / `has_` / `requires_` question above, never a lift of the downloader's loop | no — described |
| `docker-btc-all`, `docker-btc-lifecycle` | a ticker in a target name | detached from every document and page; retire when the basket grows, as their sunset notes say | no — described |
| compose project, container and network names derive from the directory | none | checkouts of LIORA can sit side by side on one host with the same service names; a fixed name would merge them | no — described |
| the image is named `mlops-portfolio-1m-pipeline`, a name older than LIORA | none for the mapping: one runtime package, no ticker | kept; the name is one runtime package with no ticker, which is all the mapping needs; two checkouts that build one tag share whichever built last, so a rename is worth doing only under a tag no sibling builds | no — described |
| `centered_rsi14` is spelled the American way | the one identifier that breaks the British spelling of the prose | a stored column, an artifact key and a feature name — a contract with files on disk that moves only with every writer and reader in one commit | no — described |
| `hpo` names the stage and the file; `hyperparameter_search_result` names the key | one term in two forms | a domain abbreviation `AGENTS.md` § Canonical vocabulary admits, spelled out where a key has no file name beside it — as UTC and OHLCV are | no — described |
| `module_ml.status` writes a basket snapshot and per-asset READMEs in one stage | two namespaces in one stage | each named: the README is an asset artifact of an asset-scoped part of that stage, the snapshot a fold over completed asset artifacts | no — described |
