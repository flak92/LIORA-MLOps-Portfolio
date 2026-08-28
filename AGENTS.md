# AGENTS — the contract of this repository

The governing contract for every change, human or agent. Read the repo in
this order: **AGENTS.md → module names → module_skills → code.**
(README is general information, not part of the working path.) If a change
conflicts with this file, the change is wrong.

## Values

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
  One GitHub Actions workflow carries the rule past the clone: a push to `main`
  regenerates `module_monitoring/files_and_folders_visualisation.html` and commits it, because a
  picture of the files that a human has to remember to refresh is a picture
  that is quietly wrong.
- **Main = clean working logic.** No test frameworks, security layers,
  validation frameworks or precautionary guards. What stays are the guards
  the mathematics requires: causality invariants (`indicators.asof_index`) and
  arithmetic preconditions (the full canonical grid in `labels.load_research_1m`,
  the aligned decision grids of the arrays `dataset.load_xy` joins by position,
  the basket-wide ingest, the download that aborts on a short post-listing day).
  A check that could only fail on a stale artifact from another run is not one
  of them. The single workflow in `.github/` does **exactly two** things, and the
  count is the rule: it regenerates one artifact whose whole purpose is to equal
  the tree, and it checks the tree against the names this project enacted. Both
  are the contract keeping itself true, neither asserts anything about the
  mathematics, and neither adds a dependency. A test suite, a linter, a coverage
  gate or a merge block does not belong here — and a third thing, or a second
  workflow, is the signal that this one has been misread. Thread caps (`nthread=1`, `OMP_NUM_THREADS=1`) are
  part of correctness, not a setting.
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
generated state. Five project modules — three runtime modules, in the order
the data moves through them, and two non-runtime modules:

```
module_data/          sources → normalised raw 1m → ONE canonical DuckDB
module_ml/            canonical dataset → X, Y → search → model → research simulation
module_monitoring/    presentation of what the two modules measured about themselves
module_skills/        the contract's companions: the act, the register, the methodologies, the skills
module_visualisation/ the tracked tree → the repository's own picture, regenerated on every push
```

`module_skills` and `module_visualisation` never participate in runtime imports
or dataflow. `module_visualisation` reads the git index, never the canonical
dataset, which is what keeps it a separate responsibility rather than a second
job for `module_monitoring`. A new
`module_<domain>` is justified only by a distinct responsibility with a stable
input/output boundary; until then the owning module is extended.

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
- **the kind comes first, so siblings sort together.** A listing is read by
  eye before it is parsed: `module_data`, `module_ml`, `module_monitoring`,
  `module_skills`, then `store_assets_artifacts`, `store_db`,
  `store_raw_1m` — two blocks, not seven scattered entries. If
  renaming would put things of one kind next to each other, rename them.
  Checked with `ls -1d */`: one kind, one contiguous block;
- short, predictable paths, built only in a module's `config.py` — never
  assembled at the point of use; the one exception is an external format's own
  file names, built by its adapter (`module_data/lean.py` for the Lean tree) —
  and the browser, which has no config module and fetches its two snapshots by
  literal name (`data.js`, `ml.js`); one asset is one folder,
  `store_assets_artifacts/<TICKER>/`, one file per distinct artifact
  responsibility. The artifact folder is the ticker in capitals, the raw tree
  is the symbol in lower case because Lean demands it — that difference is a
  boundary, not an inconsistency to tidy away. A top-level path constant
  begins with the exact canonical root token, so the name predicts the
  directory: `STORE_RAW_1M_DIR` → `store_raw_1m/`, `MODULE_MONITORING_DIR` →
  `module_monitoring/`;
- one convention per language: BEM in CSS, snake_case in Python and JSON,
  the same hierarchy everywhere, no accidental exceptions.

## Canonical vocabulary

**Names must be self-explanatory before they are project-specific. Prefer
established software-engineering terminology over project-specific synonyms: if
a concept already has a widely recognised name, use that name — in code, in
documentation, in the skills and in the interface alike — and do not invent
local terminology for a standard concept. A glossary confirms meaning; it must
not be required to decode an obscure name.**

One concept, one name — in the code, in the artifacts and in the interface. The
register is `module_skills/glossary.md`, and a new name enters it in
the same commit that introduces it. The fold vocabulary it fixes: `fold` (one
chronological segment), `WARMUP_END_MS` (before any decision is allowed),
training rows (everything that finished before the evaluated block), `purge`
(training events overlapping that block, removed by `event_end_ts <=
oos_start`), `embargo` (width zero here — forward chaining needs none) and
`oos` (the evaluated block); `VALIDATION_FOLD_IDS` are F2–F4 and carry the
data-driven selection of model hyper-parameters and the entry edge threshold —
the barrier width, the horizon, the cost and the feature set are frozen a
priori, not selected — and `FINAL_HOLDOUT_FOLD_ID` is F5, which only
evaluates. The word "test" never names a fold.

And one name, one concept. A name that could denote two things **in the same
scope** is renamed until it denotes one. The scopes are enumerated, so the rule
can be applied without argument: make targets, compose services, tracked paths,
and Python symbols within a module. Two objects sharing a name in *different*
scopes are not a collision — the compose service `dashboard` and the make target
`monitoring-dashboard` are addressed by different tools and never appear in one
listing. This is the rule the act already leaned on twice without writing it
down: `db` is legal where nothing else could be meant (row 3), and `status`
became `data-status` the moment `ml-status` existed (row 13).

**Derived, never drafted.** Every derived artifact is generated from source and
config, and never hand-edited; a hand edit to a generated file is a violation.
`module_monitoring/files_and_folders_visualisation.html` is derived from the git
index and `module_visualisation/visualisation_config.json`, and
`make visualisation-check` is what makes this enforceable instead of hoped for.

**Prefer generative structure over repeated project knowledge.** When a family —
assets, venues, timeframes, paths, artifact files, payload keys, pipeline stages
— is governed by one canonical definition, derive the repeated representations
from that owner rather than copying the same list or naming decision into
several files; adding the next member of an established family should need one
local definition and predictable derivation. Keep it stupid simple: no
generators, registries, metaprogramming or abstraction layers for a one-off
value. Generation earns its place only when it removes duplicated knowledge and
shortens the extension path, and it is a preference the repository states rather
than a grammar it can check — `module_skills/act_naming_conventions.md` records
it among the rules no grep can settle.

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
| module-private helpers | a leading `_` on the name its layer's grammar gives | `_rounded`, `_pnl_block`, `_utc_ms` | a public name for a helper nothing outside imports |
| CLI entry | `main()` — one per stage module, returning the exit code | `main` | `run`, `cli`, `entrypoint` |
| quantities | `<what>_<unit>` | `fold_start_ms`, `equity_1m`, `returns_15m` | `n_min`, `off` |
| index arrays | `<population>_rows` | `training_rows`, `window_rows`, `scoring_rows` | `tr`, `wi`, `oi` |
| booleans | `<subject>_<predicate>`, stating the condition that is true; a function that asks takes `is_` | `entry_observable`, `label_valid`, `is_full_utc_day()` | `flag`, `ok`, `check` |
| artifact keys | snake_case, the same word as the identifier that produced it; a count is `<what>_count`, a quantity with a unit `<what>_<unit>`, a share `_pct`, a formatted UTC string `_utc`, epoch milliseconds `_ms` | `scored_row_count`, `ffill_bars`, `coverage_pct`, `generated_at_utc` | a separate vocabulary for JSON; a bare plural (`gaps`) or an adjective (`ambiguous`) as a count; `n_`; `ret` for return |
| features | `<computation>[<parameter>]_<timeframe>` | `ema20_minus_ema50_over_atr14_4h`, `centered_rsi14_1h`, `range_position_20_15m` | `feature_3`, `f_rsi` |
| stored columns | the quantity for OHLCV, `<what>_<unit>` for anything derived, `<subject>_<predicate>` for a boolean — and a column and the key that publishes it carry **one** name | `timestamp_ms`, `ffill_bars`, `zero_volume_bars`, `binance_valid` | `n_ffill`, a column and key that disagree |
| Makefile targets | `<module>-<stage>` for a stage of a runtime module, `docker-<module>-<stage>` for its container twin; only the lifecycle targets go bare (`all`, `setup`, `help`, `docker-build`, `docker-up`, `docker-down`) | `data-ingest`, `ml-hpo`, `docker-ml-train` | a bare stage (`ingest`), a twin named after the tool (`docker-run`) |
| directories | `<kind>_<detail>/`; a raw store names its granularity with the compact timeframe token, `store_raw_<timeframe>/` | `module_*`, `store_*`, `store_raw_1m` | a kind scattered through the alphabet, a store spelling its timeframe in sorting slots |
| artifact files of one timeframe family | `<asset>_<artifact>_<timeframe-slot>.<ext>`, slots per the standard `ss-mm-hh-dd-MM` (the act, § timeframe slots) | `BTC_features_ss-15-hh-dd-MM.parquet`, `BTC_features_ss-mm-04-dd-MM.parquet` | `BTC_features_15m.parquet` — siblings that no listing orders by granularity |
| CSS | BEM `block__element--modifier`, the class named for what it marks | `frame__head`, `pill--active`, `final-holdout` | `.red`, `.diag` |
| JavaScript functions | lowerCamelCase, verb from the closed list `build<Object>` (returns a DOM node), `render<Section>` (writes into the page), `format<Value>` (value → string), `append<Child>` (mutates a parent), `select<Target>`, `init<Component>`; a quantity or a descriptor carries no verb | `buildMeter`, `renderStrategy`, `formatBytes`, `appendCell`, `mean`, `validationFolds` | `makeTable`, a bare noun for a builder (`cell()`, `sparkline()`) |

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
inside the call that speaks it, and project names begin at the return value:
the raw tree is the QuantConnect Lean layout and `module_data/lean.py` speaks
Lean's own terms; the same holds for the exchange REST parameters, xgboost,
optuna, argparse, the SVG attributes and DuckDB SQL — every boundary is a row
of the act's *External vocabularies* table, an exception the conventions name
rather than an inconsistency they tolerate.

## The default choice

For every new change, prefer **the smallest, most modular and most obvious
implementation that correctly closes the full pipeline.**

Project-specific agent instructions live in `module_skills/` — the
only other place agent guidance may exist in this tree. Its files are
kind-first and are read in listing order, starting with the act: the enacted
names (`act_naming_conventions.md`), the naming register (`glossary.md`), the
methodology documents — `methodology_data.md` (how the canonical dataset is
built) and `methodology_ml.md` (the research layer, equation by equation, with
the citations) — and the skills (`skill_*.md`), among which
`skill_self_explaining_naming.md` carries the check for every grammar row. A module-specific guidance subfolder is created at the
third module-specific document, not before.
