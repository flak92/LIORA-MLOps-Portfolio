# module_ml — the catalogue, the bars and the canonical series in, a research result out

The orientation of this module: what it is, where its responsibility stops and how to run it. The method — every
equation, every fold, every citation — is `skills/methodology_ml.md`, and the layer's rules are
`skills/skill_methodology_ml.md`.

`module_ml` reads one asset's feature catalogue, its bars and its canonical 1m series and produces a research result:
X from the asset's feature set, triple-barrier labels, a hyper-parameter search, purged walk-forward XGBoost
predictions and a gated strategy simulation. Each tabular result is the asset's partition of a table family,
`schema.json` at the family's root; each other result is a file in the asset's own folder, `ticker=<TICKER>/`. Outside
the chain it answers the serpentine search's questions: the states one `<TICKER>_score_request.json` names are scored
on the validation folds and answered in `<TICKER>_score_response.json`.

## Where the responsibility stops

```
<TICKER>_catalogue.json + catalogue + bars + ohlcv_1m_canonical → labels → search → model → strategy
    → ml_status.json, <TICKER>_README.md
```

It begins at the feature layer's contract, `<TICKER>_catalogue.json`, the catalogue partitions it names, the `bars`
partitions and `ohlcv_1m_canonical` — every one read as a file — and asks nothing about where a minute came from or how
a column was computed. Downloading, venue selection and provenance belong to `module_data`; the bars, the catalogue,
the serpentine search and its promotion belong to `module_features`; presentation belongs to `module_monitoring`. This
module scores a state it is asked about and chooses none. What an operator may set is a record of `CONFIGURABLES` in
`config.py` (`METHODOLOGY-ML-AN-EXPERIMENT-CONSTANT-LIVES-IN-CONFIG`); the decision timeframe, the hierarchy, the
warm-up and the catalogue's columns arrive per asset in the contract
(`METHODOLOGY-ML-THE-LAYER-NAMES-NO-TIMEFRAME-OF-THE-REGISTER`).

## Stages

Run in order; `make ml-all` runs them, each stage in a one-off container of the `ml` runner, and a single stage is its
own `ml-<stage>` target — or `python -m module_ml.<stage> --tickers <TICKER>` by hand in a shell that exports
`STORE_ASSETS_ARTIFACTS_DIR`, `STORE_TRIALS_DIR` and `STORE_STATUS_DIR`. The four stages above `status` fan out one
process per asset, `JOBS` of them side by side; `status` runs once over the assets the launcher names.

| stage | target | writes |
|---|---|---|
| labels | `make ml-labels` | the asset's `labels` partition on the decision timeframe the contract names, `labels/ticker=<TICKER>/timeframe=<timeframe>/labels.parquet`, and `labels/schema.json` |
| hyper-parameter search | `make ml-hpo` | `<TICKER>_parameters.json`, and every point its study drew into `hpo_trials/ticker=<TICKER>/hpo_trials.jsonl` of the trials store, with `hpo_trials/schema.json` |
| training | `make ml-train` | `<TICKER>_model_evaluation.json`, and the `oos_predictions` partition, `oos_predictions/ticker=<TICKER>/timeframe=<timeframe>/oos_predictions.parquet`, with `oos_predictions/schema.json` |
| strategy | `make ml-strategy` | `<TICKER>_strategy_evaluation.json` |
| status | `make ml-status` | `store/status/ml_status.json`, the module's `CONFIGURABLES` records beside the assets, and `<TICKER>_README.md` |
| score — outside the chain, the serpentine search's question | `make ml-score`, one process per asset, and between two turns of `make features-serpentine-search` | `<TICKER>_score_response.json`: a trial row per state, or a study and its candidate per beam parent; a study's points into `score_trials/ticker=<TICKER>/score_trials.jsonl` of the trials store, with `score_trials/schema.json` |

A promotion (`make features-serpentine-search-promote ASSET=<TICKER>`, the feature module's target) copies a
proposal's whole state and reruns `ml-all` for the asset, whose study starts from the promoted point
(`SERPENTINE-SEARCH-PROMOTION-IS-A-HAND`, `METHODOLOGY-ML-NO-STUDY-IS-HANDED-A-STARTING-POINT`).

## What it writes

```
store/assets_artifacts/labels/ticker=<TICKER>/timeframe=<timeframe>/labels.parquet                    Y on the decision grid of the decision timeframe
store/assets_artifacts/oos_predictions/ticker=<TICKER>/timeframe=<timeframe>/oos_predictions.parquet  the out-of-sample class probabilities, full windows
store/assets_artifacts/{labels,oos_predictions}/schema.json                                           each family's columns, beside its partitions
store/assets_artifacts/ticker=<TICKER>/                                                               the parameters, the two evaluations, the README, the score response
store/trials/hpo_trials/ticker=<TICKER>/hpo_trials.jsonl                                              every point ml-hpo's studies drew
store/trials/score_trials/ticker=<TICKER>/score_trials.jsonl                                          every point the studies ml-score ran for the search drew
store/trials/{hpo_trials,score_trials}/schema.json                                                    the one row both trials families share
store/status/ml_status.json                                                                           the status snapshot the dashboard reads
```

The manifest of an asset's research artifacts is the Files table of its `<TICKER>_README.md`, and what each holds is the
register's § Artifacts. `<TICKER>_README.md` and `<TICKER>_parameters.json` are tracked, beside the serpentine search's
files and the promoted state `module_features` writes, because the parameters are tuned for the promoted state and
travel with it.

## Extending

| what you add | where, and how much | what it changes | the gate |
|---|---|---|---|
| a hyper-parameter | one entry in `HYPERPARAMETER_SEARCH_SPACE` (`config.py`), in xgboost's own spelling, with the kind of its draw — `int`, `int_step`, `float` or `log` — and its bounds | the search space, `best_params`, the `params` of both trials families' `schema.json` — `TRIAL_COLUMNS` is built from the space — and every artifact downstream of a retune; a recorded serpentine search is reset and run again after the retune (`SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT`) | `ml-labels` and the catalogue's partitions byte-identical; the record's `requires_rerun` names what to run |
| a coordinate of a state's barrier geometry | one entry in `BARRIER_COORDINATE_CASTS` and one in `START_BY_COORDINATE_DEFAULT` (`config.py`), each twice by extraction with `module_features/sub_module_serpentine_search/config.py`, the name in `TRADE_EXIT_COORDINATE_NAMES` too where it moves only a trade's exit, and the one computation that reads it — `labels.label_events()` for the label, `strategy.signals_for_fold()` for a trade; its moves are the search's | nothing of `score.py`: a state, its key, its fit identity and its trial row carry the coordinates by the register's names | with the coordinate at its start value the chain's files are byte-identical |

## Design rationale

Why each object of this module sits where it does, one row per object or analogous pair; the last column is the
responsibility of the mapping table in `module_skills/README.md` § The Pre-AWS mapping it answers to
(`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The frozen experiment of the research layer — its `CONFIGURABLES` records and the constants below them — and one descriptor per family and per file of this module. | Every stage imports it, nothing else names an artifact path of this module, and being standard library, the terminal imports it too; it imports nothing of another module. | A stage reaches a file by descriptor (`PRE-AWS-SOLUTION-A-PATH-IS-BUILT-BY-ONE-DESCRIPTOR`). | STORAGE — research artifacts |
| `dataset.py` | The shared IO of the layer — the one read of the contract per stage, X and Y, the feature set, the barrier geometry and `barriers_from()`, the one place a horizon token becomes minutes, the JSON and parquet writers and the ledger's append. | `labels.py`, `hpo.py`, `train.py`, `strategy.py`, `score.py` and `status.py` import it. | It writes to the descriptor it is handed; `build_xy()` reads no file, so `score.py` builds X and Y in process the way a stage does. | STORAGE — research artifacts |
| `labels.py` | LABEL — Y: the triple-barrier events on the canonical 1m path (`skills/methodology_ml.md` § 5). | It reads the canonical series and the bars as files, never the catalogue; `score.py` calls `label_events()` again for a state whose label geometry moved. | X and Y are built by two stages and joined by position at the read. | COMPUTE — one stage for one asset |
| `model.py` | The xgboost boundary: the class mapping, the draw of the search space, fit, predict and the two importances, pure functions over numpy arrays. | `hpo.py`, `train.py` and `score.py` fit through it. | It reads and writes nothing; the same fit under `nthread=1` and a fixed seed runs anywhere (`DETERMINISM-THREAD-CAPS-FROZEN-AT-ONE`). | COMPUTE — one stage for one asset |
| `validation.py` | The fold contract — warm-up, train, purge, out-of-sample, final holdout — and the metrics, pure numpy (`skills/methodology_ml.md` § 6, § 8). | `hpo.py`, `train.py` and `strategy.py` import it; a population and its weights leave it together. | Its folds are fixed bounds of `config.py` and its arithmetic touches no file. | COMPUTE — one stage for one asset |
| `hpo.py` | The hyper-parameter search: one sequential, seeded study per asset over the frozen space, its objective the CAGR of the validation path, and for a beam parent of the serpentine search the same study stopped by one gate (`skills/methodology_ml.md` § 7); `log_trials()`, the one ledger writer. | It reads X and Y through `dataset.py` and writes `<TICKER>_parameters.json`, the one file `train.py` takes from it. | A tracked file with no timestamp (`METHODOLOGY-ML-AN-ARTIFACT-CARRIES-ONLY-WHAT-IT-COMPUTED`). | COMPUTE — one stage for one asset |
| `train.py` | Out-of-fold predictions per validation fold with the two importances of that fold's booster, and the final-holdout report, under the parameters `hpo.py` chose (`skills/methodology_ml.md` § 8). | It writes the evaluation JSON and the `oos_predictions` partition `strategy.py` reads; `fold_evaluation()` is what a study and a scored state fit through. | The numbers are persisted and the model is not (`METHODOLOGY-ML-NO-BOOSTER-IS-PERSISTED`). | COMPUTE — one stage for one asset |
| `strategy.py` | STRATEGY — the research evaluation of the predictions on the canonical path, with explicit costs (`skills/methodology_ml.md` § 9); its threshold selection is one function the stage and `score.py` both run. | The last stage of `ml-all` before `status`, reading the predictions `train.py` wrote. | It writes `<TICKER>_strategy_evaluation.json` and trades nothing. | COMPUTE — one stage for one asset |
| `score.py` | The evaluation of the states one request names — a trial row per state, or a study and its candidate per beam parent; it decides nothing about which state to try next (`skills/methodology_ml.md` § 4). | It calls the stages' own functions as a library, reads the question a turn wrote and writes the answer once every state has one. | The search crosses into this module as two files (`SERPENTINE-SEARCH-THE-EVALUATOR-IS-A-FILE-AWAY`). | COMPUTE — one stage for one asset |
| `status.py` | The stage that measures this module's own artifacts — the basket snapshot, the `CONFIGURABLES` records beside it, and each asset's README. | It reads what `hpo.py`, `train.py` and `strategy.py` wrote and writes the snapshot `ml.js` fetches. | Once over the basket, at `ML_STATUS_JSON_PATH`. | COMPUTE — one stage, one one-off process |
| `__init__.py` | The package that makes `python -m module_ml.<stage>` a command, its docstring the module's responsibility in one line. | It imports nothing. | The same command runs in a one-off container of the `ml` runner. | COMPUTE — one stage, one one-off process |
| `sub_module_terminal/` | The module's own terminal: each asset's artifacts, then one target of the module started through `make`. | It imports `config.py` and carries the reader `dataset.py` cannot lend a host without duckdb and numpy. | It computes nothing and writes nothing (`TUI-DESIGNER-ONE-TERMINAL-PER-MODULE`). | no row — the hand's instrument over the module's targets, placed beside its module (`AGENTS.md` § Canonical vocabulary, the sub-module row) |
| the module's documents — `README_module_ml.md` and `skills/` | This orientation, the layer's rules and its method, filed by ownership (`AGENTS.md` § The default choice). | Every rule about this module sits in `skills/` (`AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_ml/` that no stage and no route reads. | no row — a document that travels with the module's code, placed beside it |

## Its sub-module

`sub_module_terminal/` is the hand's instrument over this module: `make ml-terminal` opens it over the basket,
`ASSET=<TICKER>` over one asset, shows whether each asset's contract, labels, parameters and evaluations stand, and
starts one target of this module through `make`. The serpentine search's draft, reading and promotion are the features
terminal's. Its orientation is `sub_module_terminal/README_sub_module_terminal.md`.
