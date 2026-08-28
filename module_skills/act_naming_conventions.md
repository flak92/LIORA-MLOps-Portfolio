# Act: naming conventions — the enacted names of this project

`AGENTS.md` holds the grammars — how a name is derived. This act holds the
decisions — which exact names the project enacted where a grammar left a
choice. One authority each: a rule lives in the contract, a decision lives
here, and a new decision enters this act in the commit that enacts it. Every
entry names the rejected form, because the rejected form is what stops the
next reader from reinventing it.

## Enacted names

| # | enacted | not | why |
|---|---|---|---|
| 1 | `module_data/`, `module_ml/`, `module_monitoring/`, `module_skills/` | `data_module`, `src`, `module_guidance`, `module_skills_for_the_project` | kind first so siblings sort together; the shortest name whose kind-first files say the rest; "for the project" repeats the scope it lives in |
| 2 | `store_Assets_artifacts/` | `store_research_artifacts`, `store_assets_artifacts` | the capital A signals what the folder holds — one `<TICKER>/` in capitals per asset; the eye reads the signal before the parser reads the contents |
| 3 | `store_db/` | `db`, `store_database` | kind first; `db` is unambiguous in this technical context |
| 4 | `store_raw_data_ss-01-hh-dd-MM/` | `store_raw_1m`, `raw_downloaded_1m_data` | the timeframe slot standard (§ below): every future raw store sorts from the finest granularity to the coarsest |
| 5 | `<TICKER>/` in capitals inside `store_Assets_artifacts/` | `btc`, `BTCUSDT` | the ticker is the project's asset identity; the exchange symbol belongs to the adapter boundary |
| 6 | Lean raw tree spelling: `cryptofuture/<venue>/minute/<symbol lowercase>/`, `YYYYMMDD_trade.zip` | project-cased variants | external-format boundary — Lean's vocabulary wins inside the store it defines |
| 7 | guidance files: `act_*`, `skill_*`, `methodology_*`, `glossary.md` | bare topic names | kind first inside the folder, same rule as the tree above it |
| 8 | the asset folder manifest (§ below): every per-asset file carries the `<TICKER>_` prefix, a time series carries its grid in timeframe slots | `canonical_1m.parquet`, `features.parquet`, `hyperparameter_search.json`, a bare `README.md` | the file identifies its asset and its grid on its own, and the folder lists as one contiguous `<TICKER>_*` block |

## The asset folder manifest

`store_Assets_artifacts/<TICKER>/` holds exactly these nine files — every one
prefixed with its ticker, every time series carrying its grid in timeframe
slots, paths built only by the descriptors in the modules' `config.py`:

| file | holds | written by |
|---|---|---|
| `<TICKER>_canonical_ohlcv_ss-01-hh-dd-MM.parquet` | the published canonical 1m OHLCV series (t, O, H, L, C, V) | `module_data/export.py` |
| `<TICKER>_features_ss-15-hh-dd-MM.parquet` | X — 15 causal feature columns on the 15m decision grid | `module_ml/features.py` |
| `<TICKER>_label_events_ss-15-hh-dd-MM.parquet` | Y — triple-barrier events on the 15m decision grid | `module_ml/labels.py` |
| `<TICKER>_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-sample class probabilities, full prediction windows | `module_ml/train.py` |
| `<TICKER>_OPTUNAs_XGB_HPOs_best_params.json` | the winning point of the Optuna→XGB search, its log-loss and the trial count | `module_ml/hpo.py` |
| `<TICKER>_model_evaluation.json` | classification metrics per fold, gain importance, populations | `module_ml/train.py` |
| `<TICKER>_strategy_evaluation.json` | the entry edge threshold, PnL per fold, the equity curve | `module_ml/strategy.py` |
| `<TICKER>_experiment_configuration.json` | the a-priori experiment configuration, recorded at report time | `module_ml/status.py` |
| `<TICKER>_README.md` | what the folder holds and what came out of it | `module_ml/status.py` |

A file copied out of its folder still says which asset it belongs to and which
grid it lives on — the name does the folder's work when the folder is gone.

## The timeframe slot standard

A filesystem name that carries a timeframe writes it as five fixed slots,
finest to coarsest: `ss-mm-hh-dd-MM` (seconds, minutes, hours, days, months).
The active granularity is a zero-padded number in its slot; every inactive
slot keeps its unit letters as a placeholder.

| timeframe | slots |
|---|---|
| 1 second | `01-mm-hh-dd-MM` |
| 1 minute | `ss-01-hh-dd-MM` |
| 15 minutes | `ss-15-hh-dd-MM` |
| 1 hour | `ss-mm-01-dd-MM` |
| 4 hours | `ss-mm-04-dd-MM` |
| 1 day | `ss-mm-hh-01-MM` |
| 1 month | `ss-mm-hh-dd-01` |

Why it sorts: ASCII digits precede letters, so a filled slot beats a
placeholder at the same position and finer granularity always lists first —
verified identical under `LC_COLLATE=C` and `en_US.UTF-8`. Zero-padding keeps
numeric order inside a slot; the fixed slot count keeps listings
column-aligned. The mechanics are the subject of
`skill_sorting_files_naming_standard.md`.

In a Python identifier the slot dashes become underscores:
`store_raw_data_ss-01-hh-dd-MM/` mirrors to
`STORE_RAW_DATA_SS_01_HH_DD_MM_DIR`.

## The serialized-schema boundary

The slot standard governs filesystem names. Serialized schema — DuckDB tables
(`ohlcv_1m_canonical`, `ohlcv_15m_canonical`…), parquet columns, feature names
(`centered_rsi14_15m`) and artifact keys — keeps the compact `1m/15m/1h/4h`
tokens: those names are contracts with the files on disk, and a schema
migration is not a naming cleanup. They adopt the standard only at the next
schema-breaking change, recorded here when it happens.
