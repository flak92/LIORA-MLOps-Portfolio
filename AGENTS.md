# AGENTS — the contract of this repository

The governing contract for every change, human or agent. Read the project in
this order: **AGENTS.md → module names → each module's package and its
`config.py` → code**. This file and `README.md` are the whole prose of the tree:
the contract here, the overview there, and every other rule in the comment beside
the code it governs. No third prose file is created. If a change conflicts with
this file, the change is wrong.

## Values

- **Destination, not road.** *The repository shows the destination, not the road*. No tests, no security
  layers, no CI, no precautionary guardrails; the only guards are the ones the
  mathematics requires, and a stage proves itself by running.
- **Minimalism.** Every line, file, module and dependency has a concrete
  purpose. If its purpose cannot be named, it goes.
- **Minimum requirements.** Python 3.12.x with `venv` and `pip`; the container
  is `python:3.12-slim`, one image for the tree. A library is added
  only when the standard library and the current stack — `duckdb`,
  `mlflow-skinny`, `numpy`, `optuna`, `xgboost-cpu` — cannot do the job, or when
  it is the field's own instrument for a responsibility this project names and
  the stack's equivalent would be a private reimplementation of it: § Canonical
  vocabulary's preference for an established name over a local synonym, read
  forward from names to instruments. `mlflow-skinny` is the one such addition
  and the trial ledger the one such responsibility. `requirements.txt` declares
  the project's direct dependencies only, one pinned version each.
- **KISS / YAGNI / DRY / SOLID.** The simplest correct implementation, built
  for the need that exists, never for a hypothetical one. One responsibility
  per module; repeated logic becomes one function, not three copies.
- **UCAS — Useless Click Avoiding System.** Manual steps, clicks and context
  switches that can be automated, are: `make all` runs the whole pipeline
  from a fresh recursive clone, every stage is idempotent, the dashboard opens
  itself.
- **Main = clean working logic.** No test frameworks, security layers,
  validation frameworks or precautionary guards. What stays are the seven
  guards the mathematics requires: causality invariants (`indicators.asof_index`) and
  arithmetic preconditions (the full canonical grid inside the frozen research
  window, asserted per asset by `labels.load_research_1m`, and a finite,
  positive ATR at every decision, asserted beside it; the aligned decision
  grids of the arrays `dataset.load_xy` joins by position — one guard, asserted twice, because the feature parquets agreeing with each other and X agreeing with Y are two checks; a finite
  catalogue after the warm-up, asserted by `catalogue.build_catalogue`; the download that
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
generated state. Four modules — one Python package `module_<domain>` each, in
the order the data moves through them — and, around them, the launcher that runs
them and carries no dataflow of its own:

```
module_data/         sources → normalised raw 1m → one canonical DuckDB per asset
module_features/     canonical DuckDB → the bars of the register → the feature catalogue, one parquet per timeframe, the per-asset contract and its snapshot
module_ml/           the catalogue and the canonical path → X, Y → search → model → research simulation
module_monitoring/   presentation of what the three computational modules measured about themselves and of what record.py measured around every stage, and the server that serves it — in an asset container, the container reporting itself
the root             the Makefile and docker-compose.yml that run the four, record.py, the developer-experience drawing (sub_module_dx/), the five stores, and the canon: this contract and the overview beside it
```

Each module holds its package under one directory; nothing above it belongs to
one module alone. `make all` from a fresh clone runs the chain. A reference is a path in
backticks, always.

**No module imports another.** What would cross a module boundary as an import crosses it as a
file in a store instead — the five `STORE_*_DIR` the launcher names
and `README.md` § The stores tabulates, the per-asset contract
`<TICKER>_catalogue.json` the feature layer writes and every ML stage reads, the
three snapshots each computational module writes about itself and the dashboard
serves, the run record `record.py` writes around every stage — or as a copy marked
`# twice by extraction` where it is defined, each marker naming its counterparts
in its own line, identical to the byte on every side. The basket is the launcher's: `TICKERS` in the
`Makefile`, and one `asset-<ticker>` service per ticker in its
`docker-compose.yml`; every stage is told its assets by `--tickers` and defines
none. The asset containers are services of that compose file, one per ticker of
the basket, written out under the three anchors — the store contract every
service reads, what every service is, and the one command the servers add — so
the topology is visible in the file that runs it; `module_monitoring/serve.py`
reaches them by service name. A new `module_<domain>` is justified only by a
distinct responsibility with a stable input/output boundary; until then the
owning module is extended, and no repository is ever created for what two
modules share — a dozen shared lines are a registered duplicate, not a `common`.
`module_features` is that case: its input is the canonical series, its output
one parquet per timeframe that any model could read and the contract that names
them, and nothing above it in the dataflow imports it.

Each `module_*` is an **extracted bounded context**: its domain rules, its
orientation and its code sit together in its own repository, so its meaning is
never reconstructed from documentation that stayed elsewhere. It builds its own
image from its own tree alone (`docker build` in the repository, outside any
workspace), runs standalone against the stores its `Makefile` is pointed at
(`make setup`, then `make <module>-<stage> ASSET=<TICKER>` in a venv), and knows
nothing of the others: they share the store contract, the files it names and the
copies the register lists, and nothing between them speaks over a network.

Regular, predictable, symmetrical, easy to scan — the structure should be
recognisable by eye before it is parsed (neuro-optical consistency):

- **names also define visual structure.** Before introducing a file or
  directory, determine its semantic family and derive its name from that
  family's established grammar, so analogous objects sort together and both the
  object's role and its expected location are predictable from its name. The
  detailed sorting grammar is § Sorting and the timeframe slots;
- one obvious responsibility per module; no wrappers without logic of their own;
- analogous names for analogous objects (`download_binance.py` ↔
  `download_bybit.py`, `store_assets_artifacts/<TICKER>/<TICKER>_<artifact>.<ext>`, `ml-<stage>`
  targets); each computational module (`module_data`,
  `module_features`, `module_ml`) measures its own domain state in `status.py`,
  and `module_monitoring` presents their snapshots;
- **taxonomic ordering — the category token comes first, so siblings sort
  together.** A listing is read by eye before it is parsed: at the root
  `module_data`, `module_features`, `module_ml`,
  `module_monitoring` — the chain in its own order, the
  module's position in the chain at the time it was seated; a new module takes
  the next free number and nothing is ever renumbered — then `sub_module_dx`,
  then `store_assets_artifacts`, `store_raw_1m`,
  `store_run_records`, `store_status`, `store_trials`: blocks, not scattered entries. If
  renaming would put things of one category next to each other, rename them;
- short, predictable paths, built only in a module's `config.py` — never
  assembled at the point of use; the one exception is an external format's own
  file names, built by its adapter (`module_data/lean.py` for the Lean tree,
  `module_monitoring/serve.py` for the cgroup and procfs paths of its boundary,
  `record.py` for the four pipeline stores it lists)
  — and the browser, which has no config module and fetches its three snapshots
  (`data_status.json`, `features_status.json`, `ml_status.json`) under
  `/store_status/` and the container, run and `/devops/api/*` routes by literal
  name; one asset is one folder,
  `store_assets_artifacts/<TICKER>/`, one file per distinct artifact
  responsibility. The artifact folder is the ticker in capitals, the raw tree
  is the symbol in lower case because Lean demands it — that difference is a
  boundary, not an inconsistency to tidy away. A top-level path constant
  begins with the exact canonical root token, so the name predicts the
  directory it names — on the host `STORE_RAW_1M_DIR` → `store_raw_1m/`,
  `STORE_RUN_RECORDS_DIR` → `store_run_records/`, in a container the same
  variables → `/store/raw_1m`, `/store/run_records`;
- one convention per language: BEM in CSS, snake_case in Python and JSON,
  the same hierarchy everywhere, no accidental exceptions.

## Pre-AWS architectural direction

Pre-AWS is this repository's word for its own shape: a local, academic
architecture whose boundaries would still be the right boundaries after local
storage, local container execution and local stage order were replaced by their
standard equivalents on Amazon Web Services (AWS). No cloud is used and none is
planned; the mapping is drawn — the deployment view of the developer-experience
drawing seats every tracked file beside the primitive that would hold the same
responsibility — and built nowhere.

- **Academic, not AWS.** The runtime is local — one image per module under
  docker compose, driven by a Makefile — and the goal is a correct dataflow with visible
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
  boundary — selects every datum and artifact; no code, file, function or
  service definition is named for a ticker — `asset-<ticker>` is one instance
  of the asset container, and a ticker may name a convenience alias in the
  Makefile, with its sunset note, never a target another file depends on; a new
  asset is one line in the `Makefile`'s `TICKERS` and one
  `asset-<ticker>` block in its `docker-compose.yml`, and nothing in any module.
- **Compute owns no state.** A stage reads a store, writes a store and exits; it
  holds nothing between invocations, binds no port, reads no `ASSET` and assumes
  no resident peer.
- **Storage is separate from compute.** Pipeline state lives in the five stores
  — the `store_*` roots, named to every `config.py` by its
  `STORE_*_DIR` and mounted at `/store/<content>` into each service that touches
  them, read-only where a service only reads — never
  inside a container and never inside a repository's tree; the image carries the
  pins and nothing else, the code and the state arrive as mounts, and the three
  snapshots are the one store that is tracked.
- **Modules are built by ownership and lifetime.** A function sits beside the
  functions that write the same state and live as long as it does, never beside
  what happened to be written with it; every object is classified before it is
  placed.
- **Every placement is argued.** Before an object is committed, § The naming
  review answers where it lives, what it sits beside and which boundary it
  draws; an object whose responsibilities answer to no primitive of the
  deployment view, or to two, is questioned first.
- **Names carry the responsibility.** A name says what the object is, what it
  does and where it belongs — a service by its runtime role, a store by what it
  holds, a function by its verb from the closed list or by the quantity it is;
  local names never imitate cloud resources, and cloud resources would inherit
  the local vocabulary unchanged.
- **The Makefile is the local developer interface.** It names stages after their
  modules, lists their order and never schedules; orchestration sits above the
  stages and inside none.
- **Docker is compute.** A container is the local counterpart of the one-off
  container a cloud runtime would launch per stage and per asset; the runners
  `data`, `features` and `ml` are how the fan-out does it locally, the resident
  `asset-<ticker>` only reports itself, and no stage depends on it.
- **A few assets are proof enough.** The whole chain on `BTC` demonstrates the
  architecture; scale is `ASSET=<TICKER>`, never hundreds of assets.

Cloud proper nouns are external vocabulary. Apart from the repository's own word
*Pre-AWS*, they are spoken in exactly two places: this section, where the stance
is stated, and the `deployment` block of `sub_module_dx/visualisation_config.json`
with the page drawn from it, where each one names the primitive a local object
would become. Never in a make target, a compose service, an environment
variable, a payload key, a code comment, an identifier or a tracked path.

## Canonical vocabulary

**Names must be self-explanatory before they are project-specific. Prefer
established software-engineering terminology over project-specific synonyms: if
a concept already has a widely recognised name, use that name — in code, in
documentation, in the comments and in the interface alike — and do not invent
local terminology for a standard concept. No glossary is kept: a name that needs
one is the wrong name.**

One concept, one name — in the code, in the artifacts, in the interface, in the
Makefile, in docker compose and in the two documents. The tree is its own
register: before minting a name, `git grep` it, and a name that already denotes
something else in the same scope is renamed until it denotes one thing. The word
"test" never names a fold.

And one name, one concept. A name that could denote two things **in the same
scope** is renamed until it denotes one. The scopes are enumerated so the rule
applies without argument: make targets, compose services, container environment
variables, tracked paths, and Python symbols within a module. A name shared across *different* scopes is not a
collision — the module `module_ml/status.py` and the route `GET /status` are
addressed by different tools and never appear in one listing.

**Derived, never drafted.** A derived artifact is generated from source and
config and never hand-edited: `<TICKER>_parameters.json`,
`<TICKER>_feature_set_search.json`, `<TICKER>_README.md`, `<TICKER>_catalogue.json`,
the three snapshots and the developer-experience drawing
(`sub_module_dx/files_and_folders_visualisation.html`). A hand edit to one is a
violation.

**Rule-derived structure over repeated project knowledge.** When a family —
assets, venues, timeframes, paths, artifact files, payload keys, pipeline stages
— is governed by one definition, derive the repeated representations from it
rather than copying the same list into several files: `TICKERS` in the
orchestration `Makefile` — the launcher — is the one definition the fan-out and
every `--tickers` derive from; a module is told its assets and never defines
them, and the `/containers` registry lists the asset folders the store holds.
The limit is equally binding: no generator,
no metaprogramming, no abstraction layer for a one-off value — and none for a
file whose whole value is being read. `docker-compose.yml` spells its asset
services out under its anchors, one per ticker, because a topology a reader can see beats one a
reader has to run a generator to see.

Every layer has a closed grammar, the way CSS has BEM. A name is **derived**
from its layer's grammar, never invented:

| layer | grammar | in this repo | what it forbids |
|---|---|---|---|
| constants | `<OBJECT>_<ROLE>_<PARAMETER>_<UNIT>` | `ATR_WILDER_SMOOTHING_PERIOD_BARS` | `RSI_N` |
| external I/O functions | `<verb>_<object>`, verb from the closed list `fetch_` (network), `load_` (storage → memory), `write_` (persist), `parse_` (bytes → values) | `fetch_klines`, `load_xy`, `write_parquet`, `parse_zip` | `get_`, `process_`, `handle_` |
| conversions | `to_<representation>` | `to_class`, `to_json_safe` | ambiguous `convert` |
| composite constructors | `build_<object>` | `build_x` | `make_stuff` |
| functions that *are* a quantity | no verb — the name is what it returns | `rsi`, `atr`, `sharpe_annualised`, `triple_barrier` | `calculate_rsi` |
| pure descriptors | a noun phrase naming the returned object; a descriptor does no I/O — the moment it fetches, loads or writes it takes that verb, the moment it assembles it takes `build_` | `symbol`, `artifact_dir`, `fold_bounds` | `get_fold_bounds`, `fetch_symbol` |
| populations of rows | `<population>_set` / `_window` | `training_set`, `scoring_set`, `prediction_window` | `get_train_indices` |
| report fragments | `<section>_block` | `sample_block`, `strategy_block`, `hyperparameter_search_result_block` | `make_sample_dict` |
| statement constants (SQL text) | `<OBJECT>_<KIND>`, kind from the closed list `DDL`, `INSERT`, `SCAN`, `PREDICATE`, `COLUMNS` | `CANONICAL_DDL`, `BAR_INSERT`, `VENUE_SCAN`, `OHLC_INTACT_PREDICATE`, `Y_COLUMNS` | `SOURCE_SWITCHES`, `QUERY_1` |
| conversion factors | `<UNIT>_PER_<UNIT>` | `MILLISECONDS_PER_MINUTE`, `MINUTES_PER_DAY` | `MS_MIN`, `60_000` inline |
| module-private helpers | a leading `_` on the name its layer's grammar gives, for a helper no other module may import | `_pnl_block`, `_classification_block` | an `_` name imported by another module |
| CLI entry | `main()` — one per stage module, returning the exit code | `main` | `run`, `cli`, `entrypoint` |
| quantities | `<what>_<unit>` | `fold_start_ms`, `equity_1m`, `returns_15m` | `n_min`, `off` |
| index arrays | `<population>_rows` | `training_rows`, `window_rows`, `scoring_rows` | `tr`, `wi`, `oi` |
| booleans | `<subject>_<predicate>`, stating the condition that is true; a function that asks takes `is_`, `has_` or `requires_` — state, possession, obligation | `entry_observable`, `label_valid`, `is_full_utc_day()`, `is_artifact_set_complete()` | `flag`, `ok`, `check`; `should_`, `check_`, `needs_`, a bare `trigger` |
| artifact keys | snake_case, the same word as the identifier that produced it; a count is `<what>_count`, a quantity with a unit `<what>_<unit>`, a share `_pct`, a formatted UTC string `_utc`, epoch milliseconds `_ms` | `scored_row_count`, `ffill_bars`, `coverage_pct`, `generated_at_utc` | a separate vocabulary for JSON; a bare plural (`gaps`) or an adjective (`ambiguous`) as a count; `n_`; `ret` for return |
| features | `[<normaliser>_]<term>{_<operator>_<term>}_<timeframe>`, a term `[<series>_]<indicator><parameter>` or a bare series, read off the catalogue record — the rest is § The feature grammar | `ema20_minus_ema50_over_atr14_4h`, `centered_rsi14_1h`, `range_position20_15m`, `close_minus_sma200_over_atr14_4h` | `feature_3`, `f_rsi`, `rsi_14`, `sma_200`, `trend_4h` |
| stored columns | the quantity for OHLCV, `<what>_<unit>` for anything derived, `<subject>_<predicate>` for a boolean — and a column and the key that publishes it carry **one** name | `timestamp_ms`, `ffill_bars`, `zero_volume_bars`, `binance_valid` | `n_ffill`, a column and key that disagree |
| Makefile targets | `<module>-<stage>` for a stage of a runtime module — run in a one-off container of that module's runner — and `<module>-all` for its chain; `tmux-<module>-<stage>` for the detached twin of a stage that outlives the terminal — only a stage that resumes may have one; only the lifecycle targets and the repository's own tools go bare (`all`, `build`, `help`, `on`, `off`, `all-record`, `dx-update`), `on` / `off` being the presentation switch, and a ticker alias of a lifecycle target carries its own sunset note, run in its venv with `ASSET=<TICKER>` — by `python3` where the module has no dependency — beside `setup` and `help` | `data-ingest`, `ml-hpo`, `features-all`, `tmux-ml-feature-set-search`, `on` | a bare stage (`ingest`), a `docker-` twin of a stage (there is one way to run a stage), a target named after the tool (`docker-run`), a detached twin of a stage that cannot resume, a second switch pair (`start` / `stop`, `up` / `down`), a second Makefile carrying stage order of its own |
| directories | `<category>_<detail>/`; a raw store names its granularity with the compact timeframe token, `store_raw_<timeframe>/` at the time it was seated — a new module takes the next free number and nothing is ever renumbered | `module_*`, `store_*`, `store_raw_1m` | a kind scattered through the alphabet, a store spelling its timeframe in sorting slots, a renumbered checkout, `repository_module_<domain>/` |
| images | `liora-1m-pipeline`, one for the tree, built from the root `Dockerfile` | `liora-1m-pipeline` | compose's `<project>-<service>` default, an image per service, an image per asset, one image for every module |
| compose services | a runtime role, never an image or a ticker in code — the runners `data`, `features`, `ml`, the residents `dashboard`, `asset-<ticker>`, `devops` | `ml`, `asset-btc` | `pipeline`, a service named for an image or a tool, a service per asset stage |
| store paths | `store_<content>/` on the host, `/store/<content>` inside a container, `STORE_<CONTENT>_DIR` the variable that names the one to the other | `store_raw_1m/`, `/store/raw_1m`, `STORE_RAW_1M_DIR` | a path derived from `__file__`, `/app/store_*` as an address, a store literal at the point of use |
| artifact files of one timeframe family | `<asset>_<artifact>_<timeframe-slot>.<ext>`, slots per the standard `ss-mm-hh-dd-MM` (§ Sorting and the timeframe slots) | `BTC_features_ss-15-hh-dd-MM.parquet`, `BTC_features_ss-mm-04-dd-MM.parquet` | `BTC_features_15m.parquet` — siblings that no listing orders by granularity |
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
window, `HORIZON` for the future of a label, `INTERVAL` for a sampling step. A
parameter carried by a term of the feature catalogue (`("ema", 20)`) is the
descriptor's own and is never copied into a named constant: the record is the
one place the number lives.
A compact timeframe token inside an identifier (`ANNUALISATION_PERIOD_15M_BARS`, `equity_15m`,
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
(`module_ml/model.py`, `module_ml/hpo.py`), mlflow (`module_ml/hpo.py`), numpy (every module that computes),
argparse (`module_data/config.py`, `module_features/config.py`, `module_ml/config.py` — the one parser, twice by extraction —,
`module_ml/feature_set_promote.py`, `sub_module_dx/visualise.py`), DuckDB SQL (every module that queries), the SVG
and DOM attributes (every `*.js` of `module_monitoring`, its sub-modules included, and the canvas of
the drawing's template), docker compose (`Makefile`,
`docker-compose.yml`), tmux (`Makefile`), `urllib` (`module_monitoring/serve.py`,
`module_monitoring/sub_module_devops/config.py` and both downloaders), the `git`
command line over `subprocess` (`sub_module_dx/visualise.py`) and a stage's
command line over `subprocess` (`record.py`), `http.server` (`module_monitoring/serve.py` and the panel's own),
cgroup v2 and procfs (`module_monitoring/serve.py`), `socket` and the Docker Engine API over its
unix socket (`module_monitoring/sub_module_devops/`), and the file listing of the four pipeline stores
(`record.py`). A
boundary is an exception the conventions name, not an inconsistency they
tolerate.

### Sorting and the timeframe slots

A listing is read by eye, so a name is built to sort. Three rules give the
grammar, and the slot standard follows from them:

- **digits sort before letters** in every collation a terminal, an editor or a
  file manager uses, so a numeric field placed left of a letter field orders the
  listing by that number;
- **every number is zero-padded** to the width of its field, or `10` sorts
  before `2`;
- **the field width is fixed**, so the columns of a listing line up and the eye
  compares them without reading.

The timeframe of an artifact is therefore written as five fixed slots, finest
first, and only the active one carries digits:

| slot | unit | a 15m artifact | a 1h artifact | a 4h artifact |
|---|---|---|---|---|
| `ss` | seconds | `ss` | `ss` | `ss` |
| `mm` | minutes | `15` | `mm` | `mm` |
| `hh` | hours | `hh` | `01` | `04` |
| `dd` | days | `dd` | `dd` | `dd` |
| `MM` | months | `MM` | `MM` | `MM` |

`BTC_features_ss-15-hh-dd-MM.parquet`, `BTC_features_ss-mm-01-dd-MM.parquet`,
`BTC_features_ss-mm-04-dd-MM.parquet` — three siblings a plain `ls` orders from
the finest granularity to the coarsest, which `15m`, `1h`, `4h` would not.

**Two patterns, two jobs.** The slots name files on a filesystem; the compact
token — `1m`, `15m`, `1h`, `4h` — names timeframes inside code, schemas and
payload keys, where nothing sorts and the short form reads better. That is why
the raw store is `store_raw_1m/` and not a slot string: a store names its
granularity, it does not order siblings by it.

### The feature grammar

Every column of X is read off its own name; nothing but the catalogue record is
needed to decode one:

```
feature     = definition "_" timeframe
definition  = [normaliser "_"] term {"_" operator "_" term}
term        = series | [series "_"] indicator parameter
operator    = "minus" | "over"
normaliser  = "centered"
```

- **the parameter is glued to the indicator token** — `ema20`, `rsi14`,
  `atr14`, `sma200` — never `rsi_14`, which would read as two terms;
- **the series prefix appears only when it is not the default** —
  `log_volume_zscore50`, but a bare `rsi14`, because an indicator on the close
  needs no prefix;
- **`minus` is a difference and `over` a ratio**, and `over` yields `0.0` where
  the denominator is zero — a fact of the arithmetic, not a fallback;
- **`centered` maps a bounded indicator to its own midpoint**, `(x − mid) / half`,
  so a centred RSI runs from −1 to 1;
- **the suffix is the timeframe of every term in the definition.** A name says
  nothing about the decision grid, the alignment or the label horizon, because
  those belong to the run and not to the column.

So `ema20_minus_ema50_over_atr14_4h` is the 4h distance between two exponential
moving averages, expressed in 4h true ranges, and `centered_rsi14_1h` the 1h
relative-strength index about its midpoint. The register of indicators, each
with its parameter word, its warm-up multiple and its output range, is
`INDICATORS` in `module_features/indicators.py` — one record beside each kernel,
and the one place an indicator's invariants live.

### The naming review

Before an object is committed, six questions place it. They are answered in the
head, not in a file:

1. **What is it?** A quantity, a descriptor, an action, a population, a
   constant — the layer decides the grammar.
2. **What does it return, and in what unit?** The unit belongs in the name
   unless the name already says what is counted.
3. **Where does it belong?** Beside the functions that write the same state and
   live as long as it does.
4. **Is the term already used here?** `git grep` it. A name that denotes two
   things in one scope is renamed until it denotes one.
5. **Would a reader who has never seen this project guess right?** If the answer
   needs a document, the name is wrong.
6. **Is this the standard term?** A widely recognised name beats a local
   synonym, always.

**A name gives way to a more derivable one** — but a serialised name is a
contract with the files on disk. An artifact key, a parquet or database column,
a feature: each moves only together with everything that writes, reads and
stores it, in one commit. Parity is measured against those names.

### Minting a convention

A convention is minted at the **third** occurrence, never the first: two
occurrences are a coincidence, three are a family. It is minted only when the
name is derived from its layer's grammar, the rule is written here in one line,
every existing occurrence is renamed to it in the same commit, and the form it
forbids is named beside it. At an external-format or external-library boundary
the external vocabulary wins inside the call that speaks it, and the project's
own names begin at the return value — that is why the Lean raw tree is a
lowercase symbol while the artifact folder is the ticker in capitals.

### The closed list absorbs its synonyms

One verb per job. The synonyms below are not shades of meaning; they are the
same job under another name, and they collapse:

| the verb | absorbs |
|---|---|
| `write_` | `save_`, `publish_`, `persist_`, `store_` |
| `load_` | `read_`, `open_`, `get_` |
| `fetch_` | `download_`, `pull_`, `request_` |
| `build_` | `generate_`, `calculate_`, `compute_`, `aggregate_` |
| `parse_` | `decode_`, `extract_` |
| `fit` | `train_` |
| — | `process`, `handle`, `run`, `execute`, `manage`: these name no job at all |

`evaluate_` is not a verb here either: it becomes the noun the artifact carries,
`<object>_evaluation`. A function that *is* a quantity takes no verb: `rsi`, `atr`,
`sharpe_annualised`. A function that computes never writes — the moment it
persists, the body is split at the store.

## Determinism

The same inputs produce the same bytes, and **bit parity is the proof** — the
standard any change that should not alter results is measured against
(`README.md` § Parity is the procedure).

- **the thread caps are correctness, not settings.** `SET threads=1` at every
  DuckDB connection, `nthread=1` for XGBoost, `OMP_NUM_THREADS=1` in every
  service: float summation must not be reordered, and a reordered sum changes
  the last bits. They are never raised to go faster;
- **`SEED = 42`**, and Optuna runs sequentially with a seeded sampler, so the
  same search visits the same trials in the same order;
- **DuckDB orders are pinned** — `arg_min` / `arg_max` over an explicit
  `ORDER BY`, never an implicit row order — and every writer sorts before it
  writes, JSON with sorted keys;
- **speed comes from outside a stage, never from inside it.** `JOBS` is measured
  at invocation from cores and available memory, one process per asset, and is
  never hardcoded. `data-ingest` stays sequential because the memory ceiling is
  per process.

## Comments

Comments are the only prose beside these two documents, so each one earns its
place. A comment says the **why** that the code cannot: the invariant a line
protects, the reason a constant has that value, the counterpart a copy must
change with. It states its rule outright and never points at a document to carry
it. What a comment is never: a restatement of what the line already says, a
paraphrase of a rule written here, a debt marker — `TODO`, `FIXME`, `XXX`,
`HACK` are a postponed decision, and a postponed decision is not committed — or
a line of code left commented out, which is a version git already holds.

## Rejected vocabulary

The rejected vocabulary stays as a list of words that steers the repository
toward a lower level of vectors, guiding AI agents toward useful embeddings for
solving problems in a concrete and minimally correct way. No check stands
behind it. The last column of the grammar table holds the forms bound to one
rule and the register's `never` columns the synonyms bound to one concept; this
list gathers the words bound to neither, and repeats the few the register
already binds that are worth steering away from on sight.

- **directories and path segments** (the drawing's node type `core` is neither: it is a
  value in `sub_module_dx/visualisation_config.json`)**:** `src`, `core`, `lib`, `common`, `utils`,
  `helpers`, `manager`, `service`, `assets`, `artifacts`, `data`, `db`,
  `database`, `raw_data`, a lowercase ticker folder, a venue symbol as a folder;
  `repository_module_<domain>`, a numbered package directory,
  renumbered
- **module and file stems:** `module_compose`, `module_docker`,
  `module_capsule`, `module_asset`, `module_viz`; `dashboard.py`, `proxy.py`,
  `server.py` beside `serve.py`; a strategy file per asset, a parameters file
  per stage, an `export` stage, a per-asset OHLCV parquet; a module named for
  a cloud resource (`module_s3`, `module_ecs`, `module_eventbridge`); `worker`,
  `processor`; `common`, `shared`, `lib` as a repository or a package for what
  two modules share
- **function verbs:** `read_`, `probe_`, `spool_`, `iter_`, `run_`, `compute_`,
  `_factory`; in JavaScript `load`, `poll`. The stem is rejected as a **verb**: a
  function named for a domain noun the register carries is not one, which is why
  `run_dir()` and `run_payload()` stand — a run is the object `record.py` writes —
  and why `write_venue_spool()` stands, its verb being `write` and its spool the CSV
  it names
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
  which publishes no port, as `docker-compose.yml` shows; `8900` as the
  page's address in a document, a command or a comment — the host port is measured, the
  page's address the one `make on` prints. `CONTAINER_PORT` is a different fact and may be written as itself: the
  port every service listens on inside its own namespace, and the left-hand side of a
  reader's own forward; `TODO`, `FIXME`,
  `XXX`, `HACK`; test suite, linter, coverage gate, CI, workflow, hook,
  generator, framework; `authority`, `single source of truth`; `one-shot` for a
  one-off — an external API's own parameter spelling is that API's, not ours
  (§ Canonical vocabulary, the external-vocabulary boundary); `cloud-ready`, `AWS-ready`, `cloud-native`; `s3://` in a path
  constant, an adapter for a cloud that is not there; a second compose file, a
  second Makefile, a hand-edited derived artifact

## The default choice

For every new change, prefer **the smallest, most modular and most obvious
implementation that correctly closes the full pipeline.**

**A rule about code lives in the comment beside that code; a rule about the
project lives here. There is no third place.** Each is written exactly once, and
there is no second copy to drift. A comment states its rule outright — it never
points at a document to carry it, and the only documents it could point at are
these two.

A **sub-module** is the one boundary in this shape: `sub_module_<domain>/` inside
the owner of its subject, with its own `config.py`, its own `main()` and no
dataflow of its own. It exists twice. The DevOps panel is
`module_monitoring/sub_module_devops/`, nested rather than promoted because the
dashboard serves its own directory — a top-level module would have to be given a
route, and the page reaches the browser as a static file instead; the panel adds
one route for its API alone, because an API is not a file, and the socket it holds
is the reason it is a service of its own rather than a role of `serve.py`. The
developer-experience drawing is `sub_module_dx/` at the repository root, because
its subject is the whole tracked tree and no module owns that; the dashboard
serves its page as a static file through the read-only bind mount
`docker-compose.yml` seats below its web root, so the drawing costs no route
either and `module_monitoring` holds no code of it. `sub_module_*` does not enter
the directory grammar above: two occurrences are a coincidence, and the third one
mints it or nothing does.

## The shape — what holds the project together

The shape is four modules and a launcher: one image, the stores explicit and
outside compute, the orchestration outside the modules, the contracts between
modules as files, the asset as a parameter, the recorder measuring what a stage
wrote — and nothing of a cloud. The conditions below hold at every commit; a change that breaks one
is wrong.

| # | holds |
|---|---|
| D01 | the root holds no data, feature or ML logic: its only Python is `record.py` and `sub_module_dx/`, both describing the assembled project |
| D02 | `git grep "from module_"` inside a module package finds only that package: no module imports another |
| D04 | a fresh `git clone` followed by `make all` and `make on` is a working project |
| D05 | one `docker-compose.yml` carries the whole topology, and one `Makefile` the stage order and the fan-out |
| D06 | no module writes into another's source tree: what a stage writes lands in a store |
| D07 | an asset is `ASSET` on the make line and `--tickers` at the process boundary — never an image or a service definition of its own |
| D08 | neither the drawing nor the panel is a module: `sub_module_dx/` is the launcher's, `module_monitoring/sub_module_devops/` the monitoring module's |
| D09 | a payload key and the identifier that produced it carry one name, and a key added, dropped or renamed moves every reader of it in the same commit — the feature layer's contract file `<TICKER>_catalogue.json`, the `catalogue` block of `features_status.json` beside `assets[].row_count_by_timeframe`, and the `ticker` key in every row of `data_status.json` |
| D10 | determinism is unchanged: the caps, the seed, the pinned orders (§ Determinism) |
| D11 | parity: the chain on the frozen raw store reproduces the nine BTC artifacts and the three normalised snapshots byte for byte against the reference list `README.md` § Parity names. A change that reshapes a snapshot re-bases that snapshot's line and no other — the gate is then a field-level before/after comparison, every kept field byte-identical, beside the lines held fixed |
| D12 | zero cloud mechanisms: nothing in the tree reaches a service off this host, and `mlflow` writes a tracking URI built in `module_ml/config.py` under `STORE_TRIALS_DIR`, never a network location; the five pins of `requirements.txt` are the project's, and a sixth moves this line in the commit that adds it |
| D13 | `features_status.json` is written by `module_features.status` |
| D14 | every copy carried by extraction is marked `# twice by extraction` where it is defined, names its counterparts in that same comment, and is changed on every side at once |
| D15 | the tracked remnant of the artifacts store — `<TICKER>_README.md`, `<TICKER>_parameters.json` and, once promoted, `<TICKER>_feature_set.json` — and the three snapshots are tracked, so a fresh clone opens on real numbers |
| D16 | the fan-out and the detached search run through `docker compose run --rm`; nothing is `exec`'d into a resident |
