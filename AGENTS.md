# AGENTS — the contract of the project

The governing contract for every change, human or agent, in each of the five
repositories of LIORA: the four module repositories and the Orchestration
repository that pins them as submodules and runs them. This file is written
once, in `LIORA-MLOps-Portfolio-Orchestration`, and travels into every module
repository as a read-only copy stamped by `module_skills/distributed_from.md`
(§ The default choice); wherever you read it, the source is the Orchestration
repository. Read the project in this order: **AGENTS.md → module names →
`README_module_<name>.md` → the module's own `skills/` → code**, with
`module_skills/` beside them for the rules that cross modules, indexed by
`module_skills/README.md`. (A `README.md` is general information, not part of
the working path.) If a change conflicts with this file, the change is wrong.

## Values

- **Destination, not road.** *The repository shows the destination, not the road*. No tests, no security
  layers, no CI, no precautionary guardrails; the only guards are the ones the
  mathematics requires, and a stage proves itself by running.
- **Minimalism.** Every line, file, module and dependency has a concrete
  purpose. If its purpose cannot be named, it goes.
- **Minimum requirements.** Python 3.12.x with `venv` and `pip`; the container
  is `python:3.12-slim`, one image per module repository. A library is added
  only when the standard library and the current stack — `duckdb`, `numpy`,
  `optuna`, `xgboost-cpu` — cannot do the job. Each module repository's
  `requirements.txt` declares its own direct dependencies only, pinned to the
  versions the other three pin.
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
generated state; a repository is one of the five the project is made of. Four
module repositories — one Python package `module_<domain>` each, in the order
the data moves through them — and the Orchestration repository, which carries
no dataflow:

```
LIORA-MLOps-Portfolio-module-data        module_data/        sources → normalised raw 1m → one canonical DuckDB per asset
LIORA-MLOps-Portfolio-module-features    module_features/    canonical DuckDB → the bars of the register → the feature catalogue, one parquet per timeframe, the per-asset contract and its snapshot
LIORA-MLOps-Portfolio-module-ml          module_ml/          the catalogue and the canonical path → X, Y → search → model → research simulation
LIORA-MLOps-Portfolio-module-monitoring  module_monitoring/  presentation of what the three computational modules measured about themselves and of what record.py measured around every stage, and the server that serves it — in an asset container, the container reporting itself
LIORA-MLOps-Portfolio-Orchestration      the workspace       the Makefile and docker-compose.yml that run the four, record.py, the developer-experience drawing (sub_module_dx/), the four stores, and the canon: this contract, the name register (module_skills/glossary.md), the cross-cutting skills and the index of every module's own
```

A module repository holds its package at its root — `module_<domain>/`, the
package unchanged — beside its own `Dockerfile`, `requirements.txt`, `Makefile`
(a venv, for the module alone), `README.md`, and the copies of the canon. The
Orchestration repository pins the four as git submodules, checked out as
`901-module_data/`, `902-module_features/`, `903-module_ml/`,
`904-module_monitoring/`; a clone of Orchestration with `--recurse-submodules` is
the workspace, and `make all` in it runs the chain. A path written
`module_<domain>/…` in this contract or in a skill names the package wherever it
is checked out — at the root of its own repository, and under
`<9NN>-module_<domain>/` in the workspace — so the same sentence is true in the
canon and in every copy; a hyperlink from one repository into another is an
absolute GitHub URL, carried by the index `module_skills/README.md` and, once
per repository, by the Orchestration `README.md` § The repositories — every
other reference is a path in backticks.

`module_skills` never participates in runtime imports or dataflow. **No module
imports another.** What crossed a module boundary as an import in the monorepo
crosses it now as a file in a store — the four `STORE_*_DIR` the launcher names
(`module_skills/glossary.md` § Stores), the per-asset contract
`<TICKER>_catalogue.json` the feature layer writes and every ML stage reads, the
three snapshots each computational module writes about itself and the dashboard
serves, the run record `record.py` writes around every stage — or as a copy
registered in `module_skills/glossary.md` § Twice by extraction, identical to the
byte on every side. The basket is the launcher's: `TICKERS` in the Orchestration
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
workspace), runs standalone against the four stores its `Makefile` is pointed at
(`make setup`, then `make <module>-<stage> ASSET=<TICKER>` in a venv), and knows
nothing of the others: they share the store contract, the files it names and the
copies the register lists, and nothing between them speaks over a network.

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
  `download_bybit.py`, `store_assets_artifacts/<TICKER>/<TICKER>_<artifact>.<ext>`, `ml-<stage>`
  targets); each computational module (`module_data`,
  `module_features`, `module_ml`) measures its own domain state in `status.py`,
  and `module_monitoring` presents their snapshots;
- **taxonomic ordering — the category token comes first, so siblings sort
  together.** A listing is read by eye before it is parsed: in the workspace
  `901-module_data`, `902-module_features`, `903-module_ml`,
  `904-module_monitoring` — the chain in its own order, the number being the
  module's position in the chain at the time it was seated; a new module takes
  the next free number and nothing is ever renumbered — then `module_skills`
  and `sub_module_dx`, then `store_assets_artifacts`, `store_raw_1m`,
  `store_run_records`, `store_status`: blocks, not scattered entries. If
  renaming would put things of one category next to each other, rename them;
- short, predictable paths, built only in a module's `config.py` — never
  assembled at the point of use; the one exception is an external format's own
  file names, built by its adapter (`module_data/lean.py` for the Lean tree,
  `module_monitoring/serve.py` for the cgroup and procfs paths of its boundary,
  `record.py` for the four stores it lists)
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
  variables → `/store/raw_1m`, `/store/run_records`; `MODULE_MONITORING_DIR` →
  `module_monitoring/`;
- one convention per language: BEM in CSS, snake_case in Python and JSON,
  the same hierarchy everywhere, no accidental exceptions.

## Pre-AWS architectural direction

Pre-AWS is this repository's word for its own shape: a local, academic
architecture whose boundaries would still be the right boundaries after local
storage, local container execution and local stage order were replaced by their
standard equivalents on Amazon Web Services (AWS). No cloud is used and none is
planned; the mapping is described in `module_skills/skill_pre_aws_solution.md`
and built nowhere.

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
  asset is one line in the Orchestration `Makefile`'s `TICKERS` and one
  `asset-<ticker>` block in its `docker-compose.yml`, and nothing in any module.
- **Compute owns no state.** A stage reads a store, writes a store and exits; it
  holds nothing between invocations, binds no port, reads no `ASSET` and assumes
  no resident peer.
- **Storage is separate from compute.** Pipeline state lives in the four stores
  — the `store_*` roots of the workspace, mounted into every container as
  `/store/<content>` and named to every `config.py` by its `STORE_*_DIR` — never
  inside a container and never inside a repository's tree; each image carries
  its module's code and nothing of the state, the mounts carry the state and
  nothing of the code, and the three snapshots are the one store that is tracked.
- **Modules are built by ownership and lifetime.** A function sits beside the
  functions that write the same state and live as long as it does, never beside
  what happened to be written with it; every object is classified before it is
  placed.
- **Every placement is argued, and the mapping is the test.** For every object
  a module holds, its `README_module_<name>.md` § Design rationale writes down,
  in one row, the answers of `module_skills/skill_self_explaining_naming.md`
  § The naming review that place it — why here, why beside these, why this
  boundary — and which row of the mapping table it answers to, the fourth being
  the test of the first three. An object one of whose responsibilities answers
  to no row, or to two, is questioned before it is committed; a file that holds
  several responsibilities — a descriptor per store, a role per `ASSET` —
  answers with one row each, and says so. The rows are
  `module_skills/skill_pre_aws_solution.md` § The mapping table.
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
*Pre-AWS* — `module_skills/glossary.md` § Pre-AWS direction, and the `pre_aws`
file stem it registers, the skill's and the report's — they are spoken only
where the stance is stated, reviewed or a local object is seated: this section
and § Skills absent here, described, the Orchestration `README.md` § Architectural direction, the
skill's prose, the column *the same responsibility elsewhere* of its mapping
table, `REPORT_pre_aws_minimalism.md` — the seats reviewed for excess — and the
one picture of that column — the deployment view of the developer-experience drawing, the
`deployment` block of
`sub_module_dx/visualisation_config.json` and the page drawn
from it, whose every primitive drawn is a row of the table and which names no
primitive the table does not — together with the UI-label column of
`module_skills/glossary.md` § Developer experience, which records the words that
view shows; and, at the edge of a local rule, the one seat paragraph of
`module_skills/skill_asset_containers.md`, `module_skills/skill_determinism.md`
(its last bullet, the skill having no headings),
`module_data/skills/skill_candle_canonicalisation.md` § 15 and
`module_monitoring/skills/skill_devops_panel.md`, each naming the primitive in
the table's words and citing the skill for the rest. Never in a make target, a
compose service, an environment variable, a payload key, a code comment, an
identifier, or a tracked path but the `pre_aws` stem. The non-goals, the twelve
classes, the review of what stays local and the mapping table are
`module_skills/skill_pre_aws_solution.md` — a cross-cutting skill of the kind
§ The default choice names, beside `skill_asset_containers.md`.

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
config and never hand-edited: `<TICKER>_parameters.json`,
`<TICKER>_feature_set_search.json`, `<TICKER>_README.md`, `<TICKER>_catalogue.json`,
the three snapshots, the developer-experience drawing
(`sub_module_dx/files_and_folders_visualisation.html`) and, in a module
repository, the copies of this contract and of `module_skills/` with their stamp
`module_skills/distributed_from.md`, written by `make skills-distribute` alone. A
hand edit to one is a violation.

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
| features | `[<normaliser>_]<term>{_<operator>_<term>}_<timeframe>`, a term `[<series>_]<indicator><parameter>` or a bare series, read off the catalogue record — the rest is `module_features/skills/skill_feature_taxonomy.md` | `ema20_minus_ema50_over_atr14_4h`, `centered_rsi14_1h`, `range_position20_15m`, `close_minus_sma200_over_atr14_4h` | `feature_3`, `f_rsi`, `rsi_14`, `sma_200`, `trend_4h` |
| stored columns | the quantity for OHLCV, `<what>_<unit>` for anything derived, `<subject>_<predicate>` for a boolean — and a column and the key that publishes it carry **one** name | `timestamp_ms`, `ffill_bars`, `zero_volume_bars`, `binance_valid` | `n_ffill`, a column and key that disagree |
| Makefile targets | in Orchestration, `<module>-<stage>` for a stage of a runtime module — run in a one-off container of that module's runner — and `<module>-all` for its chain; `tmux-<module>-<stage>` for the detached twin of a stage that outlives the terminal — only a stage that resumes may have one; only the lifecycle targets and the repository's own tools go bare (`all`, `build`, `help`, `on`, `off`, `all-record`, `dx-update`, `skills-status`, `skills-distribute`), `on` / `off` being the presentation switch, and a ticker alias of a lifecycle target carries its own sunset note; in a module repository, the same `<module>-<stage>` grammar for its own stages, run in its venv with `ASSET=<TICKER>` — by `python3` where the module has no dependency — beside `setup` and `help` | `data-ingest`, `ml-hpo`, `features-all`, `tmux-ml-feature-set-search`, `on` | a bare stage (`ingest`), a `docker-` twin of a stage (there is one way to run a stage), a target named after the tool (`docker-run`), a detached twin of a stage that cannot resume, a second switch pair (`start` / `stop`, `up` / `down`), a `docker`, `compose` or `tmux` word in a module repository's Makefile |
| directories | `<category>_<detail>/`; a raw store names its granularity with the compact timeframe token, `store_raw_<timeframe>/`; in the workspace a module repository is checked out as `<9NN>-module_<domain>/`, the number the module's position in the chain at the time it was seated — a new module takes the next free number and nothing is ever renumbered | `module_*`, `store_*`, `store_raw_1m`, `901-module_data` … `904-module_monitoring` | a kind scattered through the alphabet, a store spelling its timeframe in sorting slots, a renumbered checkout, `repository_module_<domain>/` |
| repositories | `LIORA-MLOps-Portfolio-<Role>`, the role `Orchestration` or `module-<domain>` — the same `module` + `<domain>` tokens as the package and the checkout, the separator the scope's own | `LIORA-MLOps-Portfolio-Orchestration`, `LIORA-MLOps-Portfolio-module-data` … `LIORA-MLOps-Portfolio-module-monitoring` | a ticker in a repository name; `common`, `shared`, `lib`; a repository per asset; a number in a GitHub name |
| images | `liora-module-<domain>`, one per module repository, built from its `Dockerfile` alone | `liora-module-data`, `liora-module-features`, `liora-module-ml`, `liora-module-monitoring` | compose's `<project>-<service>` default, an image per service, an image per asset, one image for every module |
| compose services | a runtime role, never an image or a ticker in code — the runners `data`, `features`, `ml`, the residents `dashboard`, `asset-<ticker>`, `devops` | `ml`, `asset-btc` | `pipeline`, a service named for an image or a tool, a service per asset stage |
| store paths | `store_<content>/` on the host, `/store/<content>` inside a container, `STORE_<CONTENT>_DIR` the variable that names the one to the other | `store_raw_1m/`, `/store/raw_1m`, `STORE_RAW_1M_DIR` | a path derived from `__file__`, `/app/store_*` as an address, a store literal at the point of use |
| the distribution stamp | `module_skills/distributed_from.md`, one line — `LIORA-MLOps-Portfolio-Orchestration@<commit> — read-only copies; edit at the source` — written by `make skills-distribute` | — | a version number, a date, a hand-written stamp, an edited copy |
| a module's own skills | `module_<name>/skills/`, in the module's own repository, holding every rule about that module and nothing else | `module_data/skills/`, `module_features/skills/`, `module_ml/skills/`, `module_monitoring/skills/` | a single module's rule kept in `module_skills/`; a second copy of one rule in both; a module's rule in the Orchestration repository |
| a module's orientation | `README_module_<name>.md`, the name derived from the module directory it sits in | `module_data/README_module_data.md`, `module_features/README_module_features.md`, `module_ml/README_module_ml.md`, `module_monitoring/README_module_monitoring.md` | `module_data/README.md`; an orientation file that restates a skill |
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
(`module_ml/model.py`, `module_ml/hpo.py`), numpy (every module that computes),
argparse (`module_data/config.py`, `module_data/status.py`,
`module_ml/feature_set_promote.py`, `sub_module_dx/visualise.py`), DuckDB SQL (every module that queries), the SVG
and DOM attributes (every `*.js` of `module_monitoring`, its sub-modules included, and the canvas of
the drawing's template), docker compose (`Makefile`,
`docker-compose.yml`), tmux (`Makefile`), `urllib` (`module_monitoring/serve.py`,
`module_monitoring/sub_module_devops/config.py` and both downloaders), the `git`
command line over `subprocess` (`sub_module_dx/visualise.py`) and a stage's
command line over `subprocess` (`record.py`), `http.server` (`module_monitoring/serve.py` and the panel's own),
cgroup v2 and procfs (`module_monitoring/serve.py`), `socket` and the Docker Engine API over its
unix socket (`module_monitoring/sub_module_devops/`), and the file listing of the four stores
(`record.py`). A
boundary is an exception the conventions name, not an inconsistency they
tolerate.

## Rejected vocabulary

The rejected vocabulary stays as a list of words that steers the repository
toward a lower level of vectors, guiding AI agents toward useful embeddings for
solving problems in a concrete and minimally correct way. No check stands
behind it. The last column of the grammar table holds the forms bound to one
rule and the register's `never` columns the synonyms bound to one concept; this
list gathers the words bound to neither, and repeats the few the register
already binds that are worth steering away from on sight.

- **directories and path segments:** `src`, `core`, `lib`, `common`, `utils`,
  `helpers`, `manager`, `service`, `assets`, `artifacts`, `data`, `db`,
  `database`, `raw_data`, a lowercase ticker folder, a venue symbol as a folder;
  `repository_module_<domain>`, `submodule_`, a `<9NN>` number reused or
  renumbered
- **module and file stems:** `module_compose`, `module_docker`,
  `module_capsule`, `module_asset`, `module_viz`; `dashboard.py`, `proxy.py`,
  `server.py` beside `serve.py`; a strategy file per asset, a parameters file
  per stage, an `export` stage, a per-asset OHLCV parquet; a module named for
  a cloud resource (`module_s3`, `module_ecs`, `module_eventbridge`); `worker`,
  `processor`; `common`, `shared`, `lib` as a repository or a package for what
  two modules share
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
  which publishes no port (`module_skills/skill_asset_containers.md`); `8900` as the
  page's address in a document, a command or a comment — the host port is measured, the
  page's address the one `make on` prints (`module_skills/skill_asset_containers.md`
  § The topology); `TODO`, `FIXME`,
  `XXX`, `HACK`; test suite, linter, coverage gate, CI, workflow, hook,
  generator, framework; `authority`, `single source of truth`; `one-shot` for a
  one-off; `cloud-ready`, `AWS-ready`, `cloud-native`; `s3://` in a path
  constant, an adapter for a cloud that is not there; a `docker` or `compose`
  word in a module repository's Makefile, a compose file in a module
  repository, a hand-edited copy of the canon, a submodule on a detached HEAD

## The default choice

For every new change, prefer **the smallest, most modular and most obvious
implementation that correctly closes the full pipeline.**

**A skill belongs to the module whose responsibility it describes.** A rule
about one module lives in `module_<name>/skills/`, in that module's repository;
a rule that crosses modules or governs the project lives in `module_skills/` of
the Orchestration repository — the canon; a module's orientation is its
`README_module_<name>.md`. Each is written exactly once, the location follows
ownership, and there is no second copy to drift — with one named exception: the
canon is **distributed**. Every module repository carries a read-only copy of
this contract and of `module_skills/`, so that a module repository read alone
still carries the rules it answers to; the copy is stamped by
`module_skills/distributed_from.md` with the Orchestration commit it was taken
from, `make skills-status` in the workspace reports any copy that differs from
the canon, `make skills-distribute` overwrites every copy from the canon and
rewrites the stamp, and a copy is never edited by hand — a change to a rule is
made at the source, distributed, committed in each module repository as *Take
the distributed rules from LIORA-MLOps-Portfolio-Orchestration@<commit>*, and
pinned. `module_skills/README.md` is the index — it links to every skill,
cross-cutting and module-owned alike, the module-owned ones by absolute GitHub
URL, and restates none of them.

`module_skills/skill_asset_containers.md` is the worked example of the cross-cutting
boundary: four images, the three runner services and `asset-<ticker>`, the Makefile
fan-out, the ceilings and the store mounts are a contract between the
infrastructure and all four runtime modules at once, so it belongs to none of
them and stays in the canon.

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

## The split — what holds five repositories together

The project was one repository, `LIORA-MLOps-Portfolio`, until the tag
`monorepo-split-ready`; its `main` ends with the boundary refactor the split was
cut from and a README banner naming Orchestration as its successor, and the tag
`monorepo-baseline` marks the tree whose nine BTC artifacts every later commit
reproduces byte for byte. What the split added is exactly this — an image per
module, the stores explicit and outside compute, the orchestration outside the
modules, the contracts between modules as files, the asset as a parameter, the
recorder measuring what a stage wrote — and nothing of a cloud
(`module_skills/skill_pre_aws_solution.md` § What the split added, and what it
did not). The conditions below hold at every commit of Orchestration; a change
that breaks one is wrong.

| # | holds |
|---|---|
| D01 | Orchestration holds no data, feature or ML logic: its only Python is `record.py` and `sub_module_dx/`, both describing the assembled project |
| D02 | each module repository carries its own `Dockerfile` |
| D03 | each module repository carries its own `requirements.txt` — its direct dependencies only, pinned to the versions the other three pin |
| D04 | each image builds from its repository alone, outside any workspace |
| D05 | `git grep "from module_"` in a module repository finds only its own package |
| D06 | a module's skills live in that module's repository and nowhere else |
| D07 | the cross-cutting canon — this contract and `module_skills/` — is written only in Orchestration |
| D08 | every copy of the canon is stamped by `module_skills/distributed_from.md` naming an Orchestration commit |
| D09 | `make skills-status` reports a copy that differs from the canon, and is silent when none does |
| D10 | `make skills-distribute` overwrites every copy from the canon; nothing else writes one |
| D11 | the four gitlinks are pinned: `git submodule status` shows no `+`, `-` or `U` |
| D12 | a fresh `git clone --recurse-submodules` followed by `make all` and `make on` is a working project |
| D13 | one `docker-compose.yml`, Orchestration's, carries the whole topology; no module repository has one |
| D14 | one `Makefile`, Orchestration's, carries the stage order and the fan-out; a module repository's Makefile names no docker, compose or tmux |
| D15 | no module writes into another's source tree: what a stage writes lands in a store |
| D16 | an asset is `ASSET` on the make line and `--tickers` at the process boundary — never a repository, an image or a service definition of its own |
| D17 | neither the drawing nor the panel is a repository: `sub_module_dx/` is Orchestration's, `module_monitoring/sub_module_devops/` the monitoring module's |
| D18 | artifact names and keys are the monorepo's, with the registered exceptions: `<TICKER>_catalogue.json`, the one new file; the `catalogue` block, moved whole from `ml_status.json` to `features_status.json`, beside the one new key `assets[].row_count_by_timeframe`; the `ticker` key in every row of `data_status.json` |
| D19 | determinism is unchanged: the caps, the seed, the pinned orders (`module_skills/skill_determinism.md`) |
| D20 | parity: the chain on the frozen raw store reproduces the nine BTC artifacts and the three normalised snapshots byte for byte (the Orchestration `README.md` § Parity) |
| D21 | zero cloud mechanisms and zero new dependencies: the four pins are the monorepo's |
| D22 | `features_status.json` is written by `module_features.status` |
| D23 | every module repository's `README.md` carries the rows of `module_skills/glossary.md` § Twice by extraction that name it |
| D24 | the old repository carries the tags `monorepo-baseline` and `monorepo-split-ready` |
| D25 | the tracked remnant of the artifacts store — `<TICKER>_README.md`, `<TICKER>_parameters.json` and, once promoted, `<TICKER>_feature_set.json` — and the three snapshots are tracked in Orchestration |
| D26 | the fan-out and the detached search run through `docker compose run --rm`; nothing is `exec`'d into a resident |
| D27 | the old repository's `README.md` opens with the banner naming Orchestration as its successor |

## Skills absent here, described

Skills the Pre-AWS seats imply and this tree does not hold: each placed by
ownership as § The default choice places every skill, described today where its
last column says, and written when its one condition holds. Two rows the split
answered are no longer here: the status prefix — the three snapshots live in
`store_status/`, the one tracked store (`module_skills/glossary.md` § Stores) —
and the image contents — each module repository's `Dockerfile` copies its
package, and the mounts carry the four stores — and, on `dashboard`, the drawing
read-only (`module_skills/skill_asset_containers.md` § The topology).

| skill | owner | governs | written when | described today in |
|---|---|---|---|---|
| `skill_task_host_volume.md` | `module_skills/` | the one Linux host every asset's runs share and the volume mounted where the four `./store_<content>` mounts are today — every asset's folder and the other `store_*` roots at the same `/store/<content>` paths, and what a task may leave on it | the first run whose `store_*` roots sit on a volume that is not the workspace's disk | `module_skills/skill_pre_aws_solution.md` § The volume is the home, the store is the copy; `module_skills/skill_asset_containers.md` § The topology |
| `skill_object_storage_layout.md` | `module_skills/` | the prefixes of the copy — `raw/<venue>/<symbol>/<day>` written once, `artifacts/<ticker>/<version>/`, `runs/<run_id>/`, `status/` — and the one discipline: a whole file copied after the last stage of a run has exited, never a path a stage writes | the first whole file copied off the host | `module_skills/skill_pre_aws_solution.md` § The volume is the home, the store is the copy; `module_skills/skill_pre_aws_solution.md` § The asset folder is a prefix, read forward |
| `skill_stage_state_machine.md` | `module_skills/` | one state per stage in the order of `all:`, `data-all:`, `features-all:` and `ml-all:`, a Map over `TICKERS` whose width is `JOBS`, the execution named by `run_id`, the whole-file copy as the state after the last stage, and the schedule that starts it | the first stage launched by something other than `make` | `module_skills/skill_pre_aws_solution.md` § The Makefile is the developer interface; `module_skills/skill_pre_aws_solution.md` § The retrain runtime is a ladder |
| `skill_rebuild_condition.md` | `module_skills/` | the four `has_` / `requires_` predicates — read-only, per asset, in the module that owns what they compare — and the condition state that reads them; never a function that both detects and trains | the first freshness predicate is written, `has_new_market_data(ticker)` in `module_data` | `module_skills/skill_pre_aws_solution.md` § The rebuild condition stays separable; `module_skills/glossary.md` § Pre-AWS direction |
| `skill_artifact_versioning.md` | `module_skills/` | `<version>` = `run_id` under the asset prefix, which version is the active one and how a reader resolves it; no version inside an artifact | the second version of one asset's artifacts exists off the host | `module_skills/skill_pre_aws_solution.md` § Correlatable artifacts, without a version scheme; `module_ml/skills/methodology_ml.md` § 10 |
| `skill_dashboard_front.md` | `module_monitoring/skills/` | the page files and the three snapshots as static objects behind a content-delivery front, the registry, run and proxy routes staying a reader process; until then the tunnel of the Orchestration `README.md` § Quickstart | the first reader the tunnel does not serve | `module_skills/skill_pre_aws_solution.md` § The mapping table, the static dashboard and reader rows; `module_skills/skill_pre_aws_solution.md` § What stays as it is, and why, the `module_monitoring/` row |
| `skill_strategy_execution.md` | `module_trading/skills/` | `module_trading/` — its own repository, `LIORA-MLOps-Portfolio-module-trading`, seated in the workspace as the next free `<9NN>-module_trading/` with its own image and container beside `module_ml`, reading the Lean-exact raw tree and the asset artifacts from the copy, its brokerage credentials read once at start from a secrets store | that repository is created — the first strategy that consumes an artifact | `module_skills/skill_pre_aws_solution.md` § Module boundaries are extraction boundaries; `module_skills/skill_pre_aws_solution.md` § Every object is classified before it is placed, STRATEGY EXECUTION; `module_skills/skill_pre_aws_solution.md` § The mapping table, the two STRATEGY EXECUTION rows |
| `skill_per_asset_status.md` | `module_skills/` | one status object per asset, written by that asset's own status run, and the fold the reader does over them — never a lock, never a basket-wide writer fanned out | a status stage is fanned out for the first time | `module_skills/skill_pre_aws_solution.md` § The resident container is a local mechanism; `module_skills/skill_pre_aws_solution.md` § What stays as it is, and why, the `module_data.status` row |
| `skill_database_promotion.md` | `module_data/skills/` | the threshold past which an asset's embedded file becomes a managed database — a second concurrent writer, or a query across assets | the first writer or query one embedded file cannot serve | `module_data/skills/skill_candle_canonicalisation.md` § 13, § 15; `module_skills/skill_pre_aws_solution.md` § The databases |
