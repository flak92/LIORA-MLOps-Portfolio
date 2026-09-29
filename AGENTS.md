# AGENTS — the contract of this repository

The governing contract for every change, human or agent. Read the project in
this order: **AGENTS.md → module names →
`README_module_<name>.md` → the module's own `skills/` → code**, with
`module_skills/` beside them for the rules that cross modules, indexed by
`module_skills/README.md`. (A `README.md` is general information, not part of
the working path.) If a change conflicts with this file, the change is wrong.

## Values

- **Destination, not road.** *The repository shows the destination, not the road*. No tests, no security
  layers, no CI, no precautionary guardrails; the only guards are the ones the
  mathematics requires, and a stage proves itself by running. One crawler
  stands beside the chain: the scalability crawler,
  `module_skills/sub_module_scalability_crawler/`, reads each controlled file of
  the sheet's files matrix against the Skills marked for it with the one active
  vendor, writes one report per file a hand reads, untracked, and its snapshot;
  a hand starts it with `make skills-crawl`, and nothing schedules it; it gates
  nothing, edits no tracked file, commits nothing.
- **Minimalism.** Every line, file, module and dependency has a concrete
  purpose. If its purpose cannot be named, it goes.
- **Minimum requirements.** Python 3.12.x with `venv` and `pip`; the container
  is `python:3.12-slim`, one image for the tree. A library is added
  only when the standard library and the current stack — `duckdb`,
  `numpy`, `optuna`, `xgboost-cpu` — cannot do the job, or when
  it is the field's own instrument for a responsibility this project names and
  the stack's equivalent would be a private reimplementation of it: § Canonical
  vocabulary's preference for an established name over a local synonym, read
  forward from names to instruments. No library stands on that reading today.
  The trial ledgers did, and do not: they are JSON Lines written by
  `dataset.append_jsonl`, the technique the serpentine search's own ledger
  already uses, and what this project needed was not the instrument but a
  smaller thing than it — a file of lines, which is what a ledger is. `optuna`
  stays on the first reading, and what it costs is measured rather than
  assumed: `import optuna` loads `colorlog`, `tqdm` and `packaging` beside
  `numpy`, and the rest of what its pin installs — `alembic`, `SQLAlchemy`,
  `greenlet`, `Mako` and `MarkupSafe`, the storage it is never asked for, with
  `PyYAML` and `typing_extensions` — is never imported by this tree. By the
  same reading the
  host admits `gum`, the field's own instrument for a responsibility this
  project names — a hand's choice in a terminal and the screens around it, the
  terminals' text-based user interface (TUI) — where the alternative would be a
  private chooser and table over curses: a binary of the host,
  no pin of `requirements.txt`. `requirements.txt` declares
  the project's direct dependencies only, one pinned version each.
- **KISS / YAGNI / DRY / SOLID.** The simplest correct implementation, built
  for the need that exists, never for a hypothetical one. One responsibility
  per module; repeated logic becomes one function, not three copies.
- **UCAS — Useless Click Avoiding System.** Manual steps, clicks and context
  switches that can be automated, are: `make all` runs the whole pipeline
  from a fresh clone, every stage is idempotent in what it derives — the
  trial ledgers alone accumulate, each study appending its lines,
  until a hand clears them, and beside the chain the crawler's reports, reset and
  written again by every crawl — and the dashboard opens itself.
- **Main = clean working logic.** No test frameworks, security layers,
  validation frameworks or precautionary guards. What stays are the seven
  guards the mathematics requires: causality invariants (`indicators.asof_index`) and
  arithmetic preconditions (the full canonical grid inside the frozen research
  window, asserted per asset by `labels.load_research_1m`, and a finite,
  positive true-range recursive mean at every decision, asserted beside it; the aligned decision
  grids of the arrays `dataset.build_xy` joins by position — one guard, asserted twice, because the catalogue's partitions agreeing with each other and X agreeing with Y are two checks; a finite
  catalogue after the warm-up, asserted by `catalogue.build_catalogue`; the download that
  aborts on a short post-listing day, and the listing probe that aborts when a
  symbol's history starts after the window) — and beside them, not guards:
  the one-line message of a status stage with nothing to report, naming the
  stage to run first, a venue's own error code surfaced as it came, and a stage's one-line refusal of an
  input it cannot use — a study whose every trial was pruned, a scoring request of an unknown kind, a promotion
  with no proposal. A test suite, a linter,
  a coverage gate, a workflow or a merge block does not belong here. No debt
  marker in a tracked file — this contract names the forbidden form — and no code left inside a comment: a marker is a
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

`module_*` is a top-level project responsibility; `store/` is persisted or
generated state. Four modules — one Python package `module_<domain>` each, in
the order the data moves through them — and, around them, the launcher that runs
them and carries no dataflow of its own:

```
module_data/         sources → normalised raw 1m → the venue families and the canonical family ohlcv_1m_canonical, one partition per asset
module_features/     the canonical family → the family bars → the family catalogue, one partition per asset and timeframe, the per-asset contract and its snapshot; outside the chain, the serpentine search over the feature set, the barrier geometry and the hyper-parameters, and its promotion
module_ml/           the catalogue and the canonical path → X, Y → search → model → research simulation: the families labels, oos_predictions, hpo_trials; outside the chain, the scoring of the serpentine search's questions and the family score_trials
module_monitoring/   presentation of what the three computational modules measured about themselves, of what record.py measured around every stage and of the dates of the canon's crawler's reports, and the server that serves it
the root             the Makefile and docker-compose.yml that run the four, record.py, the five stores, one folder each under store/, and the canon: this contract and module_skills/ — the sheet every rule and the name register are rendered from (module_skills/skills_sheet.xlsx), the cross-cutting skills, the index of every module's own, the crawler that reads each controlled file against the Skills marked for it (module_skills/sub_module_scalability_crawler/) and the canon's terminal
```

Each module holds its package, its orientation `README_module_<domain>.md` and
its own `skills/` under one directory; nothing above it belongs to one module
alone. `make all` from a fresh clone runs the chain. A reference is a path in
backticks, always.

`module_skills` participates in no runtime import and in no dataflow of the chain:
its sync renders the Skills from the sheet, and its crawler reads the controlled files and writes their reports and
one snapshot about them. **No module
imports another.** What would cross a module boundary as an import crosses it as a
file in a store instead — the five `STORE_*_DIR` the launcher names
(`module_skills/skill_glossary.md` § Stores), the families of the artifact store, the per-asset contract
`<TICKER>_catalogue.json` the feature layer writes and every ML stage reads, the
four snapshots — the three each computational module writes about itself and the crawler's —
which the dashboard serves, the run record `record.py` writes around every stage, the serpentine
search's question and answer `<TICKER>_score_request.json` and `<TICKER>_score_response.json` with the
parameters `<TICKER>_parameters.json` it starts from, and the feature set and barriers
`<TICKER>_feature_set.json` and `<TICKER>_barriers.json` its promotion writes for the ML chain — or as a copy
registered in `module_skills/skill_glossary.md` § Twice by extraction, identical to the
byte on every side unless its row there says equal by value. The basket is the launcher's: `TICKERS` in the
`Makefile`; every stage is told its assets by `--tickers` and defines
none. A new `module_<domain>` is justified only by a
distinct responsibility with a stable input/output boundary; until then the
owning module is extended, and no repository is ever created for what two
modules share — a dozen shared lines are a registered duplicate, not a `common`.
`module_features` is that case: its input is the canonical series, its output
the family `catalogue`, one partition per timeframe that any model could read, and the contract that names
them, and nothing above it in the dataflow imports it; outside the chain its
serpentine search reads the ML module's parameters and, by a hand's promotion,
writes the feature set and the barriers the ML chain reads.

Each `module_*` is an **extracted bounded context**: its domain rules, its
orientation and its code sit together under its own directory, so its meaning is
never reconstructed from documentation that stayed elsewhere. It runs standalone
against the `store/<content>/` folders it touches, each named by the launcher
(`python -m <module>.<stage> --tickers <TICKER>`, in a venv with the
`STORE_*_DIR` it reads exported or in a one-off container of its runner), and knows
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
  `download_bybit.py`, `store/assets_artifacts/ticker=<TICKER>/<TICKER>_<artifact>.<ext>`,
  `<family>/ticker=<TICKER>/[timeframe=<timeframe>/]<family>.parquet`, `ml-<stage>`
  targets); each computational module (`module_data`,
  `module_features`, `module_ml`) measures its own domain state in `status.py`,
  and `module_monitoring` presents their snapshots; the canon's sub-module
  measures the tree against the canon in a `status.py` of its own;
- **taxonomic ordering — the category token comes first, so siblings sort
  together.** A listing is read by eye before it is parsed: at the root
  `module_data`, `module_features`, `module_ml`,
  `module_monitoring` — the chain in its own order — then `module_skills`,
  then the one folder `store/`, whose five children — `assets_artifacts`,
  `raw_1m`, `run_records`, `status`, `trials` — sort together inside it, the
  category token spoken once, by their parent: blocks, not scattered entries. If
  renaming would put things of one category next to each other, rename them;
- short, predictable paths, built only in a module's `config.py` — never
  assembled at the point of use; the exceptions are an external format's own
  file names, built by its adapter (`module_data/lean.py` builds the QuantConnect
  Lean tree's file names, `record.py` those of the four pipeline stores it lists,
  every store but `store/trials/`), the Makefile's serpentine search targets, which name
  the files they test and remove — the loop the one file `<TICKER>_score_request.json`,
  the reset the files the turn and `ml-score` write for one asset
  — and the browser, which has no config module and reads its four snapshots
  (`data_status.json`, `features_status.json`, `ml_status.json`, `skills_status.json`) under
  `status/`, and `run_records/index.json` and the records it lists under `run_records/`, by
  relative path and literal name; one asset is one partition, `ticker=<TICKER>`: its non-tabular files in
  `store/assets_artifacts/ticker=<TICKER>/`, one file per distinct artifact
  responsibility, its rows of a table in `<family>/ticker=<TICKER>/[timeframe=<timeframe>/]` — one
  stage writing each family and the family's `schema.json` beside its partitions, DuckDB the
  engine in memory and no database file anywhere. The partition value is the ticker in capitals, the raw tree
  is the symbol in lower case because Lean demands it — that difference is a
  boundary, not an inconsistency to tidy away. A store's variable
  spells the exact canonical tokens of its path, the parent folder's first and
  then its child's, so the name predicts the
  directory it names — on the host `STORE_RAW_1M_DIR` → `store/raw_1m/`,
  `STORE_RUN_RECORDS_DIR` → `store/run_records/`, in a container the same
  variables → `/store/raw_1m`, `/store/run_records`;
- one convention per language: BEM in CSS, snake_case in Python and JSON,
  the same hierarchy everywhere, no accidental exceptions.

## Pre-AWS architectural direction

Pre-AWS is this repository's word for its own shape: a local, academic
architecture whose boundaries would still be the right boundaries after local
storage, local container execution and local stage order were replaced by their
standard equivalents on Amazon Web Services (AWS). No cloud is used and none is
planned; the mapping is described in `module_skills/skill_pre_aws_solution.md`
and built nowhere.

- **Academic, not AWS.** The runtime is local — one image for the tree under
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
  service definition is named for a ticker, and a ticker may name a convenience
  alias in the Makefile, with its sunset note, never a target another file
  depends on; a new asset is one ticker in the `Makefile`'s `TICKERS`, and
  nothing else.
- **Compute owns no state.** A stage reads a store, writes a store and exits; it
  holds nothing between invocations, binds no port, reads no `ASSET` and assumes
  no resident peer. A checkout runs one operation that writes state at a time,
  which is why no store carries a lock; the operations are listed once, in
  `PRE-AWS-SOLUTION-ONE-OPERATION-WRITES-AT-A-TIME-AND-NOTHING-LOCKS`.
- **Storage is separate from compute.** Pipeline state lives in the five stores,
  one folder each under `store/`, named to every `config.py` by its
  `STORE_*_DIR` and mounted from `store/<content>/` at `/store/<content>` into each service that touches
  them, read-only where a service only reads
  (`ASSET-CONTAINERS-A-SERVICE-MOUNTS-ONLY-THE-STORES-IT-TOUCHES`) — never
  inside a container and never inside a module's source tree; the image carries the
  pins and nothing else, the code and the state arrive as mounts, and the four
  snapshots are tracked, beside the tracked remnant of the artifacts store (D15);
  the crawler's reports lie in the status store beside them, untracked — reset and
  written again by every crawl.
- **Modules are built by ownership and lifetime.** A function sits beside the
  functions that write the same state and live as long as it does, never beside
  what happened to be written with it; every object is classified before it is
  placed.
- **Every placement is argued, and the mapping is the test.** For every object
  a module holds, its `README_module_<name>.md` § Design rationale writes down,
  in one row, the answers the naming review asks for that place it
  (`SELF-EXPLAINING-NAMING-A-NEW-OBJECT-PASSES-THE-NAMING-REVIEW`) — why here, why beside these, why this
  boundary — and which row of the mapping table it answers to, the fourth being
  the test of the first three. An object one of whose responsibilities answers
  to no row, or to two, is questioned before it is committed; a file that holds
  several responsibilities — a descriptor per store —
  answers with one row each, and says so. The rows are the mapping table of
  `module_skills/README.md` § The Pre-AWS mapping. The canon's orientation is its
  index, `module_skills/README.md`; its crawler argues its objects in
  `module_skills/sub_module_scalability_crawler/README_sub_module_scalability_crawler.md` § Design rationale.
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
  `data`, `features` and `ml` are how the fan-out does it locally.
- **A few assets are proof enough.** The whole chain on `BTC` demonstrates the
  architecture; scale is `ASSET=<TICKER>`, never hundreds of assets.

Cloud proper nouns are external vocabulary. Apart from the repository's own word
*Pre-AWS* — `module_skills/skill_glossary.md` § Pre-AWS direction, and the `pre_aws`
file stem it registers, the skill's — they are spoken only
where the stance is stated, reviewed or a local object is seated: this section,
§ Rejected vocabulary — the forms it refuses — and § Skills absent here,
described, `README.md` § Architectural direction, the
rows of `module_skills/skill_pre_aws_solution.md`, and `module_skills/README.md`
§ The Pre-AWS mapping — its prose, the seats of the local skills, each naming the
primitive in the table's words, and the column *the same responsibility elsewhere*
of its mapping table — and, in the register, the columns *External vocabulary* and
*Never* of `module_skills/skill_glossary.md` § Pre-AWS direction, where a foreign
name has its place beside the concept it reads forward to. Never in a make
target, a compose service, an environment variable, a payload key, a code
comment, an identifier, or a tracked path but the `pre_aws` stem. The rules are `module_skills/skill_pre_aws_solution.md` — a
cross-cutting skill of the kind § The default choice names, beside
`skill_asset_containers.md`; the twelve classes, the seats, the mapping table and
the review of what stays local are `module_skills/README.md` § The Pre-AWS mapping.

## Canonical vocabulary

**Names must be self-explanatory before they are project-specific. Prefer
established software-engineering terminology over project-specific synonyms: if
a concept already has a widely recognised name, use that name — in code, in
documentation, in the skills and in the interface alike — and do not invent
local terminology for a standard concept. A glossary confirms meaning; it must
not be required to decode an obscure name.**

One concept, one name — in the code, in the artifacts, in the interface, in the
Makefile, in docker compose and in the documents. The
register is `module_skills/skill_glossary.md`, rendered from the register table of
`module_skills/skills_sheet.xlsx`, and a new name enters that table in the same
commit that introduces it. The word "test" never names a fold.

And one name, one concept. A name that could denote two things **in the same
scope** is renamed until it denotes one. The scopes are enumerated so the rule
applies without argument: make targets, compose services, container environment
variables, tracked paths, and Python symbols within a module. A name shared across *different* scopes is not a
collision.

**Derived, never drafted.** A derived artifact is generated from source and
config and never hand-edited: `<TICKER>_parameters.json`,
`<TICKER>_serpentine_search.json` and its ledger `<TICKER>_serpentine_search_trials.jsonl`,
`<TICKER>_README.md`, `<TICKER>_catalogue.json`, the four snapshots, and every `skill_*.md` with
`module_skills/skill_glossary.md`, rendered from the sheet by `make skills-sync`. A hand edit to one is a
violation; `make features-serpentine-search-reset` removing the search's own files is not an edit
but the start of another experiment.

**Drafted, never derived.** A drafted artifact is a hand's decision written down
and never computed from another file: `module_skills/skills_sheet.xlsx`, every rule
of the tree, the name register and the files matrix, edited by a hand with any spreadsheet program;
`<TICKER>_serpentine_search_profile.json`, the
columns a hand admits to a search, the columns it starts from, the grid of each
coordinate, the loops of a round and the asset's noise sigma, measured once off a
calibration run; and, once a hand has promoted one,
`<TICKER>_feature_set.json` and `<TICKER>_barriers.json`. The profile and the promoted files are each
written by one program — the features terminal's draft, or the promotion — and each may equally be
edited in the file, because the same decisions write the same bytes and a rewrite
that changes nothing leaves `git status` clean. A stage that derives one is a
violation.

**Rule-derived structure over repeated project knowledge.** When a family —
assets, venues, timeframes, paths, artifact files, payload keys, pipeline stages
— is governed by one definition, derive the repeated representations from it
rather than copying the same list into several files: `TICKERS` in the
orchestration `Makefile` — the launcher — is the one definition the fan-out and
every `--tickers` derive from; a module is told its assets and never defines
them.
The limit is equally binding: no code generator,
no metaprogramming, no abstraction layer for a one-off value — and none for a
file whose whole value is being read. The one rendering the tree holds is
`make skills-sync`, which writes the canon's documents from its one sheet.

Every layer has a closed grammar, the way CSS has BEM. A name is **derived**
from its layer's grammar, never invented:

| layer | grammar | in this repo | what it forbids |
|---|---|---|---|
| constants | `<OBJECT>_<ROLE>_<PARAMETER>_<UNIT>` | `LABEL_BARRIER_TRUE_RANGE_SMOOTHING_PERIOD_BARS` | `BARRIER_N` |
| constant comments | a comment that explains a Python module-level constant takes one of PEP 8's two forms, by what it explains: an inline comment on the line of the one constant it explains; a block comment directly above the lines it explains when they are several constants, or one constant whose value spans several lines; the `# twice by extraction` marker explains nothing and stands where D14 places it; a file that departs moves its comments with its next change | `BYBIT_KLINE_REQUEST_LIMIT = 1000   # < 1440 -> …`; the block comments above `BINANCE_KLINE_URL` and above `VENUE_SCAN` | a block comment above a one-line constant it alone explains; an inline comment that explains the lines under it |
| external I/O functions | `<verb>_<object>`, verb from the closed list `fetch_` (network), `load_` (storage → memory), `write_` (persist), `parse_` (bytes → values) | `fetch_klines`, `load_xy`, `write_parquet`, `parse_zip` | `get_`, `process_`, `handle_` |
| conversions | `to_<representation>` | `to_class`, `to_json_safe` | ambiguous `convert` |
| composite constructors | `build_<object>` | `build_x` | `make_stuff` |
| functions that *are* a quantity | no verb — the name is what it returns | `recursive_mean_gain_share`, `true_range`, `sharpe_annualised`, `triple_barrier` | `calculate_true_range` |
| pure descriptors | a noun phrase naming the returned object; a descriptor does no I/O — the moment it fetches, loads or writes it takes that verb, the moment it assembles it takes `build_` | `symbol`, `artifact_dir`, `fold_bounds` | `get_fold_bounds`, `fetch_symbol` |
| populations of rows | `<population>_set` / `_window` | `training_set`, `scoring_set`, `prediction_window` | `get_train_indices` |
| report fragments | `<section>_block` | `sample_block`, `strategy_block`, `hyperparameter_search_result_block` | `make_sample_dict` |
| statement constants (SQL text) | `<OBJECT>_<KIND>`, kind from the closed list `DDL`, `INSERT`, `COPY`, `SCAN`, `PREDICATE`, `COLUMNS` | `VENUE_DDL`, `CANONICAL_COPY`, `BAR_COPY`, `VENUE_SCAN`, `OHLC_INTACT_PREDICATE`, `Y_COLUMNS` | `SOURCE_SWITCHES`, `QUERY_1` |
| conversion factors | `<UNIT>_PER_<UNIT>` | `MILLISECONDS_PER_MINUTE`, `MINUTES_PER_DAY` | `MS_MIN`, `60_000` inline |
| module-private helpers | a leading `_` on the name its layer's grammar gives, for a helper no other module may import | `_pnl_block`, `_classification_block` | an `_` name imported by another module |
| gum calls | `gum_<subcommand>`, the subcommand from gum's own closed list — `table`, `style`, `choose`, `filter`, `input` — for the one function that speaks it, and `_gum`, the one private call that runs a prompt and returns its answer, in the `tui.py` of a terminal and nowhere else — one file, the same in every `sub_module_terminal/`, each copy registered, never a second spelling (`module_skills/skill_glossary.md` § Twice by extraction) | `gum_table`, `gum_choose`, `gum_input`, `_gum` | `render_table`, `show_menu`, `print_block`, `draw_`; a gum command line outside `tui.py`; a second spelling of `tui.py` |
| CLI entry | `main()` — one per stage module, returning the exit code | `main` | `run`, `cli`, `entrypoint` |
| quantities | `<what>_<unit>` | `fold_start_ms`, `equity_1m`, `decision_bar_minutes` | `n_min`, `off` |
| index arrays | `<population>_rows` | `training_rows`, `window_rows`, `scoring_rows` | `tr`, `wi`, `oi` |
| booleans | `<subject>_<predicate>`, stating the condition that is true; a function that asks takes `is_`, `has_` or `requires_` — state, possession, obligation | `entry_observable`, `label_valid`, `is_full_utc_day()`, `is_artifact_set_complete()` | `flag`, `ok`, `check`; `should_`, `check_`, `needs_`, a bare `trigger` |
| artifact keys | snake_case, the same word as the identifier that produced it; a count is `<what>_count`, a quantity with a unit `<what>_<unit>`, a share `_pct`, a formatted UTC string `_utc`, epoch milliseconds `_ms` | `scored_row_count`, `ffill_bars`, `coverage_pct`, `generated_at_utc` | a separate vocabulary for JSON; a bare plural (`gaps`) or an adjective (`ambiguous`) as a count; `n_`; `ret` for return |
| features | `[<normaliser>_]<term>{_<operator>_<term>}_<timeframe>`, a term `[<series>_]<indicator><parameter>` or a bare series — `feature_id()` over `feature_definition_name()` of one `FEATURE_CATALOGUE` record, the one downstream copy the registered `feature_id()` of `module_ml`, never written by hand; one definition, one id, no second name — the rest is `module_features/skills/skill_feature_taxonomy.md` | `exponential_smoothing20_minus_exponential_smoothing50_over_true_range_recursive_mean14_8h`, `centered_recursive_mean_gain_share14_1h`, `rolling_range_position20_1d` | a hand-written id or a local alias (`feature_3`, `f_gain_share`, `gain_share_14`, `rolling_mean_200`, `trend_1d`), and any popular indicator name, which is provenance and lives in `historical_aliases` |
| stored columns | the quantity for OHLCV, `<what>_<unit>` for anything derived, `<subject>_<predicate>` for a boolean — and a column and the key that publishes it carry **one** name | `timestamp_ms`, `ffill_bars`, `zero_volume_bars`, `binance_valid` | `n_ffill`, a column and key that disagree |
| Makefile targets | `<module>-<stage>` for a stage of a runtime module — run in a one-off container of that module's runner — and `<module>-all` for its chain; `<module>-<process>` for a process on the host composed of stages — the module's own and those that answer them, each step a one-off container — and `<module>-<process>-<action>` for a hand's action on that process's files, run in a one-off container where it computes and on the host where it only removes files; `tmux-<module>-<stage>` or `tmux-<module>-<process>` for the detached twin of a stage or a process that outlives the terminal — only one that resumes may have one; a module's own terminal takes `<module>-terminal` and is run by `python3` on the host, never in a container — gum asks a hand in the shell it was started from, and a terminal does not resume, so it has no `tmux-` twin; `skills-<action>` for the canon's own tools — `skills-sync`, `skills-configurables` and `skills-crawl` — and `skills-terminal` for its terminal, run by `python3` on the host, the canon having no runner; only the lifecycle targets go bare (`all`, `build`, `help`, `on`, `off`, `all-record`), `on` / `off` being the presentation switch, and a ticker alias of a lifecycle target carries its own sunset note; every action carries its `##` and `help` and every `<module>-terminal` carry none — the Makefile's own index and an interface's entry are not actions | `data-ingest`, `ml-hpo`, `features-all`, `features-serpentine-turn` and `ml-score`, the serpentine search's two stages; `features-serpentine-search`, the loop of them; `features-serpentine-search-promote` and `features-serpentine-search-reset`, a hand's two actions on its files, the reset on the host; `tmux-features-serpentine-search`, `ml-terminal`, `skills-sync`, `on` | a bare stage (`ingest`), a `docker-` twin of a stage (there is one way to run a stage), a target named after the tool (`docker-run`), a detached twin of a stage or a process that cannot resume, a second switch pair (`start` / `stop`, `up` / `down`), a TUI under `<module>-<stage>`, `<module>-tui` or `<module>-menu`, a `tmux-` twin of a terminal, a `##` on `help` or on a terminal, a second Makefile carrying stage order of its own |
| a terminal's menu | the actions of the one Makefile whose names give them to its module, read off `make help` by `MENU_TARGET_PATTERN` in the terminal's `config.py` — `<module>-<stage>`, `<module>-all`, `<module>-<process>` with its actions, and a `tmux-` twin — so an action is offered in the one terminal of the module it names | `^(tmux-)?features-` | a menu written out by hand; an action offered in a second terminal; the terminal's own entry among its actions |
| directories | `<category>_<detail>/` for a module; the stores are one folder `store/` whose children are `<content>/` — the container's `/store/<content>` read back onto the host; a raw store names its granularity with the compact timeframe token, `store/raw_<timeframe>/`; an asset's folder and a table's partition are `ticker=<TICKER>/`, a timeframe's partition `timeframe=<timeframe>/` — Hive's `key=value`, the form a query engine reads as partition columns, the value the ticker in capitals and the compact token | `module_*`, `store/`, `store/raw_1m`, `ticker=BTC/`, `timeframe=1h/` | a kind scattered through the alphabet, a store spelling its timeframe in sorting slots, `repository_module_<domain>/`, `store_<content>/` at the root, a child that repeats its parent's token (`store/store_raw_1m/`), `<TICKER>/` without its key, a lower-case ticker as a partition value |
| sub-modules | `sub_module_<subject>/` inside the module, or the canon, that owns it — its own `config.py`, one action module with `main()` for each action of a hand, `tui.py` where it draws a terminal, its orientation `README_sub_module_<subject>.md`, and its rule beside it as `skill_<subject>.md`, `skill_<domain>_<subject>.md` where the stem would repeat across modules; no part in the chain's dataflow — a hand's research outside the chain at most, whose promotion writes files the chain reads (§ The default choice) | `module_skills/sub_module_scalability_crawler/`, `module_features/sub_module_serpentine_search/`, `module_<domain>/sub_module_terminal/` | a sub-module at the root; a sub-module of a sub-module; a sub-module that imports another module (D02); the domain repeated in the folder (`sub_module_ml_terminal`); a sub-module oriented by a section of its module's README |
| images | `liora-1m-pipeline`, one for the tree, built from the root `Dockerfile` | `liora-1m-pipeline` | compose's `<project>-<service>` default, an image per service, an image per asset, an image per module |
| compose services | a runtime role, never an image or a ticker — the runners `data`, `features`, `ml`, the resident `dashboard` | `ml`, `dashboard` | `pipeline`, a service named for an image or a tool, a service per asset stage |
| store paths | `store/<content>/` on the host, `/store/<content>` inside a container, `STORE_<CONTENT>_DIR` the variable that names the one to the other | `store/raw_1m/`, `/store/raw_1m`, `STORE_RAW_1M_DIR` | a path derived from `__file__`, `/app/store/<content>` as an address, a store literal at the point of use |
| a module's own skills | `module_<name>/skills/`, holding every rule about that module and nothing else | `module_data/skills/`, `module_features/skills/`, `module_ml/skills/`, `module_monitoring/skills/` | a single module's rule kept in `module_skills/`; a second copy of one rule in both; a module's rule in `module_skills/` |
| a module's orientation | `README_module_<name>.md`, the name derived from the module directory it sits in | `module_data/README_module_data.md`, `module_features/README_module_features.md`, `module_ml/README_module_ml.md`, `module_monitoring/README_module_monitoring.md` | `module_data/README.md`; an orientation file that restates a skill |
| a table's partition and an artifact file of one timeframe family | a table of a timeframe family is one partition `timeframe=<timeframe>/` of its family, the compact token its value, its Parquet file named for the family and carrying no slot; an artifact file of the asset's folder writes `<asset>_<artifact>_<timeframe-slot>.<ext>`, slots per the standard `ss-mm-hh-dd-MM` (`module_skills/skill_sorting_files_naming_standard.md`) | `catalogue/ticker=BTC/timeframe=1h/catalogue.parquet`, `labels/ticker=BTC/timeframe=1h/labels.parquet` | `BTC_features_1h.parquet` — siblings that no listing orders by granularity; a slot as a partition value; a Parquet file in the asset's folder |
| CSS | BEM `block__element--modifier`, the class named for what it marks | `frame__head`, `pill--active`, `final-holdout` | `.red`, `.diag` |
| JavaScript functions at file scope | lowerCamelCase, verb from the closed list `build<Object>` (returns a DOM node), `render<Section>` (writes into the page), `format<Value>` (value → string), `append<Child>` (mutates a parent), `select<Target>`, `init<Component>`, `fetch<Object>` (network, returns a promise); a quantity or a descriptor carries no verb | `buildMeter`, `renderStrategy`, `formatBytes`, `appendCell`, `fetchRunRecord`, `mean`, `validationFolds` | `makeTable`, a bare noun for a builder (`cell()`, `sparkline()`) |

Constants that carry a numeric quantity — a count, a rate, a duration, a
size, an interval — are named `<OBJECT>_<ROLE>_<PARAMETER>_<UNIT>`, and the
unit is explicit — `_BARS`, `_MINUTES`, `_MS`, `_SECONDS`, `_DAYS`, `_ROWS`,
`_FOLD_ID`, `_RATE`, `_COUNT` — unless the name already says what is counted
(`MINIMUM_TRADES_PER_VALIDATION_FOLD`); a setting handed to a tool as text carries its unit in the value, not in the
name (`DUCKDB_MEMORY_LIMIT`, a size DuckDB reads with its unit). Enumerations, paths and names carry no
unit; a collection whose values are quantities keeps theirs
(`TIMEFRAME_DURATION_MS`, `FOLD_BOUNDS_MS`, `VALIDATION_FOLD_IDS`). No name is
invented just to satisfy the schema. The parameter word follows the mechanics
— `SPAN` for an exponential smoothing,
`SMOOTHING_PERIOD` for a recursive mean, `LOOKBACK` for a real rolling
window, `HORIZON` for the future of a label, `INTERVAL` for a sampling step. A
parameter carried by a term of the feature catalogue (`("exponential_smoothing", 20)`) is the
descriptor's own and is never copied into a named constant: the record is the
one place the number lives.
A compact timeframe token inside an identifier (`equity_1m`, `ohlcv_1m_canonical`) and as the value of a
partition `timeframe=<timeframe>` is the timeframe vocabulary of code and schema; the slot
standard governs the file names of the asset's folder only.
Domain abbreviations (OHLCV, UTC, OOS, HPO, XGBoost) stay
and are spelled out on first use in the documentation; a popular indicator name — ATR, RSI, EMA,
SMA, MACD, Bollinger — is provenance, so it lives in the `historical_aliases` of the record of what
it denotes and in prose, never in an identifier, a key or a column; local ones (`N`, `W`,
`TF`, `MIN`, `MAX`, `K`, `XGB`) never cross a function boundary. A one-letter
name is legal because of its semantic role, never merely because it is local:
loop indices, the symbols of a published equation inside its tight kernel, and
SVG geometry may stay short — a domain object (a ticker, an asset, a status
payload, a strategy, a metrics block) carries its semantic name even inside a
function. Write
"QuantConnect Lean" on its first use in a file, code comments included, and "Lean" afterwards. British spelling
throughout the prose (`-ise`, `-isation`); language keywords keep their own spelling. At an
external-format or external-library boundary the external vocabulary wins
inside the call that speaks it, and project names begin at the return value.
The boundaries, each with the file that owns it: the Lean tree
(`module_data/lean.py`), the Binance and Bybit REST parameters
(`download_binance.py`, `download_bybit.py`, and `module_data/config.py` for the venue constants that carry the REST word `KLINE`), xgboost and optuna
(`module_ml/model.py`, `module_ml/hpo.py`), numpy (every module that computes),
argparse (`module_data/config.py`, `module_features/config.py`, `module_ml/config.py` — the one parser, twice by extraction —,
`module_features/sub_module_serpentine_search/promote.py` and every `module_<domain>/sub_module_terminal/terminal.py`, for their `-h`, `--help` and, where a terminal names assets, the ones the launcher gives it), DuckDB SQL (every module that queries), Hive's
`key=value` partition segments (every `config.py` that builds a partition), the SVG
and DOM attributes (every `*.js` of `module_monitoring`), docker compose (`Makefile`,
`docker-compose.yml`), tmux (`Makefile`), `urllib` (both downloaders), a stage's
command line over `subprocess` (`record.py`), each vendor's command line over `subprocess` (`module_skills/sub_module_scalability_crawler/crawl.py`, named in `module_skills/sub_module_scalability_crawler/vendors_for_crawling.toml`), TOML (that file, read by `crawl.py` and by the canon's terminal), a workbook's XML parts inside its zip (`module_skills/sheet.py`, the one reader of `module_skills/skills_sheet.xlsx`), the gum command line over `subprocess` (every `module_<domain>/sub_module_terminal/tui.py`, the terminals' one file), the shell's `NO_COLOR` and `TERM` (each of their `config.py`, plain output), `http.server` (`module_monitoring/serve.py`), the `make` command line over `subprocess` (every `module_<domain>/sub_module_terminal/terminal.py`, the targets its actions start — the Makefile alone speaks tmux and docker compose), and the file listing of the four pipeline stores
(`record.py`). A
boundary is an exception the conventions name, not an inconsistency they
tolerate.

## Rejected vocabulary

The rejected vocabulary stays as a list of words that steers the repository
toward a lower level of vectors, guiding AI agents toward useful embeddings for
solving problems in a concrete and minimally correct way. No check gates
it. The last column of the grammar table holds the forms bound to one
rule and the register's `never` columns the synonyms bound to one concept; this
list gathers the words bound to neither, and repeats the few the register
already binds that are worth steering away from on sight.

- **directories and path segments:** `src`, `core`, `lib`, `common`, `utils`,
  `helpers`, `manager`, `service`, `assets`, `artifacts`, `data`, `db`,
  `database`, `raw_data`, a lowercase ticker folder, a venue symbol as a folder;
  `repository_module_<domain>`, a numbered package directory
- **module and file stems:** `module_compose`, `module_docker`,
  `module_capsule`, `module_asset`, `module_viz`; `dashboard.py`, `proxy.py`,
  `server.py` beside `serve.py`; a strategy file per asset, a parameters file
  per stage, an `export` stage; a module named for
  a cloud resource (`module_s3`, `module_ecs`, `module_eventbridge`); `worker`,
  `processor`; `common`, `shared`, `lib` as a repository or a package for what
  two modules share
- **function verbs:** `read_`, `probe_`, `spool_`, `iter_`, `run_`, `compute_`,
  `_factory`; in JavaScript `load`, `poll`. The stem is rejected as a **verb**: a
  function named for a domain noun the register carries is not one, which is why
  `run_dir()` and `run_payload()` stand — a run is the object of
  `module_skills/skill_glossary.md` § Run record — and why `write_venue_spool()` stands, its
  verb being `write` and its spool the CSV the register names
- **key names:** bare `lag`, `age`, `usage` — without the subject and the unit —
  `mem`, `cpu_pct`, a bare duration for how long a container has been up, a
  hash, `weight` as a Y column, `_ts` on a UTC string
- **interface words:** `online` / `offline`, `alive`, `healthy`, `running` for
  an endpoint, `RAM`, `RSS`, `load`, `utilisation`, `freshness`, `boot`;
  `pill`, `chip`, `tile`, `stat` for a badge; `badge--off`, `status--red`, a
  coloured row; `mobile`, `tablet`, `phone`, `responsive`, `breakpoint`
- **tool and process words:** `-f` or `COMPOSE_FILE` on the compose line, a
  second compose file; `8900` as the
  page's address in a document, a command or a comment — the host port is measured, the
  page's address the one `make on` prints (`module_skills/skill_asset_containers.md`
  § The topology). `CONTAINER_PORT` is a different fact and may be written as itself: the
  port a server listens on inside its own namespace, and the left-hand side of a
  reader's own forward; `TODO`, `FIXME`,
  `XXX`, `HACK`; test suite, linter, coverage gate, CI, workflow, hook,
  code generator, framework; `authority`, `single source of truth`; `one-shot` for a
  one-off — an external API's own parameter spelling is that API's, not ours
  (§ Canonical vocabulary, the external-vocabulary boundary); `cloud-ready`, `AWS-ready`, `cloud-native`; `s3://` in a path
  constant, an adapter for a cloud that is not there; a second compose file, a
  second Makefile, a hand-edited derived artifact

## The default choice

For every new change, prefer **the smallest, most modular and most obvious
implementation that correctly closes the full pipeline.**

**A skill belongs to the module whose responsibility it describes.** A rule
about one module lives in `module_<name>/skills/`; a rule that crosses modules or
governs the project lives in `module_skills/` — the canon; a module's orientation
is its `README_module_<name>.md`. Each is written exactly once, the location
follows ownership, and there is no second copy to drift. Every rule is a row of one
sheet, `module_skills/skills_sheet.xlsx`, with a `rule_id` a document cites it by;
`make skills-sync` renders the rows into the `skill_*.md` beside what each governs
and the register into `module_skills/skill_glossary.md`, and no generated document is
edited by hand. `module_skills/README.md` is the index — it links to every skill,
cross-cutting and module-owned alike, restates none of them, and keeps the canon's
prose that is no rule.

`module_skills/skill_asset_containers.md` is the worked example of the cross-cutting
boundary: the one image, the four services — the three runners and `dashboard` —
the Makefile fan-out, the ceilings and the store mounts each service is given
are a contract between the infrastructure and all four runtime modules at once, so it belongs
to none of them and stays in the canon.

A **sub-module** is the one boundary in this shape: `sub_module_<subject>/` inside
the module, or the canon, that owns it, with its own `config.py`, its own `main()`
and no part in the chain's dataflow. It exists three times, so it is a convention:
the directory grammar above carries its row, and a fourth is written to it rather
than argued again. The
scalability crawler is `module_skills/sub_module_scalability_crawler/`, nested in
the canon because it reads files against the canon, and owned by no
runtime module because the sheet may mark a file of any of them. A module's terminal
is `module_<domain>/sub_module_terminal/`, one per module — the canon's among them —
nested in the module whose targets it starts: it computes nothing, imports its own package alone (D02)
— and where that module's `config.py` is not standard library, as
`module_features`' is not, imports it not at all and carries registered copies of
the descriptors it reads — and it runs on the host's `python3` and gum, starting
every stage through `make`. Every one of them shares one `tui.py`, by extraction,
and one skill, `module_skills/skill_tui_designer.md`, which crosses them and
therefore sits in the canon; what each screen holds is its orientation,
`README_sub_module_terminal.md` beside its code. The serpentine search is `module_features/sub_module_serpentine_search/`, nested in
the module whose feature set it moves: a hand's research outside the chain, an action module
with its `main()` for each action of a hand — the turn and the promotion — and a promotion
that writes the two files the chain reads, `<TICKER>_feature_set.json` and
`<TICKER>_barriers.json`; the question a turn leaves is answered by `module_ml/score.py`, a
stage of the module that fits, because a state is scored by the code that scores the chain.

## The shape — what holds the project together

The shape is four modules and a launcher: one image, the stores explicit and
outside compute, the orchestration outside the modules, the contracts between
modules as files, the asset as a parameter, the recorder measuring what a stage
wrote — and nothing of a cloud
(`module_skills/README.md` § The Pre-AWS mapping, What the shape holds). The conditions below hold at every commit; a change that breaks one
is wrong.

| # | holds |
|---|---|
| D01 | the root holds no data, feature or ML logic: its only Python is `record.py`, which measures every stage of a recorded run from outside and writes the run index, and the canon's Python is its own tools — the sheet's reader and sync, the table of CONFIGURABLES records, the crawler and its terminal — which render the tree's rules and measure the tree against them |
| D02 | `git grep "from module_"` inside a module package finds only that package: no module imports another |
| D03 | a module's skills live under that module and nowhere else; a rule that crosses modules lives in `module_skills/`; every skill is rows of `module_skills/skills_sheet.xlsx`, rendered by `make skills-sync` and never edited by hand |
| D04 | a fresh `git clone` followed by `make all` and `make on` is a working project |
| D05 | one `docker-compose.yml` carries the whole topology, and one `Makefile` the stage order and the fan-out |
| D06 | no module writes into another's source tree: what a stage writes lands in a store |
| D07 | an asset is `ASSET` on the make line and `--tickers` at the process boundary — never an image or a service definition of its own |
| D08 | no sub-module is a module: `module_skills/sub_module_scalability_crawler/` and `module_skills/sub_module_terminal/` are the canon's, `module_features/sub_module_serpentine_search/` the feature module's, and each `module_<domain>/sub_module_terminal/` its module's — each with its own `config.py` and `main()`, none in the chain's dataflow; the serpentine search's promotion writes the two files the ML chain reads, by a hand's choice |
| D09 | artifact names and keys move only with the register: every key of every payload has a row of the register table of `module_skills/skills_sheet.xlsx`, rendered into `module_skills/skill_glossary.md`, and a key added, dropped or renamed moves that row in the same commit. The feature layer's contract file `<TICKER>_catalogue.json`, every family's `schema.json`, the `catalogue` block in `features_status.json` beside `assets[].row_count_by_timeframe` and `assets[].serpentine_search`, the serpentine search's state, ledger, profile, question and answer, the `ticker` key in every row of `data_status.json`, that snapshot's own measurement set, and `run_records/index.json` — `generated_at_utc`, `runs[]` with `run_id` and `records` — are each registered there |
| D10 | determinism is unchanged: the caps, the seed, the pinned orders (`module_skills/skill_determinism.md`) |
| D11 | parity: the chain on a frozen copy of the raw store reproduces every file of `store/assets_artifacts/` and `store/trials/` and the three computational snapshots, normalised, byte for byte against the reference manifest `README.md` § Parity, the raw store's own manifest taken before the chain runs. A day the download adds past the frozen copy changes the raw tree, the two venue families, the canonical family and `data_status.json` and nothing else — every later stage reads the research window alone; `data_status.json` describes the whole canonical series and moves with every top-up by design. The files a hand drafts — `<TICKER>_serpentine_search_profile.json` and, once promoted, `<TICKER>_feature_set.json` and `<TICKER>_barriers.json` — stand outside it: no stage of the chain derives them. So do the serpentine search's own files, a hand's stage rather than the chain's: `<TICKER>_serpentine_search.json`, where the search stands at a round boundary, `<TICKER>_serpentine_search_trials.jsonl`, its ledger of scored states, and the asset's partition of `score_trials` — their proof is that a search reset and run again over the same inputs gives the same bytes in all three, and that a search stopped and run again ends on the same state and ledger. The one exception is named: `score_trials` may then hold a study twice, because a stop between a study's lines and the answer after them leaves lines the rerun appends again (`score.hpo_results()`). The state and the ledger are **tracked** all the same, because `features_status.json` reads them and is inside the proof: a clone that could not rebuild them could not reproduce the snapshot that quotes them, and the parity of the chain would rest on a file nobody shipped. A change that reshapes one of the chain's files re-bases its line and no other — the gate is then a field-level before/after comparison, every kept field byte-identical, beside the lines held fixed |
| D12 | zero cloud mechanisms: nothing in the tree reaches a service off this host but two calls — the venues' public endpoints the two downloaders read, and the one active command line of the crawler's `vendors_for_crawling.toml`, in its user's own login, outside the chain and gating nothing — and the trial ledgers are the partitions `hpo_trials_jsonl()` and `score_trials_jsonl()` build in `module_ml/config.py` under `STORE_TRIALS_DIR`, appended through `hpo.log_trials` — the family `hpo_trials` by `module_ml/hpo.py` alone, the family `score_trials` by `module_ml/score.py` alone — and never a network location; the four pins of `requirements.txt` are the project's, and a fifth moves this line in the commit that adds it |
| D13 | `features_status.json` is written by `module_features.status` |
| D14 | every object of `module_skills/skill_glossary.md` § Twice by extraction is marked `# twice by extraction` directly above its own definition — one marker per object, never one above a block of objects — and changed on every side at once |
| D15 | the tracked remnant of the artifacts store, in the asset's folder `ticker=<TICKER>/` — `<TICKER>_README.md`, `<TICKER>_parameters.json`, once drafted `<TICKER>_serpentine_search_profile.json`, once a search has run `<TICKER>_serpentine_search.json` and `<TICKER>_serpentine_search_trials.jsonl` (D11), and, once promoted, `<TICKER>_feature_set.json` and `<TICKER>_barriers.json` — and the four snapshots are tracked, so a fresh clone opens on real numbers and on the profile the last search was run under |
| D16 | the fan-out, the serpentine search's loop and its detached twin run through `docker compose run --rm`, one one-off container per step; nothing is `exec`'d into a resident |
| D17 | `skills_status.json` and the crawler's reports are written by the crawler alone — `module_skills.sub_module_scalability_crawler.status` the one writer of the snapshot, `crawl` the one caller — the snapshot a row per controlled file of the sheet's files matrix, neutral on the branch: every file `pending`, no report; the reports untracked, reset by every crawl |
| D18 | the crawler gates nothing: no target of the chain, no service and no merge depends on it; it writes only its reports and its snapshot, and a hand alone starts it |
| D19 | a module's terminal — the canon's among them — imports the standard library and its own package alone, and starts every stage through `make`: its import lines name no module of this tree but `from . import` and `from .. import`, and no third-party package — `module_features/config.py` imports `.indicators`, and numpy with it, and is never imported here, so the features terminal carries registered copies of the descriptors it reads — and no terminal runs `tmux` or `docker`, the one tmux word in any of them being a make target's name. The one file a terminal writes is `<TICKER>_serpentine_search_profile.json`, the features terminal's draft; a hand alone runs a terminal, one action per run, and none of them gates anything |

## Skills absent here, described

Skills the Pre-AWS seats imply and this tree does not hold: each placed by
ownership as § The default choice places every skill, described today where its
last column says, and written when its one condition holds. Two rows this shape
answered are no longer here: the status prefix — the snapshots live in
`store/status/`, tracked, the crawler's reports beside them untracked
(`module_skills/skill_glossary.md` § Stores) — and the image contents — the `Dockerfile`
carries the pins and each service mounts the stores it touches, the `dashboard`
those it serves, read-only (`ASSET-CONTAINERS-A-SERVICE-MOUNTS-ONLY-THE-STORES-IT-TOUCHES`).

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
