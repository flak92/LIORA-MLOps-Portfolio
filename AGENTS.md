# AGENTS — the contract of this repository

The governing contract for every change, human or agent. Read the repo in
this order: **AGENTS.md → module names → `README_module_<name>.md` → the
module's own `skills/` → code**, with `module_skills/` beside them for the
rules that cross modules, indexed by `module_skills/README.md`.
(README is general information, not part of the working path.) If a change
conflicts with this file, the change is wrong.

## Values

- **Destination, not road.** *The repository shows the destination, not the road*. No tests, no security
  layers, no CI, no precautionary guardrails; the only guards are the ones the
  mathematics requires, and a stage proves itself by running.
- **Minimalism.** Every line, file, module and dependency has a concrete
  purpose. If its purpose cannot be named, it goes.
- **Minimum requirements.** Python 3.12.x with `venv` and `pip`; the container
  is `python:3.12-slim`. A library is added only when the standard library and
  the current stack — `duckdb`, `numpy`, `optuna`, `xgboost-cpu` — cannot do
  the job. `requirements.txt` declares direct dependencies only.
- **KISS / YAGNI / DRY / SOLID.** The simplest correct implementation, built
  for the need that exists, never for a hypothetical one. One responsibility
  per module; repeated logic becomes one function, not three copies.
- **UCAS — Useless Click Avoiding System.** Manual steps, clicks and context
  switches that can be automated, are: `make all` runs the whole pipeline
  from a fresh clone, every stage is idempotent, the dashboard opens itself.
- **Main = clean working logic.** No test frameworks, security layers,
  validation frameworks or precautionary guards. What stays are the seven
  guards the mathematics requires: causality invariants (`indicators.asof_index`) and
  arithmetic preconditions (the full canonical grid inside the frozen research
  window, asserted per asset by `labels.load_research_1m`, and a finite,
  positive ATR at every decision, asserted beside it; the aligned decision
  grids of the arrays `dataset.load_xy` joins by position — one guard, asserted twice, because the feature parquets agreeing with each other and X agreeing with Y are two checks; a finite feature
  matrix after the warm-up, asserted by `features.build_x`; the download that
  aborts on a short post-listing day, and the listing probe that aborts when a
  symbol's history starts after the window) — and beside them, not guards:
  the one-line message of a status stage with nothing to report, naming the
  stage to run first, and a venue's own error code surfaced as it came. A test suite, a linter,
  a coverage gate, a workflow or a merge block does not belong here. No debt
  marker in a tracked file and no code left inside a comment: a marker is a
  postponed decision, a commented-out line is a version git already holds.
  Thread caps (`nthread=1`, `OMP_NUM_THREADS=1`) are part of correctness, not
  a setting.
- **Research logic over tooling.** External sources, libraries and
  infrastructure are implementation details. The repository should expose the
  mathematical and causal research pipeline as directly as possible.
- **Source-neutral downstream.** Venue-specific logic ends at ingestion and
  data-quality provenance. Features, labels, validation, modelling and research
  simulation operate on the canonical research dataset.
- **Academic, not production.** Prefer explicit equations, causal invariants and
  reproducible transformations over production security, orchestration and
  validation frameworks.
- **Pipeline-first.** The repository exists to close one full chain:

  ```
  market sources → ingest → validation necessary for correctness → canonical dataset
  → features / labels → training / retraining → strategy / results → monitoring
  ```

## Architecture shape

`module_*` is a top-level project responsibility; `store_*` is persisted or
generated state. Four project modules — three runtime modules, in the order
the data moves through them, and one that carries no dataflow:

```
module_data/        sources → normalised raw 1m → one canonical DuckDB per asset
module_ml/          canonical dataset → X, Y → search → model → research simulation
module_monitoring/  presentation of what the two modules measured about themselves, and the server that serves it — in an asset container, the container reporting itself; around a stage, the stage reporting itself
module_skills/      the contract's companions: the register, the repository-wide skills, and the index of every module's own
```

`module_skills` never participates in runtime imports or dataflow. The asset
containers are services of `docker-compose.yml`, one per ticker of the basket,
written out under the two anchors — what every service is, and the one command
the servers add — so the topology is visible in the file
that runs it; `module_monitoring/serve.py` reaches them by service name. A new
`module_<domain>` is justified only by a distinct responsibility with a stable
input/output boundary; until then the owning module is extended.

Each `module_*` is an **extractable bounded context**: its domain rules, its
orientation and its code sit together, so it could later be lifted into its own
repository without reconstructing its meaning from documentation that stayed
behind. That is a property of how the tree is written, not a claim that any
module is already an independent service — they share one image, one bind mount
and one `config.py` for the basket, and nothing between them speaks over a
network.

Regular, predictable, symmetrical, easy to scan — the structure should be
recognisable by eye before it is parsed (neuro-optical consistency):

- **names also define visual structure.** Before introducing a file or
  directory, determine its semantic family and derive its name from that
  family's established grammar, so analogous objects sort together and both the
  object's role and its expected location are predictable from its name. The
  detailed sorting grammar lives in
  `module_skills/skill_sorting_files_naming_standard.md`;
- one obvious responsibility per module; no wrappers without logic of their own;
- analogous names for analogous objects (`download_binance.py` ↔
  `download_bybit.py`, `store_assets_artifacts/<TICKER>/<TICKER>_<artifact>.<ext>`, `ml-<stage>` ↔
  `docker-ml-<stage>` targets); each computational module (`module_data`,
  `module_ml`) measures its own domain state in `status.py`, and
  `module_monitoring` presents their snapshots;
- **taxonomic ordering — the category token comes first, so siblings sort
  together.** A listing is read by eye before it is parsed: `module_data`,
  `module_ml`, `module_monitoring`, `module_skills`, then
  `store_assets_artifacts`, `store_raw_1m`, `store_run_records` — two blocks,
  not seven scattered entries. If renaming would put things of one category next to each other,
  rename them;
- short, predictable paths, built only in a module's `config.py` — never
  assembled at the point of use; the one exception is an external format's own
  file names, built by its adapter (`module_data/lean.py` for the Lean tree,
  `module_monitoring/serve.py` and `module_monitoring/record.py` for the cgroup
  and procfs paths of their boundary)
  — and the browser, which has no config module and fetches its two snapshots
  (`data_status.json`, `ml_status.json`) and the container, run and `/devops/api/*`
  routes by literal
  name; one asset is one folder,
  `store_assets_artifacts/<TICKER>/`, one file per distinct artifact
  responsibility. The artifact folder is the ticker in capitals, the raw tree
  is the symbol in lower case because Lean demands it — that difference is a
  boundary, not an inconsistency to tidy away. A top-level path constant
  begins with the exact canonical root token, so the name predicts the
  directory: `STORE_RAW_1M_DIR` → `store_raw_1m/`, `STORE_RUN_RECORDS_DIR` →
  `store_run_records/`, `MODULE_MONITORING_DIR` → `module_monitoring/`;
- one convention per language: BEM in CSS, snake_case in Python and JSON,
  the same hierarchy everywhere, no accidental exceptions.

## Pre-AWS architectural direction

Pre-AWS is this repository's word for its own shape: a local, academic
architecture whose boundaries would still be the right boundaries after local
storage, local container execution and local stage order were replaced by their
standard equivalents on Amazon Web Services (AWS). No cloud is used and none is
planned; the mapping is described in `module_skills/skill_pre_aws_solution.md`
and built nowhere.

- **Academic, not AWS.** The runtime is local — a venv, or one image under
  docker compose — and the goal is a correct dataflow with visible
  responsibilities: a demonstrator, not a deployment.
- **Every boundary decision weighs the future mapping.** Where a function lives,
  who writes a file, what a stage takes as its parameter, how a container is
  started — each is chosen so the mapping stays a rename, never a redesign;
  nothing is implemented for the cloud.
- **No cloud complexity without an academic need.** A mechanism that exists only
  because production would require it, and that the research logic does not
  need, is described in the skill as its future equivalent and never built here.
  Stated, not mitigated.
- **The asset is the namespace.** `ASSET=<TICKER>` — `--tickers` at the process
  boundary — selects every datum and artifact; no code, file, target or service
  definition is named for a ticker; a new asset is one line in `TICKERS` and one
  block under the compose anchor.
- **Compute owns no state.** A stage reads a store, writes a store and exits; it
  holds nothing between invocations, binds no port, reads no `ASSET` and assumes
  no resident peer.
- **Storage is separate from compute.** Pipeline state lives at paths one
  `config.py` per module builds — the `store_*` roots and the two tracked
  snapshots — never inside a container; the one bind mount carries code and
  state together as a local convenience, not as a contract.
- **Modules are built by ownership and lifetime.** A function sits beside the
  functions that write the same state and live as long as it does, never beside
  what happened to be written with it; every object is classified before it is
  placed.
- **Names carry the responsibility.** A name says what the object is, what it
  does and where it belongs — a service by its runtime role, a store by what it
  holds, a function by its verb from the closed list or by the quantity it is;
  local names never imitate cloud resources, and cloud resources would inherit
  the local vocabulary unchanged.
- **The Makefile is the local developer interface.** It names stages after their
  modules, lists their order and never schedules; orchestration sits above the
  stages and inside none.
- **Docker is compute.** A container is the local counterpart of the one-off
  container a cloud runtime would launch per stage and per asset; the resident
  `asset-<ticker>` is how the fan-out and the panel do it locally, and no stage
  depends on it.
- **A few assets are proof enough.** The whole chain on `BTC` demonstrates the
  architecture; scale is `ASSET=<ticker>`, never hundreds of assets.

Cloud proper nouns are external vocabulary and live in the skill's mapping table
alone — never in a path, a make target, a compose service, an environment
variable, a payload key or a code comment. The non-goals, the twelve classes,
the review of what stays local and the mapping table are
`module_skills/skill_pre_aws_solution.md` — the second cross-cutting skill of
the kind § The default choice names.

## Canonical vocabulary

**Names must be self-explanatory before they are project-specific. Prefer
established software-engineering terminology over project-specific synonyms: if
a concept already has a widely recognised name, use that name — in code, in
documentation, in the skills and in the interface alike — and do not invent
local terminology for a standard concept. A glossary confirms meaning; it must
not be required to decode an obscure name.**

One concept, one name — in the code, in the artifacts, in the interface, in the
Makefile, in docker compose and in the documents. The
register is `module_skills/glossary.md`, and a new name enters it in the same
commit that introduces it. The word "test" never names a fold.

And one name, one concept. A name that could denote two things **in the same
scope** is renamed until it denotes one. The scopes are enumerated so the rule
applies without argument: make targets, compose services, container environment
variables, tracked paths, and Python symbols within a module. A name shared across *different* scopes is not a
collision — the module `module_ml/status.py` and the route `GET /status` are
addressed by different tools and never appear in one listing.

**Derived, never drafted.** A derived artifact is generated from source and
config and never hand-edited: `<TICKER>_parameters.json`, `<TICKER>_README.md`,
the two snapshots. A hand edit to one is a violation.

**Rule-derived structure over repeated project knowledge.** When a family —
assets, venues, timeframes, paths, artifact files, payload keys, pipeline stages
— is governed by one definition, derive the repeated representations from it
rather than copying the same list into several files: `TICKERS` in
`module_data/config.py` is the one definition the paths, the fan-out and the
`/containers` registry derive from. The limit is equally binding: no generator,
no metaprogramming, no abstraction layer for a one-off value — and none for a
file whose whole value is being read. `docker-compose.yml` spells its asset
services out under its anchors, one per ticker, because a topology a reader can see beats one a
reader has to run a generator to see.

Every layer has a closed grammar, the way CSS has BEM. A name is **derived**
from its layer's grammar, never invented:

| layer | grammar | in this repo | what it forbids |
|---|---|---|---|
| constants | `<OBJECT>_<ROLE>_<PARAMETER>_<UNIT>` | `RSI_WILDER_SMOOTHING_PERIOD_BARS` | `RSI_N` |
| external I/O functions | `<verb>_<object>`, verb from the closed list `fetch_` (network), `load_` (storage → memory), `write_` (persist), `parse_` (bytes → values) | `fetch_klines`, `load_xy`, `write_parquet`, `parse_zip` | `get_`, `process_`, `handle_` |
| conversions | `to_<representation>` | `to_class`, `to_json_safe` | ambiguous `convert` |
| composite constructors | `build_<object>` | `build_x` | `make_stuff` |
| functions that *are* a quantity | no verb — the name is what it returns | `rsi`, `atr`, `sharpe_annualised`, `triple_barrier` | `calculate_rsi` |
| pure descriptors | a noun phrase naming the returned object; a descriptor does no I/O — the moment it fetches, loads or writes it takes that verb, the moment it assembles it takes `build_` | `symbol`, `artifact_dir`, `fold_bounds` | `get_fold_bounds`, `fetch_symbol` |
| populations of rows | `<population>_set` / `_window` | `training_set`, `scoring_set`, `prediction_window` | `get_train_indices` |
| report fragments | `<section>_block` | `sample_block`, `strategy_block`, `hyperparameter_search_result_block` | `make_sample_dict` |
| statement constants (SQL text) | `<OBJECT>_<KIND>`, kind from the closed list `DDL`, `INSERT`, `SCAN`, `PREDICATE`, `COLUMNS` | `CANONICAL_DDL`, `BAR_INSERT`, `VENUE_SCAN`, `OHLC_INTACT_PREDICATE`, `Y_COLUMNS` | `SOURCE_SWITCHES`, `QUERY_1` |
| conversion factors | `<UNIT>_PER_<UNIT>` | `MILLISECONDS_PER_MINUTE`, `MINUTES_PER_DAY` | `MS_MIN`, `60_000` inline |
| module-private helpers | a leading `_` on the name its layer's grammar gives, for a helper no other module may import | `_pnl_block`, `_classification_block`, `_utc_ms` | an `_` name imported by another module |
| CLI entry | `main()` — one per stage module, returning the exit code | `main` | `run`, `cli`, `entrypoint` |
| quantities | `<what>_<unit>` | `fold_start_ms`, `equity_1m`, `returns_15m` | `n_min`, `off` |
| index arrays | `<population>_rows` | `training_rows`, `window_rows`, `scoring_rows` | `tr`, `wi`, `oi` |
| booleans | `<subject>_<predicate>`, stating the condition that is true; a function that asks takes `is_`, `has_` or `requires_` — state, possession, obligation | `entry_observable`, `label_valid`, `is_full_utc_day()`, `is_artifact_set_complete()` | `flag`, `ok`, `check`; `should_`, `check_`, `needs_`, a bare `trigger` |
| artifact keys | snake_case, the same word as the identifier that produced it; a count is `<what>_count`, a quantity with a unit `<what>_<unit>`, a share `_pct`, a formatted UTC string `_utc`, epoch milliseconds `_ms` | `scored_row_count`, `ffill_bars`, `coverage_pct`, `generated_at_utc` | a separate vocabulary for JSON; a bare plural (`gaps`) or an adjective (`ambiguous`) as a count; `n_`; `ret` for return |
| features | `<computation>[<parameter>]_<timeframe>` | `ema20_minus_ema50_over_atr14_4h`, `centered_rsi14_1h`, `range_position_20_15m` | `feature_3`, `f_rsi` |
| stored columns | the quantity for OHLCV, `<what>_<unit>` for anything derived, `<subject>_<predicate>` for a boolean — and a column and the key that publishes it carry **one** name | `timestamp_ms`, `ffill_bars`, `zero_volume_bars`, `binance_valid` | `n_ffill`, a column and key that disagree |
| Makefile targets | `<module>-<stage>` for a stage of a runtime module, `docker-<module>-<stage>` for its container twin; only the lifecycle targets go bare (`all`, `setup`, `help`, `docker-build`, `docker-up`, `docker-down`, `docker-all`, `docker-all-record`), and a ticker alias of one of them carries its own sunset note | `data-ingest`, `ml-hpo`, `docker-ml-train` | a bare stage (`ingest`), a twin named after the tool (`docker-run`) |
| directories | `<category>_<detail>/`; a raw store names its granularity with the compact timeframe token, `store_raw_<timeframe>/` | `module_*`, `store_*`, `store_raw_1m` | a kind scattered through the alphabet, a store spelling its timeframe in sorting slots |
| a module's own skills | `module_<name>/skills/`, holding every rule about that module and nothing else | `module_data/skills/`, `module_ml/skills/`, `module_monitoring/skills/` | a single module's rule kept in `module_skills/`; a second copy of one rule in both |
| a module's orientation | `README_module_<name>.md`, the name derived from the module directory it sits in | `module_data/README_module_data.md`, `module_ml/README_module_ml.md`, `module_monitoring/README_module_monitoring.md` | `module_data/README.md`; an orientation file that restates a skill |
| artifact files of one timeframe family | `<asset>_<artifact>_<timeframe-slot>.<ext>`, slots per the standard `ss-mm-hh-dd-MM` (`module_skills/skill_sorting_files_naming_standard.md`) | `BTC_features_ss-15-hh-dd-MM.parquet`, `BTC_features_ss-mm-04-dd-MM.parquet` | `BTC_features_15m.parquet` — siblings that no listing orders by granularity |
| CSS | BEM `block__element--modifier`, the class named for what it marks | `frame__head`, `pill--active`, `final-holdout` | `.red`, `.diag` |
| JavaScript functions at file scope | lowerCamelCase, verb from the closed list `build<Object>` (returns a DOM node), `render<Section>` (writes into the page), `format<Value>` (value → string), `append<Child>` (mutates a parent), `select<Target>`, `init<Component>`, `fetch<Object>` (network, returns a promise); a quantity or a descriptor carries no verb | `buildMeter`, `renderStrategy`, `formatBytes`, `appendCell`, `fetchContainerStatus`, `mean`, `validationFolds` | `makeTable`, `pollContainers`, a bare noun for a builder (`cell()`, `sparkline()`) |

Constants that carry a numeric quantity — a count, a rate, a duration, a
size, an interval — are named `<OBJECT>_<ROLE>_<PARAMETER>_<UNIT>`, and the
unit is explicit — `_BARS`, `_MINUTES`, `_MS`, `_SECONDS`, `_DAYS`, `_ROWS`,
`_FOLD_ID`, `_RATE`, `_COUNT` — unless the name already says what is counted
(`MINIMUM_TRADES_PER_VALIDATION_FOLD`). Enumerations, paths and names carry no
unit; a collection whose values are quantities keeps theirs
(`TIMEFRAME_DURATION_MS`, `FOLD_BOUNDS_MS`, `VALIDATION_FOLD_IDS`). No name is
invented just to satisfy the schema. The parameter word follows the mechanics
— `SPAN` for an EMA,
`SMOOTHING_PERIOD` for a Wilder recursion, `LOOKBACK` for a real rolling
window, `HORIZON` for the future of a label, `INTERVAL` for a sampling step.
A compact timeframe token inside an identifier (`WARMUP_4H_BARS`, `equity_15m`,
`ohlcv_15m_canonical`) is the timeframe vocabulary of code and schema; the slot
standard governs filesystem names only.
Domain abbreviations (ATR, RSI, EMA, OHLCV, UTC, OOS, HPO, XGBoost) stay
and are spelled out on first use in the documentation; local ones (`N`, `W`,
`TF`, `MIN`, `MAX`, `K`, `XGB`) never cross a function boundary. A one-letter
name is legal because of its semantic role, never merely because it is local:
loop indices, the symbols of a published equation inside its tight kernel, and
SVG geometry may stay short — a domain object (a ticker, an asset, a status
payload, a strategy, a metrics block) carries its semantic name even inside a
function. Write
"QuantConnect Lean" on first use, "Lean" afterwards. British spelling
throughout the prose (`-ise`, `-isation`); language keywords keep their own spelling. At an
external-format or external-library boundary the external vocabulary wins
inside the call that speaks it, and project names begin at the return value.
The boundaries, each with the file that owns it: the QuantConnect Lean tree
(`module_data/lean.py`), the Binance and Bybit REST parameters
(`download_binance.py`, `download_bybit.py`), xgboost and optuna
(`module_ml/model.py`, `module_ml/hpo.py`), numpy (every module that computes),
argparse (`module_data/config.py`, `module_data/status.py`,
`module_monitoring/sub_module_dx/visualise.py`), DuckDB SQL (every module that queries), the SVG
and DOM attributes (every `*.js` of `module_monitoring`, its sub-modules included, and the canvas of
the drawing's template), docker compose (`Makefile`,
`docker-compose.yml`), `urllib` (`module_monitoring/serve.py` and both downloaders),
`http.server` (`module_monitoring/serve.py` and the panel's own), cgroup v2 and procfs
(`module_monitoring/serve.py`), `socket` and the Docker Engine API over its unix socket
(`module_monitoring/sub_module_devops/`), and `posix_spawn`, `wait4` rusage and the
per-process procfs of a wrapped stage (`module_monitoring/record.py`). A
boundary is an exception the conventions name, not an inconsistency they
tolerate.

## Rejected vocabulary

The rejected vocabulary stays as a list of words that steers the repository
toward a lower level of vectors, guiding AI agents toward useful embeddings for
solving problems in a concrete and minimally correct way. No check stands
behind it. The last column of the grammar table holds the forms bound to one
rule and the register's `never` columns the synonyms bound to one concept; this
list holds the words bound to neither.

- **directories and path segments:** `src`, `core`, `lib`, `common`, `utils`,
  `helpers`, `manager`, `service`, `assets`, `artifacts`, `data`, `db`,
  `database`, `raw_data`, a lowercase ticker folder, a venue symbol as a folder
- **module and file stems:** `module_compose`, `module_docker`,
  `module_capsule`, `module_asset`, `module_viz`; `dashboard.py`, `proxy.py`,
  `server.py` beside `serve.py`; a strategy file per asset, a parameters file
  per stage, an `export` stage, a per-asset OHLCV parquet; a module named for
  a cloud resource (`module_s3`, `module_ecs`, `module_eventbridge`); `worker`,
  `processor`
- **function verbs:** `read_`, `probe_`, `spool_`, `iter_`, `run_`, `compute_`,
  `_factory`; in JavaScript `load`, `poll`
- **key names:** bare `lag`, `age`, `usage` — without the subject and the unit —
  `mem`, `cpu_pct`, a bare duration for how long a container has been up, a
  hash, `weight` as a Y column, `_ts` on a UTC string
- **interface words:** `online` / `offline`, `alive`, `healthy`, `running` for
  an endpoint, `RAM`, `RSS`, `load`, `utilisation`, `freshness`, `boot`;
  `pill`, `chip`, `tile`, `stat` for a badge; `badge--off`, `status--red`, a
  coloured row; `mobile`, `tablet`, `phone`, `responsive`, `breakpoint`
- **tool and process words:** `-f` or `COMPOSE_FILE` on the compose line, a
  second compose file, `/var/run/docker.sock` in any container other than
  `devops` — the one service whose responsibility is docker management, and
  which publishes no port (`module_skills/skill_asset_containers.md`); `TODO`, `FIXME`,
  `XXX`, `HACK`; test suite, linter, coverage gate, CI, workflow, hook,
  generator, framework; `authority`, `single source of truth`; `one-shot` for a
  one-off; `cloud-ready`, `AWS-ready`, `cloud-native`; `s3://` in a path
  constant, an adapter for a cloud that is not there

## The default choice

For every new change, prefer **the smallest, most modular and most obvious
implementation that correctly closes the full pipeline.**

**A skill belongs to the module whose responsibility it describes.** A rule
about one module lives in `module_<name>/skills/`; a rule that crosses modules
or governs the repository lives in `module_skills/`; a module's orientation is
its `README_module_<name>.md`. Each exists exactly once, the location follows
ownership, and there is no second copy to drift.
`module_skills/README.md` is the index — it links to every skill, cross-cutting
and module-owned alike, and restates none of them.

`module_skills/skill_asset_containers.md` is the worked example of the cross-cutting
boundary: one image, the `pipeline` and `asset-<ticker>` services, the Makefile
fan-out, the ceilings and the bind mount are a contract between the
infrastructure and all three runtime modules at once, so it belongs to none of
them and stays in `module_skills/`.

A **sub-module** is the one boundary in this shape: `sub_module_<domain>/` inside
the module that owns it, with its own `config.py`, its own `main()` and no
dataflow of its own. It exists twice, both inside `module_monitoring`: the
developer-experience drawing in `sub_module_dx/`, and the DevOps panel in
`sub_module_devops/`. Both are nested rather than promoted because the
dashboard serves its own directory — a top-level module would have to be given a
route, and each page reaches the browser as a static file instead. The panel adds
one route for its API alone, because an API is not a file; the socket it holds is
the reason it is a service of its own rather than a role of `serve.py`.
`sub_module_*` does not enter the directory grammar above: two occurrences are a
coincidence, and the third one mints it or nothing does.
