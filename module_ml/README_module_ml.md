# module_ml — the catalogue and the canonical series in, a research result out

The front door of this module: what it is, where its responsibility stops, and
how to run it. The method itself — every equation, every fold, every citation —
is `skills/methodology_ml.md` and is not repeated here. *The repository shows
the destination, not the road*.

`module_ml` reads one asset's feature catalogue and canonical 1m series and
produces a research result: the feature set the model sees, triple-barrier
labels, a hyper-parameter search, purged walk-forward XGBoost predictions and a
gated strategy simulation, each persisted as a file in that asset's own folder.

## Where the responsibility stops

It begins at the catalogue parquets of `module_features` and at
`ohlcv_1m_canonical`, and asks nothing about where a minute came from or how a
column was computed. Downloading, venue selection, forward fill and provenance
belong to `module_data`; the bars of the register and the catalogue belong to
`module_features`; presentation of the results belongs to `module_monitoring`.
Every stage here opens the asset's database read-only.

Every stage here is a one-off process addressed as
`python -m module_ml.<stage> --tickers <TICKER>`: it reads files, writes files
and holds nothing between runs, so the four stages of `ml-all` above `status`,
and the feature-set search and the promotion outside the chain, already have
the shape of asset-scoped compute that receives a finished catalogue and leaves
artifacts in the asset's folder, while `status` is the basket-wide fold over
them. The
direction:
[../module_skills/skill_pre_aws_solution.md](../module_skills/skill_pre_aws_solution.md).

## Stages

Run in order; `make ml-all` runs the chain. The four stages above `status` fan
out one process per asset with its threads pinned to one; `status` runs once and
aggregates the whole basket.

| stage | local | writes |
|---|---|---|
| labels | `make ml-labels` | the triple-barrier label events parquet |
| hyper-parameter search | `make ml-hpo` | `<TICKER>_parameters.json` |
| training | `make ml-train` | `<TICKER>_model_evaluation.json`, the out-of-sample predictions parquet |
| strategy | `make ml-strategy` | `<TICKER>_strategy_evaluation.json` |
| status | `make ml-status` | `module_monitoring/ml_status.json`, `<TICKER>_README.md` |
| feature-set search — outside the chain, by a hand | `make ml-feature-set-search`; detached, `make tmux-ml-feature-set-search ASSET=<TICKER>` | `<TICKER>_feature_set_search.json` |
| promotion — outside the chain, by a hand, one asset at a time | `make ml-feature-set-promote ASSET=<TICKER> PROPOSAL=<n>` | `<TICKER>_feature_set.json`, then the chain's files anew |

Every target has a `docker-` twin: a fanned-out per-asset stage runs inside
each asset's own container; `status`, and the promotion — a hand's one-off for
one asset — inside `pipeline`. Each per-asset stage takes
`--tickers`; `status` takes it too, but there it scopes only which
`<TICKER>_README.md` files are rewritten — the snapshot always folds the whole
basket.

## What it writes

```
store_assets_artifacts/<TICKER>/
```

One folder per asset, one file per artifact responsibility; the manifest and
what each file holds are in `../module_skills/glossary.md` § Artifacts.
`<TICKER>_README.md` and `<TICKER>_parameters.json` are tracked so a folder
reads without a run — both are derived and never hand-edited.

## Design rationale

Why each object of this module sits where it does — the answers of
`../module_skills/skill_self_explaining_naming.md` § The naming review written
down, one row per object, analogous pair or the module's documents; the mapping
row it answers to is `../module_skills/skill_pre_aws_solution.md` § The mapping
table, cited by its *responsibility* column and never repeated.

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The frozen experiment of the research layer — the fold bounds, the label, search and strategy parameters — and one descriptor per artifact file of this module, re-exporting the window, the register and the catalogue from `../module_features/config.py` and `TICKERS`, `artifact_dir()` and `research_ohlcv_duckdb()` from `../module_data/config.py`. | Every stage of the module imports it, nothing else names an artifact path of this module, and `is_artifact_set_complete()` is what `status.py` asks before it folds an asset. | A stage and the recorder reach an artifact by descriptor (`../module_skills/skill_pre_aws_solution.md` § Correlatable artifacts, without a version scheme), so the asset folder keeps the same path under `/app` on whatever disk is mounted there. | STORAGE — research artifacts |
| `dataset.py` | The shared IO of the layer — `load_xy()` with `load_feature_columns()` and `build_x()`, `write_json()` and `load_json()` — the one place a canonical JSON is written, re-exporting the parquet writer of `../module_features/dataset.py` for the label and prediction writers (its docstring). | `labels.py`, `hpo.py`, `train.py`, `strategy.py`, `feature_set_search.py`, `feature_set_promote.py` and `status.py` import it, and it imports `config.py` and `../module_features/dataset.py`. | It writes to the descriptor it is handed and builds no path of its own, so an artifact lands where `config.py` says on whatever disk is mounted at `/app`. | STORAGE — research artifacts |
| `labels.py` | LABEL — Y: the triple-barrier events on the canonical 1m path, per asset (its docstring; `skills/methodology_ml.md` § 5). | It imports `config.py`, `dataset.py` and `../module_features/indicators.py`, reads the canonical tables read-only and never the catalogue parquets, and writes the events parquet `load_xy()` joins to X by position. | X and Y are built by two stages and joined by position at the read, in `load_xy()`, so the join happens at the same descriptor paths whatever disk holds them. | COMPUTE — one stage for one asset |
| `model.py` | The xgboost boundary (`../AGENTS.md` § Canonical vocabulary): the class mapping, the search space, fit, predict and the two importances the booster gives — total gain and the SHAP contributions — as pure functions over numpy arrays (its docstring). | `hpo.py` and `train.py`, the two stages that fit, import it, and it imports `config.py` alone. | It reads nothing and writes nothing — `train.py` persists the numbers and not the model — so the same fit under `nthread=1` and a fixed seed runs in whichever container the stage takes (`../module_skills/skill_determinism.md`). | COMPUTE — one stage for one asset |
| `validation.py` | The fold contract — warm-up, train, purge, out-of-sample, final holdout — and the metrics, pure numpy (its docstring; `skills/methodology_ml.md` § 6, § 8). | `hpo.py`, `train.py` and `strategy.py` import it, and a population and its weights leave it together (its docstring). | Its folds are fixed bounds from `config.py` and its arithmetic touches no file, so the same folds gate the same numbers in whichever container runs the stage. | COMPUTE — one stage for one asset |
| `hpo.py` | The search: one sequential, seeded study per asset, its objective the weighted log-loss over the validation folds (its docstring; `skills/methodology_ml.md` § 7). | It imports `config.py`, `dataset.py`, `model.py` and `validation.py`, reads X and Y through `load_xy()` and writes `<TICKER>_parameters.json`, the one file `train.py` takes from it. | It fans out `JOBS` at a time with threads pinned to one (§ Stages) and writes at `parameters_json()`, a tracked file with no timestamp (§ What it writes) — the same path on any host, the same bytes being the claim of `../module_skills/skill_determinism.md`. | COMPUTE — one stage for one asset |
| `train.py` | Out-of-fold predictions per validation fold with the two importances of that fold's booster — gain and mean absolute SHAP — and the final-holdout report, under the frozen parameters `hpo.py` chose (its docstring; `skills/methodology_ml.md` § 8). | It imports `config.py`, `dataset.py`, `model.py` and `validation.py`, reads `<TICKER>_parameters.json` and writes the evaluation JSON and the predictions parquet `strategy.py` reads. | The numbers are persisted and the model is not (its docstring), so nothing of a run outlives its two files at `oos_predictions_parquet()` and `model_evaluation_json()` — the same paths on any disk mounted at `/app`. | COMPUTE — one stage for one asset |
| `strategy.py` | STRATEGY — the research evaluation of the predictions on the canonical path, with explicit costs (`skills/methodology_ml.md` § 9), and it opens no connection to a venue; its threshold selection is one function the stage and the feature-set search both run. | The last stage of `ml-all` before `status`, importing `config.py`, `dataset.py` and `validation.py` and reading the predictions `train.py` wrote, and the trend definition on every timeframe from the catalogue columns `load_xy()` carries. | It writes `<TICKER>_strategy_evaluation.json` and trades nothing — the host that would is `../module_skills/skill_pre_aws_solution.md` § Module boundaries are extraction boundaries — so its one output keeps the path `strategy_evaluation_json()` builds. | COMPUTE — one stage for one asset |
| `feature_set_search.py` | The feature-set search: stepwise on the validation folds under the frozen parameters, selected on the model's validation skill fold by fold, the strategy's numbers reported beside every trial, the ledger of every trial its state (its docstring; `skills/methodology_ml.md` § 4). | It imports `config.py`, `dataset.py`, `model.py`, `strategy.py` and `train.py` — the fit, the predictions and the selection are the stages' own functions, called as a library — and writes the one file `status.py` reads as `feature_set_search`. | It runs one asset at a time, resumes by comparing its recorded inputs with the run's by equality, and rewrites `feature_set_search_json()` after every trial — the same path and the same bytes on any host, whether in the venv, in `asset-<ticker>` or detached in a tmux session on the host. | COMPUTE — one stage for one asset |
| `feature_set_promote.py` | The promotion: a hand's choice copied into the asset's feature set — the proposal's columns and nothing else, the commit history the record of every promotion — and nothing computed (its docstring; `skills/methodology_ml.md` § 4). | It imports `config.py` and `dataset.py`, reads the search result `feature_set_search.py` wrote and writes the one file `load_feature_columns()` reads before every fit. | It takes `--tickers` and `--proposal` and is never fanned out — one asset per hand, its docker twin a one-off in `pipeline` in the shape of `status` — and the Makefile reruns `ml-all` for that asset after it, so the promoted set is re-tuned at the same paths on any host. | COMPUTE — one stage, one one-off process |
| `status.py` | The stage that measures this module's own artifacts — the basket snapshot and each asset's README, assembled from the three result files and computing nothing of their own (its docstring) — placed by `../AGENTS.md` § Architecture shape. | It imports `config.py` and `dataset.py`, reads what `hpo.py`, `train.py`, `strategy.py`, `feature_set_search.py` and `feature_set_promote.py` wrote, and writes `../module_monitoring/ml_status.json` for `ml.js` to fetch and `<TICKER>_README.md` into the asset's folder. | It runs once in the one-off `pipeline` and folds the whole basket whatever `--tickers` says (§ Stages; `../module_skills/skill_pre_aws_solution.md` § The resident container is a local mechanism), the snapshot at the one path `MODULE_MONITORING_ML_STATUS_JSON_PATH` builds. | COMPUTE — one stage, one one-off process |
| `__init__.py` | The package that makes `python -m module_ml.<stage>` a command (§ Stages), its docstring the module's responsibility in one line. | It names the feature set, the labels, the walk-forward, the model, the strategy simulation and the two reports, and imports nothing. | The same `python -m module_ml.<stage> --tickers <TICKER>` runs in the venv, in `asset-<ticker>` and in `pipeline` (§ Stages), the command `docker compose run --rm -T pipeline` carries unchanged. | COMPUTE — one stage, one one-off process |
| the module's documents — `README_module_ml.md` and `skills/` | This orientation and the normative documents of `skills/`, filed by ownership (`../AGENTS.md` § The default choice). | The orientation points at the documents beside it (§ Its normative skills), and every rule about this module sits in `skills/` (`../AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_ml/` that no process reads, travelling with the code beside them — the same paths beside the code wherever the code is. | no row — a document that travels with the task's code, seated beside its module |

## Its normative skills

| document | answers |
|---|---|
| `skills/methodology_ml.md` | the research layer equation by equation, with its citations |

Repository-wide rules are in `../module_skills/`, indexed by
[../module_skills/README.md](../module_skills/README.md); the market object it
reads is defined by
[../module_data/skills/skill_candle_canonicalisation.md](../module_data/skills/skill_candle_canonicalisation.md),
the catalogue it takes X from by
[../module_features/skills/skill_feature_taxonomy.md](../module_features/skills/skill_feature_taxonomy.md).
