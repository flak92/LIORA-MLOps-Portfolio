# AGENTS — the contract of this repository

The governing contract for every change, human or agent. Read the project in this order: **AGENTS.md → module
names → `README_module_<name>.md` → the module's own `skills/` → code**, with `module_skills/` beside them for the
rules that cross modules, indexed by `module_skills/README.md`; `README.md` is general information, not part of the
working path. Every rule is a row of `module_skills/skills_sheet.xlsx`, rendered by `make skills-sync` beside what it
governs and cited by its `rule_id` (`FILES-AND-FOLDERS-SHEET-IS-THE-SOURCE`, `FILES-AND-FOLDERS-SKILL-IS-RENDERED`);
this file holds the values and the shape the rows serve. If a change conflicts with this file, the change is wrong.

## Values

- **Destination, not road.** *The repository shows the destination, not the road*: no tests, no security layers, no
  CI, no precautionary guardrails, and no history in a document; a stage proves itself by running
  (`AGENT-FIRST-DEVELOPMENT-PROVE-BY-RUNNING`). One crawler stands beside the chain,
  `module_skills/sub_module_scalability_crawler/`: a hand starts it, it reads each controlled file against the Skills
  the files matrix marks for it, and it gates nothing (D17, D18).
- **Minimalism.** Every line, file, module and dependency has a concrete purpose. If its purpose cannot be named, it
  goes.
- **Minimum requirements.** Python 3.12 and one image on `python:3.12-slim`
  (`ASSET-CONTAINERS-THE-IMAGE-CARRIES-THE-PINS-ALONE`). A library is added only when the standard library and the
  stack — `duckdb`, `numpy`, `optuna`, `xgboost-cpu` — cannot do the job, or when it is the field's own instrument for
  a responsibility this project names and the stack's equivalent would be a private reimplementation of it: § Canonical
  vocabulary's preference for an established name, read forward from names to instruments. By that reading the host
  admits `gum`, the terminals' instrument — a binary of the host, no pin. `requirements.txt` declares the direct
  dependencies only, one pinned version each.
- **KISS / YAGNI / DRY / SOLID.** The simplest correct implementation, built for the need that exists, never for a
  hypothetical one. One responsibility per module; repeated logic becomes one function, not three copies.
- **UCAS — Useless Click Avoiding System.** What can be automated is: `make all` runs the whole chain from a fresh
  clone, every stage is idempotent in what it derives — the trial ledgers alone accumulate, until a hand clears them
  (`METHODOLOGY-ML-LEDGER-IS-APPEND-ONLY`) — and the dashboard opens itself.
- **Main = clean working logic.** No test framework, validation framework or precautionary guard. What stays are the
  seven guards the mathematics requires: causality (`indicators.asof_index`); the full canonical grid of the research
  window and a finite, positive true-range mean at every decision, asserted per asset by `labels.load_research_1m` and
  beside it; the aligned decision grids `dataset.build_xy` joins by position, asserted twice — the catalogue's
  partitions with each other, X with Y; a finite catalogue after the warm-up (`catalogue.build_catalogue`); and the
  download that aborts on a short post-listing day, with the listing probe that aborts when a symbol's history starts
  after the window (`CANDLE-CANONICALISATION-A-SHORT-DAY-ABORTS-THE-DOWNLOAD`). Beside them, and no guard: a status
  stage's one line when it has nothing to report, a venue's own error code as it came, and a stage's one-line refusal
  of an input it cannot use. No debt marker in a tracked file and no code inside a comment: a marker is a postponed
  decision, a commented-out line is a version git already holds. Thread caps are correctness, not a setting
  (`DETERMINISM-THREAD-CAPS-FROZEN-AT-ONE`).
- **Research logic over tooling.** External sources, libraries and infrastructure are implementation details; the
  repository exposes the mathematical and causal research pipeline as directly as possible.
- **Source-neutral downstream.** Venue-specific logic ends at ingestion and data-quality provenance. Features, labels,
  validation, modelling and research simulation operate on the canonical research dataset.
- **Academic, not production.** Explicit equations, causal invariants and reproducible transformations over
  production security, orchestration and validation frameworks.
- **Pipeline-first.** The repository exists to close one full chain:

  ```
  market sources → ingest → validation necessary for correctness → canonical dataset
  → features / labels → training / retraining → strategy / results → monitoring
  ```

## Architecture shape

`module_*` is a top-level project responsibility; `store/` is persisted or generated state. Four modules — one Python
package `module_<domain>` each, in the order the data moves through them — and, around them, the launcher that runs
them and carries no dataflow of its own:

```
module_data/         sources → normalised raw 1m → the venue families and the canonical family ohlcv_1m_canonical, one partition per asset
module_features/     the canonical family → the family bars → the family catalogue, one partition per asset and timeframe, the per-asset contract and its snapshot; outside the chain, the serpentine search over an asset's feature set, barrier geometry and hyper-parameter point, and its promotion
module_ml/           the catalogue and the canonical path → X, Y → search → model → research simulation: the families labels, oos_predictions, hpo_trials; outside the chain, the scoring of the serpentine search's questions and the family score_trials
module_monitoring/   presentation of what the three computational modules measured about themselves, of what record.py measured around every stage and of the crawler's snapshot, and the server that serves it
the root             the Makefile and docker-compose.yml that run the four, record.py, the five stores under store/, and the canon: this contract and module_skills/ — the sheet every rule and the register are rendered from, the cross-cutting skills, the index of every module's own, the crawler and the canon's terminal
```

Each module holds its package, its orientation `README_module_<domain>.md` and its own `skills/` under one directory;
nothing above it belongs to one module alone. A reference is a path in backticks, always.

**No module imports another** (D02); `module_skills` takes part in no runtime import and no dataflow of the chain.
What would cross a boundary as an import crosses it as a file in a store — the families, the per-asset contract
`<TICKER>_catalogue.json`, the four snapshots, the run record, the serpentine search's question, answer and the state
a promotion writes — or as a copy registered in `module_skills/skill_glossary.md` § Twice by extraction (D14). The
basket is the launcher's, `TICKERS` in the `Makefile`, and every stage is told its assets by `--tickers`
(`PRE-AWS-SOLUTION-THE-ASSET-IS-A-NAMESPACE`). A new `module_<domain>` needs a responsibility of its own
(`AGENT-FIRST-DEVELOPMENT-NEW-MODULE-THRESHOLD`); until then the owning module is extended, and what two modules share
is a registered copy, never a `common`.

Each `module_*` is an **extracted bounded context**: its domain rules, its orientation and its code sit together
under its own directory, so its meaning is never reconstructed from documentation that stayed elsewhere. It runs
standalone against the `store/<content>/` folders it touches, each named by the launcher, and knows nothing of the
others: they share the store contract, the files it names and the registered copies, and nothing between them speaks
over a network.

Regular, predictable, symmetrical, easy to scan — the structure is recognisable by eye before it is parsed:

- a name is derived from its family's grammar, so analogous objects sort together and a name tells the object's role
  and its place (`SORTING-FILES-NAMING-STANDARD-CATEGORY-TOKEN-LEADS`, § Canonical vocabulary);
- one obvious responsibility per module; no wrappers without logic of their own;
- analogous names for analogous objects — `download_binance.py` ↔ `download_bybit.py`, one `status.py` per
  computational module measuring its own domain, `ml-<stage>` targets;
- a path is built once, by a descriptor of its module's `config.py` (`PRE-AWS-SOLUTION-A-PATH-IS-BUILT-BY-ONE-DESCRIPTOR`);
  one asset is one partition, `ticker=<TICKER>`, its files in `store/assets_artifacts/ticker=<TICKER>/`, one stage
  writing each family with its `schema.json` beside the partitions, DuckDB the engine in memory and no database file
  anywhere. The raw tree spells the symbol in lower case because QuantConnect Lean demands it: a boundary, not an
  inconsistency;
- one convention per language: BEM in CSS, snake_case in Python and JSON, the same hierarchy everywhere.

## Pre-AWS architectural direction

Pre-AWS is this repository's word for its own shape: a local, academic architecture whose boundaries would still be
the right boundaries after local storage, local container execution and local stage order were replaced by their
standard equivalents on Amazon Web Services (AWS). No cloud is used and none is planned; the mapping is described in
`module_skills/skill_pre_aws_solution.md` and `module_skills/README.md` § The Pre-AWS mapping, and built nowhere
(`PRE-AWS-SOLUTION-THE-MAPPING-IS-BUILT-NOWHERE`).

- **Academic, not AWS.** The runtime is local — one image under docker compose, driven by a Makefile — and the goal
  is a correct dataflow with visible responsibilities: a demonstrator, not a deployment.
- **Every boundary decision weighs the future mapping.** Where a function lives, who writes a file, what a stage
  takes as its parameter, how a container is started — each is chosen so the mapping stays a rename, never a redesign.
- **No cloud complexity without an academic need** (`PRE-AWS-SOLUTION-NO-MECHANISM-ONLY-PRODUCTION-NEEDS`).
- **Compute owns no state** (`PRE-AWS-SOLUTION-A-STAGE-READS-A-STORE-WRITES-A-STORE-AND-EXITS`,
  `PRE-AWS-SOLUTION-ONE-OPERATION-WRITES-AT-A-TIME-AND-NOTHING-LOCKS`), and **storage is separate from compute**: the
  five stores under `store/`, mounted into the services that touch them
  (`ASSET-CONTAINERS-A-SERVICE-MOUNTS-ONLY-THE-STORES-IT-TOUCHES`).
- **Modules are built by ownership and lifetime** (`PRE-AWS-SOLUTION-OBJECTS-ARE-GROUPED-BY-WRITER-AND-LIFETIME`), and
  every placement is argued in its orientation's § Design rationale
  (`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`).
- **Names carry the responsibility**, never a cloud resource (`PRE-AWS-SOLUTION-A-NAME-IS-A-CLASS-NEVER-A-MECHANISM`);
  cloud proper nouns stay where the rule seats them (`PRE-AWS-SOLUTION-CLOUD-NOUNS-STAY-IN-THE-MAPPING`).
- **The Makefile is the local developer interface** and never schedules (`PRE-AWS-SOLUTION-THE-MAKEFILE-NEVER-SCHEDULES`);
  **Docker is compute**, a one-off container per stage (`ASSET-CONTAINERS-A-STAGE-RUNS-IN-A-ONE-OFF-CONTAINER-OF-ITS-RUNNER`).
- **A few assets are proof enough.** The whole chain on one asset demonstrates the architecture; scale is
  `ASSET=<TICKER>`, never hundreds of assets.

## Canonical vocabulary

**Names must be self-explanatory before they are project-specific. Prefer established software-engineering
terminology over project-specific synonyms: if a concept already has a widely recognised name, use that name — in
code, in documentation, in the skills and in the interface alike — and do not invent local terminology for a standard
concept. A glossary confirms meaning; it must not be required to decode an obscure name.**

One concept, one name — in the code, the artifacts, the interface, the Makefile, docker compose and the documents;
the register is `module_skills/skill_glossary.md`, and a new name enters it in the commit that introduces it
(`AGENT-FIRST-DEVELOPMENT-NAME-ENTERS-THE-REGISTER`). The word "test" never names a fold. And one name, one concept:
a name that could denote two things in the same scope — make targets, compose services, container environment
variables, tracked paths, Python symbols within a module — is renamed until it denotes one; a name shared across
different scopes is no collision.

**Derived, never drafted.** A derived artifact is generated from source and configuration and never hand-edited:
`<TICKER>_parameters.json`, `<TICKER>_serpentine_search.json` and its ledger, `<TICKER>_README.md`,
`<TICKER>_catalogue.json`, the four snapshots, and every rendered `skill_*.md` with the register. A hand edit to one
is a violation; `make features-serpentine-search-reset` removing the search's files is no edit but the start of
another experiment.

**Drafted, never derived.** A drafted artifact is a hand's decision written down and never computed from another
file: `module_skills/skills_sheet.xlsx`, edited with any spreadsheet program; `<TICKER>_serpentine_search_profile.json`;
and, once promoted, `<TICKER>_feature_set.json`, `<TICKER>_barriers.json` and `<TICKER>_hyperparameter_point.json`.
The profile and the promoted files are each written by one program — the features terminal's draft, or the promotion —
and may equally be edited in the file, because the same decisions write the same bytes. A stage that derives one is a
violation.

**Rule-derived structure over repeated project knowledge.** When a family — assets, venues, timeframes, paths,
artifact files, payload keys, pipeline stages — is governed by one definition, its repeated representations derive
from it rather than copy it: `TICKERS` in the `Makefile` is the one definition the fan-out and every `--tickers`
derive from. The limit binds as hard: no code generator, no metaprogramming, no abstraction layer for a one-off value;
the one rendering the tree holds is `make skills-sync`.

Every layer has a closed grammar, the way CSS has BEM, and a name is derived from it, never invented
(`SELF-EXPLAINING-NAMING-A-NAME-IS-DERIVED-FROM-ITS-LAYER`, `SELF-EXPLAINING-NAMING-ABSORBED-SYNONYMS`):

| layer | grammar | in this repo | what it forbids |
|---|---|---|---|
| constants | `<OBJECT>_<ROLE>_<PARAMETER>_<UNIT>` | `LABEL_BARRIER_TRUE_RANGE_SMOOTHING_PERIOD_BARS` | `BARRIER_N` |
| constant comments | PEP 8's inline comment for one constant, a block comment above several or above one whose value spans lines; the marker `# twice by extraction` explains nothing and stands where D14 places it | `BYBIT_KLINE_REQUEST_LIMIT = 1000   # < 1440 -> …` | a block comment above a one-line constant it alone explains |
| external I/O functions | `<verb>_<object>`, the verb `fetch_` (network), `load_` (storage → memory), `write_` (persist) or `parse_` (bytes → values) | `fetch_klines`, `load_xy`, `write_parquet`, `parse_zip` | `get_`, `process_`, `handle_` |
| conversions | `to_<representation>` | `to_class`, `to_json_safe` | `convert` |
| composite constructors | `build_<object>` | `build_x` | `make_stuff` |
| functions that *are* a quantity | no verb — the name is what it returns | `true_range`, `triple_barrier` | `calculate_true_range` |
| pure descriptors | a noun phrase naming the returned object, no I/O | `symbol`, `artifact_dir`, `fold_bounds` | `get_fold_bounds` |
| populations of rows | `<population>_set` / `_window` | `training_set`, `scoring_set` | `get_train_indices` |
| report fragments | `<section>_block` | `sample_block`, `strategy_block` | `make_sample_dict` |
| statement constants (SQL text) | `<OBJECT>_<KIND>`, the kind `DDL`, `INSERT`, `COPY`, `SCAN`, `PREDICATE` or `COLUMNS` | `VENUE_DDL`, `CANONICAL_COPY`, `Y_COLUMNS` | `QUERY_1` |
| conversion factors | `<UNIT>_PER_<UNIT>` | `MILLISECONDS_PER_MINUTE` | `MS_MIN`, `60_000` inline |
| module-private helpers | a leading `_` on the name its grammar gives | `_pnl_block` | an `_` name imported by another module |
| gum calls | `gum_<subcommand>` and the one private `_gum`, in a terminal's `tui.py` alone (`TUI-DESIGNER-GUM-CALL-NAMED-FOR-ITS-SUBCOMMAND`) | `gum_table`, `gum_choose`, `_gum` | `render_table`, `show_menu`; gum outside `tui.py` |
| CLI entry | `main()`, one per stage module, returning the exit code | `main` | `run`, `cli`, `entrypoint` |
| quantities | `<what>_<unit>` | `fold_start_ms`, `equity_1m` | `n_min`, `off` |
| index arrays | `<population>_rows` | `training_rows`, `scoring_rows` | `tr`, `oi` |
| booleans | `<subject>_<predicate>`; a function that asks takes `is_`, `has_` or `requires_` | `label_valid`, `is_full_utc_day()` | `flag`, `ok`, `should_`, `check_` |
| artifact keys | snake_case, the identifier's own word; `<what>_count`, `<what>_<unit>`, `_pct`, `_utc`, `_ms` | `scored_row_count`, `coverage_pct`, `generated_at_utc` | a vocabulary of its own for JSON; a bare plural as a count; `n_` |
| features | `feature_id()` over `feature_definition_name()` of one `FEATURE_CATALOGUE` record (`module_features/skills/skill_feature_taxonomy.md`) | `centered_recursive_mean_gain_share14_1h` | a hand-written id or an alias; a popular indicator name, which is provenance |
| stored columns | the quantity for OHLCV, `<what>_<unit>` for anything derived, `<subject>_<predicate>` for a boolean; a column and its key carry one name | `timestamp_ms`, `ffill_bars` | a column and a key that disagree |
| Makefile targets | `<module>-<stage>` for a stage, `<module>-all` for a module's chain, `<module>-<process>` for a process of stages on the host, `<module>-<process>-<action>` for a hand's action on its files, `tmux-<target>` for the detached twin of one that resumes, `<module>-terminal` for a module's terminal, `skills-<action>` for the canon's tools; the lifecycle targets bare (`all`, `build`, `help`, `on`, `off`, `all-record`); every action carries its `##`, `help` and a terminal none | `data-ingest`, `features-serpentine-search-promote`, `tmux-features-serpentine-search`, `ml-terminal`, `skills-sync` | a bare stage, a `docker-` twin, a second switch pair, a `tmux-` twin of a terminal, a second Makefile |
| a terminal's menu | the actions of the one Makefile its `MENU_TARGET_PATTERN` gives its module, read off `make help` (`TUI-DESIGNER-ACTIONS-COME-FROM-MAKEFILE`) | `^(tmux-)?features-` | a menu written out by hand; an action offered in a second terminal |
| directories | `<category>_<detail>/` for a module; `store/<content>/` for a store; `ticker=<TICKER>/` and `timeframe=<timeframe>/` for a partition, Hive's `key=value` | `module_*`, `store/raw_1m`, `ticker=BTC/`, `timeframe=1h/` | `store_<content>/` at the root, `<TICKER>/` without its key |
| sub-modules | `sub_module_<subject>/` inside the module, or the canon, that owns it — its own `config.py`, an action module with `main()` per action of a hand, its `README_sub_module_<subject>.md` and its rule `skill_<subject>.md` beside it; no part in the chain's dataflow (§ The default choice) | `module_skills/sub_module_scalability_crawler/`, `module_features/sub_module_serpentine_search/`, `module_<domain>/sub_module_terminal/` | a sub-module at the root or of a sub-module; one that imports another module |
| images and compose services | the one image `liora-1m-pipeline`; a service named for its runtime role (`ASSET-CONTAINERS-THREE-RUNNERS-AND-ONE-RESIDENT`) | `ml`, `dashboard` | an image per service; a service named for a tool or a ticker |
| store paths | `store/<content>/` on the host, `/store/<content>` in a container, `STORE_<CONTENT>_DIR` between them (`ASSET-CONTAINERS-A-CONTAINER-ADDRESSES-A-STORE-AT-ITS-MOUNT`) | `STORE_RAW_1M_DIR` | a path derived from `__file__`; a store literal at the point of use |
| a module's own skills | `module_<name>/skills/`, every rule about that module and nothing else | `module_ml/skills/` | a single module's rule kept in `module_skills/` |
| a module's orientation | `README_module_<name>.md`, named for its directory (`FILES-AND-FOLDERS-README-ORIENTS`) | `module_ml/README_module_ml.md` | `module_data/README.md` |
| a timeframe's table and file | a partition `timeframe=<timeframe>/` carrying the compact token; a file of the asset's folder that carries a timeframe writes the five slots (`SORTING-FILES-NAMING-STANDARD-TIMEFRAME-SLOTS`) | `labels/ticker=BTC/timeframe=1h/labels.parquet` | `BTC_features_1h.parquet`; a slot as a partition value |
| CSS | BEM `block__element--modifier` (`DASHBOARD-CONVENTIONS-CSS-CLASSES-FOLLOW-BEM`) | `frame__head`, `pill--active` | `.red` |
| JavaScript functions at file scope | lowerCamelCase with a verb from the closed list (`DASHBOARD-CONVENTIONS-FILE-SCOPE-FUNCTIONS-TAKE-A-CLOSED-VERB`) | `buildMeter`, `renderStrategy`, `fetchRunRecord` | `makeTable`, a bare noun for a builder |

A numeric constant carries its unit — `_BARS`, `_MINUTES`, `_MS`, `_SECONDS`, `_DAYS`, `_ROWS`, `_FOLD_ID`, `_RATE`,
`_COUNT` — unless its name already says what is counted; a setting handed to a tool as text carries its unit in the
value (`DUCKDB_MEMORY_LIMIT`). The parameter word follows the mechanics — `SPAN` for an exponential smoothing,
`SMOOTHING_PERIOD` for a recursive mean, `LOOKBACK` for a rolling window, `HORIZON` for the future of a label,
`INTERVAL` for a sampling step — and a parameter of a catalogue term lives in its term
(`FEATURE-TAXONOMY-A-PARAMETER-LIVES-IN-ITS-TERM`). A compact timeframe token inside an identifier (`equity_1m`) is the
vocabulary of code and schema; the slot standard governs the file names of the asset's folder only. Domain
abbreviations (OHLCV, UTC, OOS, HPO, XGBoost) are spelled out on first use; a popular indicator name is provenance and
lives in `historical_aliases` (`FEATURE-TAXONOMY-A-NAME-IS-DERIVED`); a one-letter name is legal for its semantic role
alone (`SELF-EXPLAINING-NAMING-THE-NAME-CARRIES-THE-INFORMATION`). "QuantConnect Lean" on its first use in a file,
"Lean" afterwards; British spelling in the prose.

At an external boundary the external vocabulary wins inside the call that speaks it, and project names begin at the
return value (`SELF-EXPLAINING-NAMING-EXTERNAL-VOCABULARY-IS-REGISTERED`). The boundaries, each with the file that
owns it: the Lean tree (`module_data/lean.py`); the Binance and Bybit REST parameters (the two downloaders, and
`module_data/config.py` for the constants carrying `KLINE`); xgboost and optuna (`module_ml/model.py`,
`module_ml/hpo.py`); numpy and DuckDB SQL (every module that computes or queries); argparse (the one parser of each
runtime `config.py`, `promote.py` and every terminal); Hive's `key=value` (every `config.py` that builds a partition);
SVG and the DOM (the page's scripts); docker compose and tmux (`Makefile`, `docker-compose.yml`); `urllib` (the two
downloaders); `subprocess` over a stage's command line (`record.py`), a vendor's (`crawl.py`), gum's (`tui.py`) and
make's (every `terminal.py`); TOML (`vendors_for_crawling.toml`, read by `crawl.py` and the canon's terminal); a
workbook's XML parts (`module_skills/sheet.py`); `NO_COLOR` and `TERM` (each terminal's `config.py`); `http.server`
(`module_monitoring/serve.py`); and the file listing of the three pipeline stores (`record.py`).

## Rejected vocabulary

A list of words that steers the repository toward concrete, minimally correct solutions; no check gates it. The last
column of the grammar table holds the forms bound to one rule and the register's `never` columns the synonyms bound
to one concept; this list gathers the words bound to neither.

- **directories and path segments:** `src`, `core`, `lib`, `common`, `utils`, `helpers`, `manager`, `service`,
  `assets`, `artifacts`, `data`, `db`, `database`, `raw_data`, a lowercase ticker folder, a venue symbol as a folder;
  `repository_module_<domain>`, a numbered package directory
- **module and file stems:** `module_compose`, `module_docker`, `module_capsule`, `module_asset`, `module_viz`;
  `dashboard.py`, `proxy.py`, `server.py` beside `serve.py`; a strategy file per asset, a parameters file per stage, an
  `export` stage; a module named for a cloud resource (`module_s3`, `module_ecs`, `module_eventbridge`); `worker`,
  `processor`; `common`, `shared`, `lib` for what two modules share
- **function verbs:** `read_`, `probe_`, `spool_`, `iter_`, `run_`, `compute_`, `_factory`; in JavaScript `load`,
  `poll`. The stem is rejected as a **verb**: a function named for a noun the register carries is none, which is why
  `write_venue_spool()` stands — its verb `write`, its spool the file the register names
- **key names:** bare `lag`, `age`, `usage` without the subject and the unit, `mem`, `cpu_pct`, a bare duration for
  how long a container has been up, a hash, `weight` as a Y column, `_ts` on a UTC string
- **interface words:** `online` / `offline`, `alive`, `healthy`, `running` for an endpoint, `RAM`, `RSS`, `load`,
  `utilisation`, `freshness`, `boot`; `pill`, `chip`, `tile`, `stat` for a badge; `badge--off`, `status--red`, a
  coloured row; `mobile`, `tablet`, `phone`, `responsive`, `breakpoint`
- **tool and process words:** `-f` or `COMPOSE_FILE` on the compose line, a second compose file, a second Makefile;
  `8900` as the page's address in a document, a command or a comment — the host port is measured
  (`ASSET-CONTAINERS-THE-HOST-PORT-IS-MEASURED`), while `CONTAINER_PORT`, the port a server listens on in its own
  namespace, may be written as itself; `TODO`, `FIXME`, `XXX`, `HACK`; test suite, linter, coverage gate, CI, workflow,
  hook, code generator, framework; `authority`, `single source of truth`; `one-shot` for a one-off; `cloud-ready`,
  `AWS-ready`, `cloud-native`; `s3://` in a path constant, an adapter for a cloud that is not there; a hand-edited
  derived artifact

## The default choice

For every new change, prefer **the smallest, most modular and most obvious implementation that correctly closes the
full pipeline.**

**A skill belongs to the module whose responsibility it describes.** A rule about one module lives in
`module_<name>/skills/`; a rule that crosses modules or governs the project lives in `module_skills/` — the canon; a
module's orientation is its `README_module_<name>.md`. Each is written once, where ownership puts it
(`FILES-AND-FOLDERS-SHEET-IS-THE-SOURCE`, `FILES-AND-FOLDERS-SKILL-IS-RENDERED`); `module_skills/README.md` is the
index, and keeps the canon's prose that is no rule. `module_skills/skill_asset_containers.md` is the worked example of
a cross-cutting skill: the image, the services, the fan-out, the ceilings and the mounts are a contract between the
infrastructure and all four runtime modules at once, so it belongs to none of them.

A **sub-module** is the one boundary inside a module: `sub_module_<subject>/` in the module, or the canon, that owns
it, with its own `config.py`, its own `main()` and no part in the chain's dataflow. The tree holds three kinds, a
convention the directory grammar carries: the scalability crawler, `module_skills/sub_module_scalability_crawler/`,
nested in the canon because it reads files against the canon; a terminal per module, `module_<domain>/sub_module_terminal/`
— the canon's among them — which computes nothing, starts every stage through `make`, runs on the host's `python3`
and gum, and shares one `tui.py` and one skill, `module_skills/skill_tui_designer.md` (D19); and the serpentine
search, `module_features/sub_module_serpentine_search/`, a hand's research outside the chain whose question
`module_ml/score.py` answers, because a state is scored by the code that scores the chain, and whose promotion writes
the three files the chain reads.

## The shape — what holds the project together

The conditions below hold at every commit; a change that breaks one is wrong.

| # | holds |
|---|---|
| D01 | the root holds no data, feature or ML logic: its only Python is `record.py`, which measures every stage of a recorded run from outside and writes the run index; the canon's Python is its own tools — the sheet's reader and sync, the table of CONFIGURABLES records, the crawler and its terminal |
| D02 | `git grep "from module_"` inside a module package finds only that package: no module imports another |
| D03 | a module's skills live under that module; a rule that crosses modules lives in `module_skills/`; every skill is rows of the sheet, rendered and never edited by hand (`FILES-AND-FOLDERS-SKILL-IS-RENDERED`) |
| D04 | a fresh `git clone` followed by `make all` and `make on` is a working project |
| D05 | one `docker-compose.yml` carries the whole topology (`ASSET-CONTAINERS-ONE-COMPOSE-FILE`), and one `Makefile` the stage order and the fan-out |
| D06 | no module writes into another's source tree: what a stage writes lands in a store |
| D07 | an asset is `ASSET` on the make line and `--tickers` at the process boundary (`ASSET-CONTAINERS-ASSET-NARROWS-THE-MAKE-LINE-ALONE`) — never an image or a service of its own |
| D08 | no sub-module is a module: each has its own `config.py` and `main()` and none is in the chain's dataflow; the serpentine search's promotion writes the three files the ML chain reads, by a hand's choice (`SERPENTINE-SEARCH-PROMOTION-IS-A-HAND`) |
| D09 | artifact names and keys move only with the register: every key of every payload, file and family has a row of it, and a key added, dropped or renamed moves that row in the same commit (`AGENT-FIRST-DEVELOPMENT-NAME-ENTERS-THE-REGISTER`) |
| D10 | determinism is unchanged: the caps, the seeds, the pinned orders (`module_skills/skill_determinism.md`) |
| D11 | parity: the chain on a frozen copy of the raw store reproduces every file of `store/assets_artifacts/` and `store/trials/` and the three computational snapshots, normalised, byte for byte against the reference manifest (`README.md` § Parity). A day the download adds past the frozen copy changes the raw tree, the two venue families, the canonical family and `data_status.json` alone. The files a hand drafts stand outside the proof, and so do the serpentine search's own — its state, its ledger and the asset's partition of `score_trials` — whose proof is that a search reset and run again over the same inputs gives the same bytes, and that a search stopped and run again ends on the same state and ledger; the one exception, `score_trials` holding a study twice after a stop between its lines and the answer (`score.hpo_results()`). The state and the ledger are tracked all the same, because `features_status.json` reads them and is inside the proof. A change that reshapes one of the chain's files re-bases its line and no other, compared field by field, every kept field byte-identical |
| D12 | zero cloud mechanisms: nothing reaches a service off this host but the venues' public endpoints the two downloaders read and the crawler's one active vendor command line, outside the chain; the trial ledgers are partitions of `STORE_TRIALS_DIR` (`METHODOLOGY-ML-LEDGER-IS-APPEND-ONLY`), never a network location; the four pins of `requirements.txt` are the project's, and a fifth moves this line in the commit that adds it |
| D13 | `features_status.json` is written by `module_features.status` |
| D14 | every object of `module_skills/skill_glossary.md` § Twice by extraction is marked `# twice by extraction` directly above its own definition — one marker per object — and changed on every side at once |
| D15 | the tracked remnant of the artifacts store (`SERPENTINE-SEARCH-ITS-RECORD-IS-TRACKED`, the register's asset folder) and the four snapshots are tracked, so a fresh clone opens on real numbers and on the profile the last search ran under |
| D16 | the fan-out, the serpentine search's loop and its detached twin run through `docker compose run --rm`, one one-off container per step; nothing is `exec`'d into a resident |
| D17 | the crawler's snapshot and reports are written by the crawler alone (`FILES-AND-FOLDERS-GENERATED-BY-THE-CRAWL`); the snapshot is tracked in its neutral state — every controlled file `pending`, no report — and rewritten by every crawl, the reports untracked |
| D18 | the crawler gates nothing: no target of the chain, no service and no merge depends on it, and a hand alone starts it |
| D19 | a module's terminal imports the standard library and its own package alone and starts every stage through `make` (`TUI-DESIGNER-ONE-TERMINAL-PER-MODULE`); the features terminal carries registered copies of what it reads, and writes one file, the profile its draft makes; no terminal runs `tmux` or `docker` |

## Skills absent here, described

Skills the Pre-AWS seats imply and this tree does not hold: each placed by ownership as § The default choice places
every skill, described today where its last column says, and written when its one condition holds.

| skill | owner | governs | written when | described today in |
|---|---|---|---|---|
| `skill_task_host_volume.md` | `module_skills/` | the one Linux host every asset's runs share and the volume mounted where the `./store/<content>` mounts are today — every asset's folder and the other `store/<content>/` folders at the same `/store/<content>` paths, and what a task may leave on it | the first run whose `store/<content>/` folders sit on a volume that is not this host's disk | `module_skills/README.md` § The Pre-AWS mapping, The seats and The home and the copy |
| `skill_object_storage_layout.md` | `module_skills/` | the prefixes of the copy — `raw_1m/` written once, `assets_artifacts/<run_id>/`, `trials/`, `run_records/`, `status/` — and the one discipline: a whole file copied after the last stage of a run has exited, never a path a stage writes | the first whole file copied off the host | `module_skills/README.md` § The Pre-AWS mapping, The home and the copy |
| `skill_stage_state_machine.md` | `module_skills/` | one state per stage in the order of `DATA_STAGES`, `FEATURES_STAGES` and `ML_STAGES`, a Map over `TICKERS` whose width is `JOBS`, the execution named by `run_id`, the whole-file copy as the state after the last stage, and the schedule that starts it | the first stage launched by something other than `make` | `module_skills/README.md` § The Pre-AWS mapping, The Makefile, read forward and The ladder; `PRE-AWS-SOLUTION-THE-MAKEFILE-NEVER-SCHEDULES` |
| `skill_rebuild_condition.md` | `module_skills/` | the four `has_` / `requires_` predicates — read-only, per asset, in the module that owns what they compare — and the condition state that reads them; never a function that both detects and trains | the first freshness predicate is written, `has_new_market_data(ticker)` in `module_data` | `PRE-AWS-SOLUTION-THE-REBUILD-CONDITION-STAYS-SEPARABLE`; `module_skills/skill_glossary.md` § Pre-AWS direction |
| `skill_artifact_versioning.md` | `module_skills/` | `<version>` = `run_id` under the `assets_artifacts/` prefix, which version is the active one and how a reader resolves it; no version inside an artifact | the second version of one asset's artifacts exists off the host | `PRE-AWS-SOLUTION-AN-ARTIFACT-CARRIES-NO-RUN-IDENTITY`; `module_skills/README.md` § The Pre-AWS mapping, The home and the copy; `module_ml/skills/methodology_ml.md` § 10 |
| `skill_dashboard_front.md` | `module_monitoring/skills/` | the page files, the snapshots and the run records as static objects behind a content-delivery front — the three prefixes of `module_monitoring/serve.py` read forward; until then the tunnel of `README.md` § Quickstart | the first reader the tunnel does not serve | `module_skills/README.md` § The Pre-AWS mapping, The mapping table, the rows `MONITORING — the static dashboard` and `MONITORING — a small reader process`, and What stays as it is, and why, the `module_monitoring/serve.py` row |
| `skill_strategy_execution.md` | `module_trading/skills/` | `module_trading/` — a fifth module beside `module_ml`, with its own container, reading the Lean-exact raw tree and the asset artifacts from the copy, its brokerage credentials read once at start from a secrets store | `module_trading/` is created — the first strategy that consumes an artifact | `module_skills/README.md` § The Pre-AWS mapping, The twelve classes and the paragraph under them, and The mapping table, the two STRATEGY EXECUTION rows |
| `skill_per_asset_status.md` | `module_skills/` | one status object per asset, written by that asset's own status run, and the fold the reader does over them — never a lock, never a basket-wide writer fanned out | a status stage is fanned out for the first time | `ASSET-CONTAINERS-FANOUT-PER-ASSET-BASKET-ONCE`; `module_skills/README.md` § The Pre-AWS mapping, What stays as it is, and why, the status stages' row |
| `skill_database_promotion.md` | `module_data/skills/` | the threshold past which the table families become a managed database — a second concurrent writer of one partition, or a reader that needs one transaction across families | the first writer or reader one stage per family and one operation per checkout cannot serve | `PRE-AWS-SOLUTION-NO-DATABASE-PROCESS-BEFORE-THE-PROMOTION-THRESHOLD`; `CANDLE-CANONICALISATION-THE-CANONICAL-SERIES-IS-STORED-ONCE`; `module_skills/README.md` § The Pre-AWS mapping, The seats, the market object |
