# module_ml — the catalogue, the bars and the canonical series in, a research result out

The front door of this module: what it is, where its responsibility stops, and
how to run it. The method itself — every equation, every fold, every citation —
is `skills/methodology_ml.md`, and the layer's rules are
`skills/skill_methodology_ml.md`; neither is repeated here. *The repository
shows the destination, not the road*.

`module_ml` reads one asset's feature catalogue, its bars and its canonical 1m
series and produces a research result: X from the asset's feature set,
triple-barrier labels, a hyper-parameter search, purged walk-forward XGBoost
predictions and a gated strategy simulation. Each tabular result is the asset's
partition of a table family, `schema.json` at the family's root; each other
result is a file in the asset's own folder, `ticker=<TICKER>/`. Outside the chain
it answers the serpentine search's questions: the states one
`<TICKER>_score_request.json` names are scored on the validation folds and
answered in `<TICKER>_score_response.json`.

## Where the responsibility stops

```
<TICKER>_catalogue.json + catalogue + bars + ohlcv_1m_canonical → labels → search → model → strategy
    → ml_status.json, <TICKER>_README.md
```

It begins at the feature layer's contract, `<TICKER>_catalogue.json`, the
catalogue partitions it names, the `bars` partitions and `ohlcv_1m_canonical` —
every one read as a file — and asks nothing about where a minute came from or how
a column was computed. Downloading, venue selection, forward fill and provenance
belong to `module_data`; the bars of the register, the catalogue, the serpentine
search over the feature set, the barrier geometry and the hyper-parameters, and its
promotion belong to
`module_features`; presentation of the results belongs to `module_monitoring`.
This module scores a state it is asked about and chooses none.

Every stage here is a one-off process addressed as
`python -m module_ml.<stage> --tickers <TICKER>` (under `make` or compose, which
set the three `STORE_*_DIR` this module reads — the artifacts store, the trials
store and the status store): it reads files, writes files and holds nothing
between runs, so the four stages of `ml-all` above `status`, and `score` outside
the chain, already have the shape of asset-scoped compute that receives a
finished catalogue and leaves artifacts in the asset's folder and partitions,
while `status` is the basket-wide fold over them. The direction:
`module_skills/skill_pre_aws_solution.md`.

What an operator may set is a record of `CONFIGURABLES` in `config.py`, each
value written once there and read by name by the constant below the block;
`ml_status.json` publishes the records beside the assets, and a document names a
record rather than its value. `LABEL_BARRIER_TRUE_RANGE_TIMEFRAME` is the one
timeframe this module names instead of reading it through the contract: the
timeframe whose last closed bar sets the barrier width, which must be an entry of
the hierarchy the contract lists — its duration is read there. The decision
timeframe, the hierarchy, the warm-up and the catalogue's columns arrive per asset
in `<TICKER>_catalogue.json`.

## Stages

Run in order; `make ml-all` runs them, each stage in a one-off container of the
`ml` runner, and a single stage is its own `ml-<stage>` target in the same
runner, or the one-off process above run by hand in a shell that exports those
variables (`module_skills/skill_glossary.md` § Stores). The four stages above `status`
fan out one process per asset, `JOBS` at a time — one unless the make line says
`JOBS=n` — with its threads pinned to one; `status` runs once and aggregates the
assets the launcher names — the whole basket.

| stage | target | writes |
|---|---|---|
| labels | `make ml-labels` | the asset's `labels` partition on the decision timeframe the contract names, `labels/ticker=<TICKER>/timeframe=<timeframe>/labels.parquet`, and `labels/schema.json` |
| hyper-parameter search | `make ml-hpo` | `<TICKER>_parameters.json`, and every point its study drew into `hpo_trials/ticker=<TICKER>/hpo_trials.jsonl` of the trials store, with `hpo_trials/schema.json` |
| training | `make ml-train` | `<TICKER>_model_evaluation.json`, and the `oos_predictions` partition, `oos_predictions/ticker=<TICKER>/timeframe=<timeframe>/oos_predictions.parquet`, with `oos_predictions/schema.json` |
| strategy | `make ml-strategy` | `<TICKER>_strategy_evaluation.json` |
| status | `make ml-status` | `store/status/ml_status.json`, the module's `CONFIGURABLES` records beside the assets, and `<TICKER>_README.md` |
| score — outside the chain, the serpentine search's question | `make ml-score`, one process per asset of the basket, `ASSET=<TICKER>` narrowing it to one — and between two turns of the search, by `make features-serpentine-search` | `<TICKER>_score_response.json`: a trial row per state, or a study and its candidate per beam parent; a study's points into `score_trials/ticker=<TICKER>/score_trials.jsonl` of the trials store, with `score_trials/schema.json` |

Every stage runs in a one-off container of the `ml` runner —
`docker compose run --rm -T ml python -m module_ml.<stage> --tickers <TICKER>`,
through the Makefile's `fanout` macro one container per asset, through its
`basket` macro once for `status`. Each stage takes `--tickers`; `status` takes it
too and folds the assets it was told — the launcher passes the whole basket,
which `ASSET=` does not narrow, and every complete asset among them gets its
`<TICKER>_README.md`.

The serpentine search is `module_features`', and so are its targets:
`features-serpentine-search` alternates a turn of the search with `ml-score` while
the turn leaves a question, `tmux-features-serpentine-search` is its detached
twin, `features-serpentine-search-reset` removes an asset's search and its
`score_trials` partition, and `features-serpentine-search-promote ASSET=<TICKER>
PROPOSAL=<n>` copies a proposal's columns into `<TICKER>_feature_set.json` and its
barrier geometry into `<TICKER>_barriers.json`, then reruns `ml-all` for the
asset. That rerun tunes the hyper-parameters anew: the promoted state is
evaluated again on the validation folds F2–F4, F5 is read after them and steers
no parameter, and what is kept is the state, not the model the search evaluated.

## What it writes

```
store/assets_artifacts/labels/ticker=<TICKER>/timeframe=<timeframe>/labels.parquet                    Y on the decision grid of the decision timeframe
store/assets_artifacts/oos_predictions/ticker=<TICKER>/timeframe=<timeframe>/oos_predictions.parquet  the out-of-sample class probabilities, full windows
store/assets_artifacts/{labels,oos_predictions}/schema.json                                           each family's columns, beside its partitions
store/assets_artifacts/ticker=<TICKER>/                                                               the parameters, the two evaluations, the README, the score response
store/trials/hpo_trials/ticker=<TICKER>/hpo_trials.jsonl                                              every point ml-hpo's studies drew, written by ml-hpo alone
store/trials/score_trials/ticker=<TICKER>/score_trials.jsonl                                          every point the studies ml-score ran for the search drew, written by ml-score alone
store/trials/{hpo_trials,score_trials}/schema.json                                                    the one row both trials families share
store/status/ml_status.json                                                                           the status snapshot the dashboard reads
```

One folder per asset, one file per artifact responsibility, and beside it the
asset's partition of every family. The manifest of an asset's research artifacts,
with what each holds, is the Files table of its `<TICKER>_README.md`, written by
`status.py`; the names are registered in `module_skills/skill_glossary.md`
§ Artifacts. Of what this module writes, `<TICKER>_README.md` and
`<TICKER>_parameters.json` are tracked — beside the serpentine search's profile,
state and ledger and, once a hand has promoted one, `<TICKER>_feature_set.json`
and `<TICKER>_barriers.json`, which `module_features` writes and this module
reads — so a folder reads, and rebuilds, without a run; the parameters are tuned
for the promoted state, so they travel together. The README and the parameters
are derived and never hand-edited; the feature set and the barriers are a hand's
decisions, written by the promotion and never derived. The partitions, the two
evaluations, the request and the response and the trials store are not tracked.

## Extending

| what you add | where, and how much | what it changes | the gate |
|---|---|---|---|
| a hyper-parameter | one entry in `HYPERPARAMETER_SEARCH_SPACE` (`config.py`), in xgboost's own spelling, with the kind of its draw — `int`, `int_step`, `float` or `log` — and its bounds | the search space, `best_params`, the `params` of both trials families' `schema.json` — `TRIAL_COLUMNS` is built from the space — and every artifact downstream of a retune; a recorded serpentine search starts over, `best_params` being among its inputs | `ml-labels` and the catalogue's partitions byte-identical; the record's `requires_rerun` names what to run |
| a coordinate of a state's barrier geometry | one entry in `BARRIER_COORDINATE_CASTS` and one in `START_BY_COORDINATE_DEFAULT` (`config.py`), each twice by extraction with `module_features/sub_module_serpentine_search/config.py`, the name in `TRADE_EXIT_COORDINATE_NAMES` too where it moves only a trade's exit, and the one computation that reads it — `labels.label_events()` for the label, `strategy.signals_for_fold()` for a trade; its moves are the search's, in `module_features/sub_module_serpentine_search/` | nothing of `score.py`: a state, its key, its fit identity and its trial row carry the coordinates by the register's names, and `fit_identity()` reads which of them leave the fits alone | with the coordinate at its start value the chain's files are byte-identical; `score.py` still names no coordinate of its own |

## Design rationale

Why each object of this module sits where it does — the answers the naming review asks for
(`SELF-EXPLAINING-NAMING-A-NEW-OBJECT-PASSES-THE-NAMING-REVIEW`) written down, one row per object, analogous pair
or the module's documents; the mapping row it answers to is a row of the mapping table of `module_skills/README.md`
§ The Pre-AWS mapping, cited by its *responsibility* column and never repeated
(`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The frozen experiment of the research layer — its `CONFIGURABLES` records, what an operator may set, each value written once and read by name by the constants below the block: the seed, the fold bounds, the label's barrier scale, the geometry a state starts from, the study's counts and space, the cost, the threshold grid, the trade floor, the trend agreement and the DuckDB ceiling — and one descriptor per family and per file of this module: `labels` and `oos_predictions`, partitioned by asset and decision timeframe, `hpo_trials` and `score_trials`, partitioned by asset in the trials store, and the files of the asset's folder, the catalogue's partitions named by the contract itself. It carries its own copies of the units, the DuckDB ceiling, the store reads and the descriptors of the canonical and bars families, `to_utc_ms()`, `artifact_dir()`, `partition_dir()`, `schema_json()`, `feature_id()`, the `--tickers` parser and `rounded()`, and of the values a state is made of and the two files of the evaluation contract — twice by extraction, each marked so above its definition; it imports nothing of another module: the register, the grid and the warm-up arrive per asset as `<TICKER>_catalogue.json`. | Every stage of the module imports it, nothing else names an artifact path of this module, and `is_artifact_set_complete()` is what `status.py` asks before it folds an asset; being standard library, the terminal imports it too. | A stage reaches a file by descriptor (correlatable artifacts, without a version scheme: `module_skills/skill_pre_aws_solution.md`), so the asset's folder and each family's partitions keep the same paths under `/store/<content>` on whatever disk is mounted there. | STORAGE — research artifacts |
| `dataset.py` | The shared IO of the layer — `load_catalogue()`, the one read of the feature layer's contract per stage, `load_xy()` and `build_xy()` with `load_feature_material()`, `load_label_events()`, `load_feature_columns()`, `load_barriers()` and `barriers_from()` — the one place a horizon token becomes minutes — and `build_x()`; `write_json()`, `load_json()`, `load_jsonl()` and the parquet writer with the schema read off a written partition, twice by extraction, identical in `module_features/dataset.py` (its docstring), and `append_jsonl()`, the append a ledger grows by. | `labels.py`, `hpo.py`, `train.py`, `strategy.py`, `score.py` and `status.py` import it, and it imports `config.py` alone. | It writes to the descriptor it is handed and builds no path of its own, so a file lands where `config.py` says on whatever disk is mounted at `/store`; `build_xy()` reads no file, so `score.py` builds X and Y in process the way a stage does. | STORAGE — research artifacts |
| `labels.py` | LABEL — Y: the triple-barrier events on the canonical 1m path, per asset, the barrier scale the recursive mean of the true range of the barrier's timeframe (`skills/methodology_ml.md` § 5). | It imports `config.py` and `dataset.py`, carries its own copies of `recursive_mean()`, `true_range()` and `asof_index()` (twice by extraction, identical in `module_features/indicators.py` — the label defines its own barrier scale), reads the canonical series and the bars as files and never the catalogue's partitions, and writes the `labels` partition `build_xy()` joins to X by position; `label_events()` is what `score.py` calls again for a state whose label geometry moved. | X and Y are built by two stages and joined by position at the read, in `build_xy()`, so the join happens at the same descriptor paths whatever disk holds them. | COMPUTE — one stage for one asset |
| `model.py` | The xgboost boundary (`AGENTS.md` § Canonical vocabulary): the class mapping, the draw of the search space, fit, predict and the two importances the booster gives — total gain and the SHAP contributions — as pure functions over numpy arrays (its docstring). | `hpo.py` and `train.py`, the two stages that fit, and `score.py`, which fits through `train.fold_evaluation()` and maps the classes with `to_class()`, import it; it imports `config.py` alone. | It reads nothing and writes nothing — `train.py` persists the numbers and not the model — so the same fit under `nthread=1` and a fixed seed runs in whichever container the stage takes (`DETERMINISM-THREAD-CAPS-FROZEN-AT-ONE`, `DETERMINISM-SEED-IS-FIXED-AND-SEARCH-SEQUENTIAL`). | COMPUTE — one stage for one asset |
| `validation.py` | The fold contract — warm-up, train, purge, out-of-sample, final holdout — and the metrics, pure numpy (its docstring; `skills/methodology_ml.md` § 6, § 8). | `hpo.py`, `train.py` and `strategy.py` import it, and a population and its weights leave it together (its docstring). | Its folds are fixed bounds from `config.py` and its arithmetic touches no file, so the same folds gate the same numbers in whichever container runs the stage. | COMPUTE — one stage for one asset |
| `hpo.py` | The hyper-parameter search: one sequential, seeded study per asset over the frozen space, its objective the CAGR of the validation path — the quantity the serpentine search selects on — and, for a beam parent of that search, the same study stopped by one gate, the thresholds at which every fold so far clears the trade floor and beats the parent's Calmar, read off one sweep of the threshold grid per fold, and offering its best admissible point (its docstring; `skills/methodology_ml.md` § 7). | It imports `config.py`, `dataset.py`, `model.py`, `strategy.py`, `train.py` and `validation.py` — the fit, the predictions and the threshold sweep are the stages' own functions — reads X and Y through `load_xy()` and writes `<TICKER>_parameters.json`, the one file `train.py` takes from it; `log_trials()`, this module's one ledger writer — `dataset.append_jsonl` and nothing else — appends every point a study drew to the partition it is handed, `hpo_trials` from `ml-hpo` and `score_trials` from `ml-score`, each family's `schema.json` written from `TRIAL_COLUMNS`, the one constant the row is built from. | It fans out `JOBS` at a time with threads pinned to one (§ Stages) and writes at `parameters_json()`, a tracked file with no timestamp (§ What it writes) — the same path on any host, the same bytes being the claim of `METHODOLOGY-ML-AN-ARTIFACT-CARRIES-ONLY-WHAT-IT-COMPUTED`. | COMPUTE — one stage for one asset |
| `train.py` | Out-of-fold predictions per validation fold with the two importances of that fold's booster — gain and mean absolute SHAP — and the final-holdout report, under the frozen parameters `hpo.py` chose (its docstring; `skills/methodology_ml.md` § 8); `fold_evaluation()` and `to_oos_predictions()` are what a study and a scored state fit and replay through. | It imports `config.py`, `dataset.py`, `model.py` and `validation.py`, reads `<TICKER>_parameters.json` and writes the evaluation JSON and the `oos_predictions` partition `strategy.py` reads. | The numbers are persisted and the model is not (its docstring), so nothing of a run outlives its files at `oos_predictions_parquet()` and `model_evaluation_json()` — the same paths on any disk mounted at `/store/assets_artifacts`. | COMPUTE — one stage for one asset |
| `strategy.py` | STRATEGY — the research evaluation of the predictions on the canonical path, with explicit costs (`skills/methodology_ml.md` § 9), and it opens no connection to a venue; its threshold selection is one function the stage and `score.py` both run, and `validation_path_cagr()` the one growth rate a threshold, a trial and a state are ranked by. | The last stage of `ml-all` before `status`, importing `config.py`, `dataset.py`, `labels.py` and `validation.py` and reading the predictions `train.py` wrote, and the trend definition on every timeframe from the catalogue columns `load_xy()` carries. | It writes `<TICKER>_strategy_evaluation.json` and trades nothing — the host that would is where `module_skills/skill_pre_aws_solution.md` makes module boundaries extraction boundaries — so its one output keeps the path `strategy_evaluation_json()` builds. | COMPUTE — one stage for one asset |
| `score.py` | The evaluation of the states one request names: X and Y for each, the three fits or the ones it inherits, the threshold selection and the row a scored state carries — or, for a beam parent, a study and the candidate it offers; it decides nothing about which state to try next (its docstring; `skills/methodology_ml.md` § 4). | It imports `config.py`, `dataset.py`, `hpo.py`, `labels.py`, `model.py`, `strategy.py` and `train.py` — the labels, the fit, the predictions and the selection are the stages' own functions, called as a library — reads `<TICKER>_score_request.json`, which a turn of the serpentine search writes, and writes `<TICKER>_score_response.json` once every state of it has an answer, a study's points into `score_trials` before it; `theta()`, `state_key()` and the two kinds of scoring are twice by extraction with `module_features/sub_module_serpentine_search/serpentine_search.py`. | No module imports another: the search crosses into this module as two files in the asset's folder, the question and the answer, and `ml-score` is fanned out like any per-asset stage of the `ml` runner, so a state is scored at the same paths on any host. | COMPUTE — one stage for one asset |
| `status.py` | The stage that measures this module's own artifacts — the basket snapshot, the module's `CONFIGURABLES` records beside it, and each asset's README, assembled from the three result files and deriving nothing of their own (its docstring) — placed by `AGENTS.md` § Architecture shape. | It imports `config.py`, `dataset.py`, `hpo.py` and `strategy.py` for the keys they publish under, reads what `hpo.py`, `train.py` and `strategy.py` wrote, and writes `store/status/ml_status.json` for `ml.js` to fetch and `<TICKER>_README.md` into the asset's folder; the serpentine search is published by `module_features.status`, in `features_status.json`. | It runs once in a one-off container of the `ml` runner and folds the tickers `--tickers` names — the launcher passes the whole basket (§ Stages; the resident container a local mechanism, `module_skills/skill_pre_aws_solution.md`), the snapshot at the one path `ML_STATUS_JSON_PATH` builds, under the `STORE_STATUS_DIR` the launcher names. | COMPUTE — one stage, one one-off process |
| `__init__.py` | The package that makes `python -m module_ml.<stage>` a command (§ Stages), its docstring the module's responsibility in one line. | It names the labels, the purged walk-forward, XGBoost, the strategy simulation, the two reports and the scoring of the states a request names, and imports nothing. | The same `python -m module_ml.<stage> --tickers <TICKER>` runs in a one-off container of the `ml` runner (§ Stages) — the launcher setting the three `STORE_*_DIR` this module reads — the command `docker compose run --rm -T ml` carries unchanged whichever host starts it. | COMPUTE — one stage, one one-off process |
| `sub_module_terminal/` | The module's own terminal: each asset's artifacts, then one action — a target of the module carrying a `##` in the Makefile, a stage of the chain, the chain whole or `ml-score` — started through `make` for one asset (`sub_module_terminal/README_sub_module_terminal.md`; its rules `module_skills/skill_tui_designer.md`). | It imports `config.py` for every descriptor it reads, and carries the reader `dataset.py` cannot lend a host without duckdb and numpy — `load_json()`, twice by extraction — beside its own `tui.py`, one file with every other terminal's. | It computes nothing and writes nothing of its own; every stage it names runs through `make`, so the terminal stays on the host's `python3` and gum while the stages keep their one-off container of the `ml` runner. | no row — the hand's instrument over the module's targets, placed beside its module (`AGENTS.md` § Canonical vocabulary, the sub-module row) |
| the module's documents — `README_module_ml.md` and `skills/` | This orientation, the layer's rules in `skills/skill_methodology_ml.md` — rendered from `module_skills/skills_sheet.xlsx` by `make skills-sync`, never edited by hand — and its method, `skills/methodology_ml.md`, a reference for a human, filed by ownership (`AGENTS.md` § The default choice). | The orientation points at the documents beside it (§ Its normative skills), and every rule about this module sits in `skills/` (`AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_ml/` that no stage and no route reads, travelling with the code beside them — the same paths beside the code wherever the code is. | no row — a document that travels with the module's code, placed beside it |

## Its sub-module

`sub_module_terminal/` is the hand's instrument over this module: `make
ml-terminal` opens it over the basket, `ASSET=<TICKER>` over one asset. It shows,
per asset, whether the contract, the labels, the parameters, the model evaluation
and the strategy evaluation stand, then offers every target of this module that
carries a `##` in the Makefile — the stages of the chain, `ml-all` and `ml-score` —
and starts the one a hand chooses, for one asset, through `make`; then it closes.
It reads the feature layer's contract and looks whether the files stand; it reads
no snapshot and no file of the serpentine search, whose draft, reading and
promotion are the features terminal's. It computes nothing and writes nothing of
its own: it runs on the host's `python3` and gum and imports the standard library
and its own package alone — `config.py` of this module among them, which is
standard library. Its orientation is
`sub_module_terminal/README_sub_module_terminal.md`, and its rules — the
standards of its screens, with every other terminal's —
`module_skills/skill_tui_designer.md`.

## Its normative skills

| document | answers |
|---|---|
| `skills/skill_methodology_ml.md` | the layer's rules, one per `METHODOLOGY-ML-` identifier: the series, the entry, the labels, the folds and their weights, the search and its trials, the threshold, the backtest and the artifacts |
| `skills/methodology_ml.md` | the method, equation by equation, with its citations — a reference for a human, never sent by the crawler |

Project-wide rules are in `module_skills/`, the canon, indexed by
`module_skills/README.md`; the market object this module reads is defined by
`module_data/skills/skill_candle_canonicalisation.md`, the catalogue it takes X
from by `module_features/skills/skill_feature_taxonomy.md`, and the serpentine
search that asks it for scores by `module_features/skills/methodology_features.md`,
its rules `module_features/sub_module_serpentine_search/skill_serpentine_search.md`.
