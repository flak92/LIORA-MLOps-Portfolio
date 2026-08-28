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
| 9 | OHLCV lives only in DuckDB; the asset folder publishes no price series | `<TICKER>_canonical_ohlcv_*.parquet`, an `export` stage | the market object has one home and every stage reads it there; a published copy nothing reads is weight without function |
| 10 | one parameters file per asset (`<TICKER>_parameters.json`), one shared strategy (`module_ml/strategy.py`) | a parameters file per stage, a strategy file per asset | code is common, parameters are per asset; the two sections keep a-priori configuration and the search's winner apart inside one file |
| 11 | every count key is `<what>_count`: `row_count`, `gap_count`, `duplicate_count`, `ohlc_violation_count`, `source_switch_count`, `decision_count`, `ambiguous_event_count`, `unobservable_entry_count`, `trainable_row_count`; a UTC string is `_utc` (`window_start_utc`, `first_observation_utc`); `return` is spelled out (`max_abs_return_1m`) | `rows`, `gaps`, `duplicates`, `ambiguous`, `trainable`, `first_ts` for a string, `max_abs_ret_1m` | one grammar for a number: the suffix says it is a count, the word says of what; a bare plural or an adjective made the reader guess, and `_ts` already means epoch milliseconds in the parquets |
| 13 | make targets `data-download`, `data-download-binance`, `data-download-bybit`, `data-ingest`, `data-status` and the container twins `docker-data-download`, `docker-data-ingest`, `docker-data-status`; `docker-build`, `docker-up`, `docker-down` are compose lifecycle, not twins, and the single-venue downloads have no twin | bare `download`, `ingest`, `status`; `docker-download` | `<module>-<stage>` beside `ml-<stage>`: `make help` lists one module as one block, and `status` stops being ambiguous next to `ml-status` |
| 12 | the asset folder manifest is written in `LC_COLLATE=C` listing order wherever it is written (this act, the register, `FILE_MANIFEST`, the store guide) | reading order, artifact-responsibility order | one order that a byte-comparing `ls` reproduces; three orders made the same nine files look like three manifests |

## The asset folder manifest

`store_Assets_artifacts/<TICKER>/` holds exactly these nine files. No OHLCV:
the canonical series and its aggregations live only in DuckDB — the asset
folder carries the asset's features, parameters, evaluations and guide. Every
file is prefixed with its ticker, every time series carries its grid in
timeframe slots, and paths are built only by the descriptors in the modules'
`config.py`:

The table is in `LC_COLLATE=C` listing order — the register and the generated
README use the same one, so the three can be checked against each other by eye:

| file | holds | written by |
|---|---|---|
| `<TICKER>_README.md` | what the folder holds and what came out of it | `module_ml/status.py` |
| `<TICKER>_features_ss-15-hh-dd-MM.parquet` | the five 15m family columns on the decision grid | `module_ml/features.py` |
| `<TICKER>_features_ss-mm-01-dd-MM.parquet` | the five 1h family columns on the decision grid | `module_ml/features.py` |
| `<TICKER>_features_ss-mm-04-dd-MM.parquet` | the five 4h family columns on the decision grid | `module_ml/features.py` |
| `<TICKER>_label_events_ss-15-hh-dd-MM.parquet` | Y — triple-barrier events (regenerable work product) | `module_ml/labels.py` |
| `<TICKER>_model_evaluation.json` | classification results per fold, gain importance, populations | `module_ml/train.py` |
| `<TICKER>_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-sample probabilities (regenerable work product) | `module_ml/train.py` |
| `<TICKER>_parameters.json` | the one parameters file: sections `experiment_configuration` (a-priori) and `OPTUNAs_XGB_HPOs_best_params` (the winner, its log-loss, the trial count) | `module_ml/hpo.py` |
| `<TICKER>_strategy_evaluation.json` | the entry edge threshold, PnL per fold, the equity curve | `module_ml/strategy.py` |

The columns inside a per-timeframe features file carry only their family
names — the filename already says the timeframe, and a name repeats nothing
its scope states. The strategy itself is one shared file for the whole
project, `module_ml/strategy.py`: code is common, parameters are per asset.
A file copied out of its folder still says which asset it belongs to and
which grid it lives on. The store root carries one committed guide,
`store_Assets_artifacts/EXAMPLE_TICKER_README.md`, describing every manifest
file and its contents for a placeholder ticker.

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
