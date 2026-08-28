# AGENTS — the contract of this repository

The governing contract for every change, human or agent. Read the repo in
this order: **AGENTS.md → module names → module_guidance → code.**
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
- **Main = clean working logic.** No test frameworks, security layers,
  validation frameworks or precautionary guards. What stays are the guards
  the mathematics requires: causality invariants, arithmetic preconditions,
  the fail-closed export. Thread caps (`nthread=1`, `OMP_NUM_THREADS=1`) are
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
generated state. Four project modules — three runtime modules, in the order
the data moves through them, and one non-runtime module:

```
module_data/         sources → normalised raw 1m → ONE canonical DuckDB → published parquet
module_ml/           canonical dataset → X, Y → search → model → research simulation
module_monitoring/   presentation of what the two modules measured about themselves
module_guidance/     the contract's companions: methodology, skills, the register
```

`module_guidance` never participates in runtime imports or dataflow. A new
`module_<domain>` is justified only by a distinct responsibility with a stable
input/output boundary; until then the owning module is extended.

Regular, predictable, symmetrical, easy to scan — the structure should be
recognisable by eye before it is parsed (neuro-optical consistency):

- one obvious responsibility per module; no wrappers without logic of their own;
- analogous names for analogous objects (`download_binance.py` ↔
  `download_bybit.py`, `store_research_artifacts/<TICKER>/<artifact>.<ext>`, `ml-<stage>` ↔
  `docker-ml-<stage>` targets); each computational module (`module_data`,
  `module_ml`) measures its own domain state in `status.py`, and
  `module_monitoring` presents their snapshots;
- **the kind comes first, so siblings sort together.** A listing is read by
  eye before it is parsed: `module_data`, `module_ml`, `module_monitoring`,
  `module_guidance`, then `store_db`, `store_raw_1m`,
  `store_research_artifacts` — two blocks, not seven scattered entries. If
  renaming would put things of one kind next to each other, rename them.
  Checked with `ls -1d */`: one kind, one contiguous block;
- short, predictable paths, built only in a module's `config.py` — never
  assembled at the point of use; one asset is one folder,
  `store_research_artifacts/<TICKER>/`, one file per distinct artifact
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
standard domain terminology. A glossary confirms meaning; it must not be
required to decode an obscure name.**

One concept, one name — in the code, in the artifacts and in the interface. The
register is `module_guidance/glossary.md`, and a new name enters it in
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

Every layer has a closed grammar, the way CSS has BEM. A name is **derived**
from its layer's grammar, never invented:

| layer | grammar | in this repo | what it forbids |
|---|---|---|---|
| constants | `<OBJECT>_<ROLE>_<PARAMETER>_<UNIT>` | `RSI_WILDER_SMOOTHING_PERIOD_BARS` | `RSI_N` |
| external I/O functions | `<verb>_<object>`, verb from the closed list `fetch_` (network), `load_` (storage → memory), `write_` (persist), `parse_` (bytes → values) | `fetch_klines`, `load_xy`, `write_parquet`, `parse_zip` | `get_`, `process_`, `handle_` |
| conversions | `to_<representation>` | `to_class`, `to_json_safe` | ambiguous `convert` |
| composite constructors | `build_<object>` | `build_x` | `make_stuff` |
| functions that *are* a quantity | no verb — the name is what it returns | `rsi`, `atr`, `sharpe_annualised`, `triple_barrier` | `calculate_rsi` |
| pure descriptors | a noun phrase naming the returned object | `symbol`, `artifact_dir`, `fold_bounds` | `get_fold_bounds`, `fetch_symbol` |
| populations of rows | `<population>_set` / `_window` | `training_set`, `scoring_set`, `prediction_window` | `get_train_indices` |
| report fragments | `<section>_block` | `sample_block`, `hpo_block` | `make_sample_dict` |
| quantities | `<what>_<unit>` | `fold_start_ms`, `equity_1m`, `returns_15m` | `n_min`, `off` |
| index arrays | `<population>_rows` | `training_rows`, `window_rows`, `scoring_rows` | `tr`, `wi`, `oi` |
| booleans | `<subject>_<predicate>`, stating the condition that is true; a function that asks takes `is_` | `entry_observable`, `label_valid`, `is_full_utc_day()` | `flag`, `ok`, `check` |
| artifact keys | snake_case, the same word as the identifier that produced it, suffixes `_count`, `_ms`, `_pct`, `_utc` | `scored_row_count`, `generated_at_utc` | a separate vocabulary for JSON |
| features | `<computation>[<parameter>]_<timeframe>` | `ema20_minus_ema50_over_atr14_4h`, `centered_rsi14_1h`, `range_position_20_15m` | `feature_3`, `f_rsi` |
| stored columns | the quantity for OHLCV, `<what>_<unit>` for anything derived, `<subject>_<predicate>` for a boolean — and a column and the key that publishes it carry **one** name | `timestamp_ms`, `ffill_bars`, `zero_volume_bars`, `binance_valid` | `n_ffill`, a column and key that disagree |
| directories | `<kind>_<detail>/` | `module_*`, `store_*` | a kind scattered through the alphabet |
| CSS | BEM `block__element--modifier` | `frame__head`, `pill--active` | `.red` |

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
external-format boundary the external vocabulary wins: the raw tree is the
QuantConnect Lean layout (`cryptofuture/<venue>/minute/<symbol lowercase>/`,
`YYYYMMDD_trade.zip`) and the adapter speaks Lean's own terms — a boundary
exception the conventions name rather than an inconsistency they tolerate.

## The default choice

For every new change, prefer **the smallest, most modular and most obvious
implementation that correctly closes the full pipeline.**

Project-specific agent instructions live in `module_guidance/` — the
only other place agent guidance may exist in this tree. Its files are
kind-first: the naming register (`glossary.md`), the skills (`skill_*.md`) and
the methodology documents — `methodology_data.md` (how the canonical dataset
is built) and `methodology_ml.md` (the research layer, equation by equation,
with the citations). A module-specific guidance subfolder is created at the
third module-specific document, not before.
