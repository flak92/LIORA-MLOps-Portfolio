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
| 1 | `module_data/`, `module_ml/`, `module_monitoring/`, `module_skills/` | `src`, `core`, `lib` | kind first so siblings sort together; the shortest name whose kind-first files say the rest; "for the project" repeats the scope it lives in |
| 2 | `store_assets_artifacts/` | `assets/`, `store_Assets_artifacts` | kind first, then what the store holds, in the ordinary lowercase snake_case every other store uses — so `STORE_ASSETS_ARTIFACTS_DIR` mirrors the directory exactly and no rule has to explain a capital letter |
| 3 | `store_db/` | `db`, `database` | kind first; `db` is unambiguous in this technical context |
| 4 | `store_raw_1m/`, and every future raw store as `store_raw_<timeframe>/` | a store spelling its timeframe in sorting slots, `raw_data` | a store is one object: its name says what it holds, in the compact timeframe token the code and the schema already speak (`ohlcv_1m_canonical`, `SOURCE_CANDLE_INTERVAL`), so the next raw store names itself. Sorting slots are for the file family that has to sort by granularity (§ timeframe slots) |
| 5 | `<TICKER>/` in capitals inside `store_assets_artifacts/` | `btc`, `BTCUSDT` | the ticker is the project's asset identity, spelled the way the basket spells it; the exchange symbol belongs to the adapter boundary |
| 6 | Lean raw tree spelling: `cryptofuture/<venue>/minute/<symbol lowercase>/`, `YYYYMMDD_trade.zip` | project-cased variants | external-format boundary — Lean's vocabulary wins inside the store it defines |
| 7 | guidance files: `act_*`, `skill_*`, `methodology_*`, `glossary.md` | bare topic names | kind first inside the folder, same rule as the tree above it |
| 8 | the asset folder manifest (§ below): every per-asset file carries the `<TICKER>_` prefix, a time series carries its grid in timeframe slots | `features.parquet`, a bare `README.md` — any per-asset file that needs its folder to say which asset it belongs to | the file identifies its asset and its grid on its own, and the folder lists as one contiguous `<TICKER>_*` block |
| 9 | OHLCV lives only in DuckDB; the asset folder publishes no price series | a per-asset OHLCV parquet, an `export` stage | the market object has one home and every stage reads it there; a published copy nothing reads is weight without function |
| 10 | one parameters file per asset (`<TICKER>_parameters.json`), one shared strategy (`module_ml/strategy.py`) | a parameters file per stage, a strategy file per asset | code is common, parameters are per asset; the two sections keep the a-priori configuration and the search result apart inside one file |
| 11 | every count key is `<what>_count`: `row_count`, `gap_count`, `duplicate_count`, `ohlc_violation_count`, `source_switch_count`, `decision_count`, `ambiguous_event_count`, `unobservable_entry_count`, `trainable_row_count`; a UTC string is `_utc` (`window_start_utc`, `first_observation_utc`); `return` is spelled out (`max_abs_return_1m`) | a bare plural (`rows`, `gaps`), an adjective holding a number (`ambiguous`), `_ts` on a string, `ret` for a return | one grammar for a number: the suffix says it is a count, the word says of what; a bare plural or an adjective made the reader guess, and `_ts` already means epoch milliseconds in the parquets |
| 12 | the asset folder manifest is written in `LC_COLLATE=C` listing order wherever it is written (this act, the register, `FILE_MANIFEST`, the store guide) | reading order, artifact-responsibility order | one order that a byte-comparing `ls` reproduces; three orders made the same nine files look like three manifests |
| 13 | make targets `data-download`, `data-download-binance`, `data-download-bybit`, `data-ingest`, `data-status` and the container twins `docker-data-download`, `docker-data-ingest`, `docker-data-status`; `docker-build`, `docker-up`, `docker-down` are compose lifecycle, not twins, and the single-venue downloads have no twin | bare `download`, `ingest`, `status`; `docker-download` | `<module>-<stage>` beside `ml-<stage>`: `make help` lists one module as one block, and `status` stops being ambiguous next to `ml-status` |
| 14 | `<TICKER>_README.md` with README in capitals | `<TICKER>_readme.md`, a bare `README.md` | README is a convention older than this act; it is the one manifest entry whose position depends on collation (first under `LC_COLLATE=C`, eighth under `en_US.UTF-8`) — the `<TICKER>_*` block stays contiguous under both, and GitHub renders neither spelling as the folder's README |
| 15 | `EXAMPLE_TICKER_README.md` sorts inside the ticker block of `store_assets_artifacts/` | a store-root `README.md` | the guide is found where a reader looks for an asset folder; `ls -1d */` sees only the ten ticker directories |
| 16 | ecosystem-fixed file names keep their spelling: `__init__.py`, `AGENTS.md`, `Dockerfile`, `Makefile`, `README.md`, `docker-compose.yml`, `requirements.txt` | project-cased variants | a boundary like Lean's casing (row 6); they are the only names whose sort position depends on collation, so the collation check binds every other directory |
| 17 | the stage order lives in the Makefile (`all:`, `ml-all:`); every document points there | a second copy of the chain in README or a methodology | two copies drift; the per-asset reproduce line of `<TICKER>_README.md` is derived from the same order by `module_ml/status.py` |

## External vocabularies

Row 6 is the first instance of a rule that holds at every boundary: inside the
call that speaks an external format or library, the external spelling wins, and
the project's names begin at the return value. An unnamed boundary is the class of
names a mechanical rename walks into by accident — to a regular expression an
SVG attribute like `viewBox` is an identifier, to the browser it is a contract —
so every one is listed here with the file that owns it.

| boundary | owning file | words that stay external |
|---|---|---|
| QuantConnect Lean minute-trade format | `module_data/lean.py` (names, writer, full-day predicate); the tree above the file name comes from `module_data/config.py` | `cryptofuture/<venue>/minute/<symbol>/`, `YYYYMMDD_trade.zip`, `YYYYMMDD_<symbol>_minute_trade_perp.csv` |
| Binance REST | `module_data/download_binance.py` | `symbol`, `interval`, `startTime`, `endTime`, `limit` |
| Bybit REST v5 | `module_data/download_bybit.py` | `category`, `interval="1"`, `start`, `end`, `limit`, `retCode`, `retMsg`, `result.list` |
| xgboost, and the sklearn pair it borrows | `module_ml/model.py` | `DMatrix`, `train`, `num_boost_round`, `predict`, `get_score`, `fit`, `predict_proba`, the hyper-parameter names in `best_params` |
| optuna | `module_ml/model.py`, `module_ml/hpo.py` | `trial.suggest_int/float`, `create_study`, `TPESampler`, `n_trials`, `n_jobs`, `best_trial` — and the borrowed verb `suggest_params`, legal because the closed I/O verb list binds I/O functions only |
| argparse | `module_data/config.py` (`ticker_parser`) | `ArgumentParser`, `add_argument`, `parse_args` |
| SVG / DOM | `module_monitoring/*.js` | `setAttribute`, `viewBox`, `preserveAspectRatio`, `x1`, `y1`, `points`, `insertRow`, `createTHead`, `textContent` |
| DuckDB SQL | `module_data/ingest.py`, `module_data/status.py`, `module_ml/bars.py`, `module_ml/dataset.py`, `module_ml/features.py`, `module_ml/labels.py`, `module_ml/strategy.py` | `read_csv`, `read_parquet`, `arg_min`, `arg_max`, `FILTER`, `quantile_cont`, `last_value … IGNORE NULLS`, `fetchnumpy` |
| docker compose | `Makefile` (`docker-up`, `docker-down`), `docker-compose.yml` | `up`, `down`, `run --rm`, `${PORT:-8900}` |

The browser is a boundary of its own: it has no config module, so `app.js` and
`ml.js` fetch the two snapshots by literal name. Before any mechanical rename,
run the pre-sweep grep and confirm that every hit sits inside an owning file
above: `git grep -n 'setAttribute("\|suggest_\|retCode\|startTime\|DMatrix\|read_csv\|read_parquet' -- '*.py' '*.js'`.

## The asset folder manifest

`store_assets_artifacts/<TICKER>/` holds exactly these nine files. No OHLCV:
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
| `<TICKER>_parameters.json` | the one parameters file: sections `experiment_configuration` (a-priori) and `hyperparameter_search_result` (the chosen point, its log-loss, the trial count) | `module_ml/hpo.py` |
| `<TICKER>_strategy_evaluation.json` | the entry edge threshold, PnL per fold, the equity curve | `module_ml/strategy.py` |

The `.gitignore` whitelist is the manifest's fifth site: it names the two
tracked files, `<TICKER>_parameters.json` and `<TICKER>_README.md`; the other
seven are regenerable and stay out.

The columns inside a per-timeframe features file carry only their family
names — the filename already says the timeframe, and a name repeats nothing
its scope states. The strategy itself is one shared file for the whole
project, `module_ml/strategy.py`: code is common, parameters are per asset.
A file copied out of its folder still says which asset it belongs to and
which grid it lives on. The store root carries one committed guide,
`store_assets_artifacts/EXAMPLE_TICKER_README.md`, describing every manifest
file and its contents for a placeholder ticker.

## The timeframe slot standard

A file that belongs to a timeframe family writes its granularity as five fixed slots,
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

Two patterns, two jobs — a name follows the one that fits its object:

```
STORE, one object, an identity:     store_raw_<timeframe>/
                                    store_raw_1m/   store_raw_5m/   store_raw_1h/

FILES, a family that must sort by   <asset>_<artifact>_<timeframe-slot>.<ext>
granularity inside one listing:     BTC_features_ss-15-hh-dd-MM.parquet
                                    BTC_features_ss-mm-01-dd-MM.parquet
                                    BTC_features_ss-mm-04-dd-MM.parquet
```

A store has no siblings to order, so it takes the token the rest of the project
speaks; the three feature files of one asset are read as one block, so they take
the slots that put the finest first.

## The serialized-schema boundary

The slot standard governs filesystem names. Serialized schema — DuckDB tables
(`ohlcv_1m_canonical`, `ohlcv_15m_canonical`…), parquet columns, feature names
(`centered_rsi14_15m`) and artifact keys — keeps the compact `1m/15m/1h/4h`
tokens: those names are contracts with the files on disk, and a schema
migration is not a naming cleanup. They adopt the standard only at the next
schema-breaking change, recorded here when it happens.

The same deferral covers two more names the schema already carries: the
epoch-millisecond columns `decision_ts`, `entry_ts`, `event_end_ts` of the
parquets (the key grammar says `_ms`; no new `_ts` is minted), the DuckDB column
`rel_divergence` (published only as `relative_divergence_*`). A compact timeframe
token inside an identifier or a key (`WARMUP_4H_BARS`, `folds.warmup_4h_bars`,
`equity_15m`) is not a deferral at all: it is the timeframe vocabulary of code
and schema, and the slots are for the file family that sorts by granularity.
