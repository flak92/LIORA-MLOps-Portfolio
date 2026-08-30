# Glossary — one concept, one name

*The repository shows the destination, not the road*: the register confirms; no check reads it.
Every concept below has exactly one name in the code, one key in the artifacts
and one label in the interface. Names that are standard
in the field (`fold`, `purge`, `embargo`, out-of-sample, Sharpe) appear as
confirmation; the rest of the concept column states what the name means.

## Validation and folds

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| one chronological segment of the research window | `fold`, `fold_id` | `fold_2` … `fold_5` | `F2` … `F5` | split, period, chunk |
| the segment boundaries | `fold_bounds()`, `FOLD_BOUNDS_MS` | — | — | split_bounds |
| the folds used for the data-driven selection of model hyper-parameters and the entry edge threshold | `VALIDATION_FOLD_IDS` = (2, 3, 4) | `validation` | `F2`–`F4` | test folds, CV folds, "the folds that choose every parameter" |
| the fold that is only ever evaluated | `FINAL_HOLDOUT_FOLD_ID` = 5 | `final_holdout`, `final_holdout_fold_id` | `F5 — final holdout (out-of-sample)` | test, test set, locked test, final OOS |
| the evaluated block of a fold, and which one a prediction belongs to | `oos`, `oos_fold_id` | `oos_fold_id` (parquet column) | out-of-sample | test block, test period |
| dropping training events that overlap the evaluated block | `purge` — `event_end_ts <= oos_start` | — | purged | gap, buffer |
| a forced wait after the evaluated block — **width zero here**, forward chaining needs none | `embargo` | — | — | cooldown, post-test embargo |
| bars consumed before the first decision is allowed | `WARMUP_4H_BARS` = 200, `WARMUP_END_MS` | `warmup_excluded_decision_count` | warm-up excluded | burn-in |

## Market object

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the external minute-bar format the raw store is byte-compatible with | Lean — `module_data/lean.py` | — (the raw tree only) | — | QC, quantconnect-format, `lean` lower-case mid-sentence; a project-cased spelling of its tree |
| the studied series, and the only series below the ingest boundary | `ohlcv_1m_canonical` and its aggregates | — (tables of the asset's own DuckDB; no copy of the series is published) | canonical dataset | fused series, index, blended price |
| the three timeframes the hierarchy reads | `HIERARCHY_TIMEFRAMES` = ("15m", "1h", "4h") | — | 15m / 1h / 4h | levels, LEVELS |
| the timeframe a decision is taken on | `DECISION_TIMEFRAME` = "15m" | — | — | DECISION_TF |
| how long one bar of a timeframe lasts | `TIMEFRAME_DURATION_MS` | — | — | TF_MS |
| a data provider, above the ingest boundary only | `binance` / `bybit`, in `module_data` | `venues.*`, `binance_pct` / `bybit_pct` | Raw source | venue or exchange used below ingest |
| which provider a canonical minute came from | `source`, `source_switch_count` | same | primary / secondary / ffill | — |
| a minute with no observed trade | `volume = 0`, `zero_volume` | `zero_volume`, `zero_volume_bars` | zero-vol | carried-forward price (true only of forward-filled minutes) |
| a synthesised continuity minute | `source = 'ffill'` | `ffill_bars` | ffill | gap, missing bar |
| quality columns that are never features | `binance_valid`, `bybit_valid`, `rel_divergence` | — (database columns; `rel_divergence` is published only as `relative_divergence_mean` / `relative_divergence_p99` / `relative_divergence_max`) | — | signal, feature |

## Event and sample

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the moment a decision may be taken — close of the 15m bar | `decision_ts` | `decision_ts` | — | signal time |
| the candidate entry minute after the decision — an entry is permitted here, not guaranteed | `entry_ts` | `entry_ts` | — | fill time, first tradable minute |
| the canonical open of that minute | `entry_price` | `entry_price` | — | `p0` as an identifier (`P₀` stays in the equations) |
| the take-profit price of a long, the stop of a short | `upper_barrier` | `upper_barrier` | upper_barrier | `upper`, ceiling, band |
| the stop of a long, the take-profit of a short | `lower_barrier` | `lower_barrier` | lower_barrier | `lower`, floor, band |
| the vertical barrier, in minutes (240 = 16 × 15m bars) | `LABEL_HORIZON_MINUTES`, `LABEL_HORIZON_MS` | — | 240-minute horizon | HORIZON_BARS, W, H |
| the exclusive end of the event | `event_end_ts` | `event_end_ts` | — | exit time |
| the price that closes the event | `exit_reference_price` | `exit_reference_price` | — | exit_ref |
| how the event ended | `event_resolution` | `event_resolution`, `exit_counts.*` | upper_barrier / lower_barrier / vertical / ambiguous | reason, exit_reason |
| the four resolutions | `EVENT_RESOLUTION_{UPPER_BARRIER, LOWER_BARRIER, VERTICAL, AMBIGUOUS}` | `event_resolution` | — | bare 1 / −1 / 0 / 9 |
| the entry minute traded at all — knowable at `entry_ts`, may gate an entry | `entry_observable` | `entry_observable`; its complement is counted as `unobservable_entry_count` | unobservable entry | tradable, valid entry |
| the event can be classified — knowable only afterwards, never gates an entry | `label_valid` | `label_valid`; its complement is counted as `ambiguous_event_count` | ambiguous | masked |
| the supervised population: both of the above | `sample_valid` | `trainable_row_count`, `trainable_row_pct` | trainable rows | valid rows |
| how little an event overlaps its neighbours **within one population** — measured after the purge, never stored in Y | `average_uniqueness_weight()`, `train_weight` / `scoring_weight` | — | — | `weight` as a Y column, class weight |

`decision_ts`, `entry_ts` and `event_end_ts` are the three epoch-millisecond
columns spelled `_ts`, a contract with the parquets on disk; every new
epoch-millisecond key is `_ms`.

## Signal and strategy

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the model's directional lean, `p_long − p_short` | `directional_probability_edge` | — | edge | `edge` as a code name |
| how much of that lean a signal must carry to be traded | `entry_edge_threshold` (τ) | `entry_edge_threshold` | τ (entry edge threshold) | `tau` as an identifier |
| the grid searched for it | `ENTRY_EDGE_THRESHOLD_GRID` | — | — | TAU_GRID |
| whether any threshold on the grid cleared the trade floor | `entry_edge_threshold_constraint_met` | same | `constraint met` (yes / fallback); `!` beside a fallback threshold | `tau_ok`, a name that says a constraint without saying which |
| the trade floor — a selection guardrail, not an acceptance gate | `MINIMUM_TRADES_PER_VALIDATION_FOLD` = 30 | — | — | MIN_TRADES, acceptance gate |
| how many timeframes must agree with the side | `MINIMUM_AGREEING_TREND_TIMEFRAMES`, `agreeing_trend_timeframe_count` | `minimum_agreeing_trend_timeframes` | at least 2 of 3 timeframes agree | AGREE_MIN, n_agree, level |
| replaying the strategy over the canonical price path | `backtest()` | `<TICKER>_strategy_evaluation.json` | STRATEGY | live execution, exchange execution |
| the execution cost charged on entry and on exit | `EXECUTION_COST_RATE_PER_TRADE_SIDE` = 0.0006 | `execution_cost_rate_per_trade_side` | cost per side | costs_per_side, cost_per_side, fees |

The symbol τ may stay in equations and in table headers; its first use in any
document or on any page spells out `entry edge threshold`.

## Counts

Every count is `<what>_count`; a bare `n`, a bare plural (`gaps`) or an
adjective (`ambiguous`) names no number.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| decisions on the 15m grid after the warm-up | `decision_count` | `decision_count` | decisions | rows, `n` |
| rows a fold's metrics are computed on | `scored_row_count` | `scored_row_count` | scored | `n` |
| rows the model is fitted on, and the events purged before them | `training_row_count`, `purged_event_count` | same | trained on / purged | n_train, n_purged |
| rows in a prediction window | `window_row_count` | `window_row_count` | window | n_window |
| trades a fold produced | `trade_count` | `trade_count` | trades | n_trades |
| trials the search ran | `trial_count` | `trial_count` | trials | n_trials |

## Data quality (data_status.json)

Written by `module_data/status.py`; every alias a scan publishes is the key it becomes.

| concept | artifact key | UI label | never |
|---|---|---|---|
| minutes a venue printed / the canonical grid holds | `row_count` | rows (`canonical rows` on the Pipeline tab) | rows, n |
| grid minutes a venue did not print (whole window / since its first observation) | `gap_count`, `gap_count_after_first_observation` | gaps | gaps |
| minutes printed more than once | `duplicate_count` | dups | duplicates |
| candles whose OHLC ordering is broken | `ohlc_violation_count` | ohlc bad | ohlc_violations |
| minutes whose source differs from the previous minute | `source_switch_count` | switches | source_switches |
| the largest 1m move at a switch / anywhere on the canonical series | `max_abs_return_at_switch`, `max_abs_return_1m` | max \|ret\| | `*_ret_*` |
| a venue's first and last printed minute | `first_observation_utc`, `last_observation_utc` | first / last | `first_ts` (a `_ts` is epoch ms) |
| the data window | `window_start_utc`, `window_end_utc` | window | `window_start` |
| totals across the flow | `binance_zip_count`, `bybit_zip_count`, `binance_row_count`, `bybit_row_count`, `canonical_row_count` | flow | `zips_binance`, `rows_canonical` |
| bars of a kind inside a bar or a series (a unit, not a bare count) | `ffill_bars`, `zero_volume_bars`, `flat_bars` | ffill (`ffill bars` on the Pipeline tab) / zero-vol / flat | `n_ffill` |
| shares | `coverage_pct`, `binance_pct`, `bybit_pct`, `ffill_pct`, `real_data_pct` | coverage / primary / secondary / ffill / real-data share | ratio without `_pct` |
| cross-venue close divergence over the canonical series | `relative_divergence_mean`, `relative_divergence_p99`, `relative_divergence_max` | rel. divergence mean / p99 / max | `rdiv` |

## Metrics

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| log-loss of the weighted training class prior | `prior_logloss` | `prior_logloss` | prior log-loss (`prior LL` in a cross-section header) | baseline |
| log-loss of the model on the evaluated block | `model_logloss` | `model_logloss` | model log-loss (`model LL` in a cross-section header) | loss |
| information beyond the prior, `1 − model / prior` | `relative_logloss_skill` | `relative_logloss_skill` | skill (`rel. skill`, `val skill F<n>`, `mean val skill`, `holdout skill` in the tables) | accuracy, edge |
| the search for model hyper-parameters, and the stage that runs it | HPO — `module_ml/hpo.py`, `make ml-hpo` | `hyperparameter_search_result` | search | tuning, optimisation, autoML; `HPO` spelled out mid-document after its first use |
| the HPO objective value at the chosen point | `best_logloss` | `best_logloss` | best mean F2–F4 log-loss (`best LL` in the search table) | best_value, score |
| what the search chose: the point, its objective value and the trial count | `hyperparameter_search_result` | `hyperparameter_search_result` (a section of the parameters file, a block of ml_status.json) | search | a second name for the same block |
| annualised Sharpe of the 15m equity path | `sharpe` | `sharpe`, `selection_score_mean_sharpe` | Sharpe; `selection score` for the validation mean, and `degradation` for holdout Sharpe minus the selection score — presentation arithmetic | return/risk |
| maximum drawdown of the 1m equity path | `max_drawdown` | `max_drawdown` | maxDD | DD |
| share of the fold spent in a position | `exposure` | `exposure` | exposure | utilisation |
| share of a fold's trades that ended positive | `hit_rate` | `hit_rate` | hit | win rate |
| mean cost-adjusted return of a trade | `average_trade_return` | `average_trade_return` | avg trade | expectancy, `avg_trade_ret` |
| equity at the end of the fold, starting from 1.0 | `final_equity` | `final_equity` | final equity | PnL |
| total gain per feature column of the final-holdout booster (fitted on F1–F4) | `gain_importance()` | `gain_importance` | FEATURES — XGBoost total gain | importance, weight, a validation booster's gain |

## Payload structure

The container and envelope keys of the two snapshots, so that every published
key is in this register.

| concept | artifact key | holds |
|---|---|---|
| when the snapshot is written | `generated_at_utc` | the one timestamp of a payload |
| the frozen experiment, once, globally | `research_window` with `start_utc`, `end_utc`, `seed` | the window and the seed, published once — no per-asset copy |
| the per-asset reports of ml_status.json | `assets` (a list) with `ticker`, `sample`, `hyperparameter_search_result` (`best_params`, `best_logloss`, `trial_count`), `validation`, `final_holdout`, `gain_importance`, `strategy`, `artifacts` | the experiment flow, sample → search → validation → holdout → attribution → strategy, then the folder |
| the classes of the supervised population | `class_counts` with `short`, `neutral`, `long` | counts, named by class |
| the two structural numbers the page needs beside the assets | `final_holdout_fold_id`, `minimum_agreeing_trend_timeframes` | which fold is the final holdout; how many timeframes the gate needs |
| how the trades of a fold ended | `exit_counts` with `upper_barrier`, `lower_barrier`, `vertical`, `ambiguous` | counts, named by `event_resolution` |
| the final-holdout equity path | `equity_curve` with `equity` | weekly-sampled values only; the last value is `final_equity` |
| the three tables of data_status.json | `symbols`, `venues` (one list per venue), `canonical_source` — lists whose rows are keyed by `symbol` | the pipeline, raw-source and canonical-construction tables |
| the flow totals | `flow` | one `<venue>_zip_count` and `<venue>_row_count` per venue, plus `canonical_row_count` |
| the engine of the databases | `duckdb_version` | the engine that wrote every asset's database |
| an asset's database on disk | `db_bytes` (a `symbols` row) | the size of `<TICKER>_research_ohlcv.duckdb` |
| the last canonical minute of an asset | `last_observation_utc` (a `canonical_source` row) | the asset's grid end; in a venue row the same key names that venue's last printed minute |
| the unit of download work, and the cadence a measurement's age is judged against | `download_cadence_minutes` | one UTC day; the Containers tab warns above it |
| when the model evaluation was last written | `artifacts` with `model_evaluation_modified_utc` | a fact of the folder, published in ml_status.json only, never in the timestamp-free README |
| day files a venue's tree holds | `zip_count` | one per UTC calendar day — `zips` on the page |
| the longest run of flat no-trade minutes | `longest_flat_run_minutes` | a duration, in minutes — `flat run (min)` on the page |

## Artifacts

**One file per distinct artifact responsibility; no duplicate representations
of the same result.** One directory per ticker under `store_assets_artifacts/`;
every file carries the `<TICKER>_` prefix, a time series carries its grid in
timeframe slots, and paths are built only by the descriptors of
`module_ml/config.py`.

The nine manifest files in `LC_COLLATE=C` listing order — the order
`FILE_MANIFEST` in `module_ml/status.py` and the generated README share:

| file | written by | holds |
|---|---|---|
| `<TICKER>_README.md` | `module_ml/status.py` | what the folder holds and what came out of it; no timestamp |
| `<TICKER>_features_ss-15-hh-dd-MM.parquet` | `module_ml/features.py` | X — `decision_ts` and the five 15m family columns on the decision grid |
| `<TICKER>_features_ss-mm-01-dd-MM.parquet` | `module_ml/features.py` | X — `decision_ts` and the five 1h family columns |
| `<TICKER>_features_ss-mm-04-dd-MM.parquet` | `module_ml/features.py` | X — `decision_ts` and the five 4h family columns |
| `<TICKER>_label_events_ss-15-hh-dd-MM.parquet` | `module_ml/labels.py` | Y — `decision_ts`, `entry_ts`, `y`, `event_end_ts`, `entry_observable`, `label_valid`, `event_resolution`, `entry_price`, `upper_barrier`, `lower_barrier`, `exit_reference_price` |
| `<TICKER>_model_evaluation.json` | `module_ml/train.py` | `validation.fold_2..4` and `final_holdout`, each `prior_logloss`, `model_logloss`, `relative_logloss_skill`, `scored_row_count`; `gain_importance`, `class_counts`, `labels`, `segments` |
| `<TICKER>_oos_predictions_ss-15-hh-dd-MM.parquet` | `module_ml/train.py` | `decision_ts`, `oos_fold_id`, `p_short`, `p_neutral`, `p_long` — the full windows of F2–F5; metrics score only the supervised subset |
| `<TICKER>_parameters.json` | `module_ml/hpo.py` | `hyperparameter_search_result` (`best_params`, `best_logloss`, `trial_count`) |
| `<TICKER>_strategy_evaluation.json` | `module_ml/strategy.py` | `entry_edge_threshold`, `entry_edge_threshold_constraint_met`, `selection_score_mean_sharpe`, `execution_cost_rate_per_trade_side`; per fold `sharpe`, `max_drawdown`, `trade_count`, `hit_rate`, `average_trade_return`, `exposure`, `exit_counts`, `final_equity`; the final holdout's `equity_curve` |

Two files are tracked, `<TICKER>_README.md` and `<TICKER>_parameters.json` —
they make a folder readable without a run; the seven others are regenerable
from the database. Beside the manifest, outside it, `<TICKER>_research_ohlcv.duckdb`
holds the canonical series and its aggregations: its size moves with every
top-up, and the README is byte-reproducible for an unchanged experiment.

## Features

The five feature families — `ema20_minus_ema50_over_atr14`, `centered_rsi14`,
`atr14_over_close`, `range_position_20`, `log_volume_zscore_50` — each on
`_15m`, `_1h`, `_4h`; the definitions are in `methodology_ml.md` § 4. Never
`trend`, `momentum`, `volatility`, `structure` or `activity` as a column name —
those name a category, not a computation. The strategy hierarchy reads the
first family through `config.TREND_FAMILY`, so the name appears once in the
code rather than in three string literals.

## Asset containers

The concepts of `docker-compose.yml` and of `serve.py`'s asset role. They name
how a stage is run, never what it computes.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the one asset a container is | `ASSET` (environment) = `ticker` (code, key, folder); read by the fan-out's command line, `--tickers $ASSET`, and by `serve.py` choosing its role — never by the engine, never the default of `build_ticker_parser` | `ticker` (the endpoint envelope) | — | `TICKER`, `SYMBOL`, `ASSET_TICKER`, a per-asset `.env` |
| a compose service that is one asset's container: resident, answering `/status`, the place every per-asset stage runs | `asset-<ticker lowercase>` — one service per ticker under the file's `x-server` anchor | — | — | `asset-BTC`, `container-btc`, a one-off `run --rm` container beside a resident, a `restart:` policy, a published port |
| the command the servers run — the server, its role by `ASSET`, on the internal port | the `x-server` anchor's `command:`; `CONTAINER_PORT` = 8900 and `BIND_ADDRESS` = `0.0.0.0` in `serve.py` | — | — | a per-service command, a port or a bind address read from the environment or the command line, `PORT` inside a container |
| where the dashboard's proxy reads one asset's endpoint | `http://asset-<ticker>:8900/status`, built in `serve.py` | — | — | an IP, a published port |
| the one image every service runs | `image: mlops-portfolio-1m-pipeline` | — | — | compose's `<project>-<service>` default, one image per service |
| the memory ceiling every service runs under | the `x-service` anchor's `deploy.resources.limits.memory` | — | — | `mem_limit` beside it, a CPU quota, a reservation, a service written outside the anchor and so without a ceiling |

## Container status endpoint

The keys `module_monitoring/serve.py` answers with — `GET /containers` on the
dashboard, `GET /status` on an asset container.

| concept | artifact key | holds |
|---|---|---|
| the basket, as the dashboard serves it | `tickers` | `module_data.config.TICKERS`, in order |
| how often the page asks | `poll_interval_seconds` | published by the server, never a literal in the page |
| when the server of an asset container started — how long it has been up, for the tab | `started_at_utc` | one UTC string, beside the envelope's `generated_at_utc` |
| the asset's data, as last measured | `data` with the snapshot's `generated_at_utc`, `row_count`, `last_observation_utc`, `db_bytes`, and `observation_lag_minutes`, `measurement_age_minutes`, `research_window_covered` | `null` when the snapshot has no row for the asset; `db_bytes` `null` while the database is absent; is the market data behind, is anyone still measuring, does the grid cover the frozen window |
| the asset's folder, as last measured | `artifacts` with `model_evaluation_modified_utc`, `entry_edge_threshold_constraint_met` | `null` when the ML snapshot has no block for the asset |
| what only the container can see about itself | `footprint` with `memory_bytes`, `memory_peak_bytes`, `memory_limit_bytes`, `cpu_usage_seconds`, `cpu_count` | the cgroup's accounting: `memory_bytes` is what the kernel charges, page cache included; the limit is the cgroup ceiling or `MemTotal` when it sets none; the CPU count is the host's, the basket sets no quota. A CPU rate is the page's arithmetic over two polls, never a key |

The Containers tab's columns and labels are the tab table of
`skill_asset_containers.md`. The page's navigation: the tabs *Pipeline*, *Data
Quality*, *ML Research*, *ML Assets*, *Containers*, *Lifecycle*, and the ML Assets views
*Labels & data*, *Classification*, *Strategy*, *Search*.

## Run record

What one recorded run of the chain leaves in
`store_assets_artifacts/<TICKER>/runtime/<run_id>/`, written by
`module_monitoring/record.py` wrapping each stage command in the container that
stage already runs in. `run_id` is `<YYYYMMDDTHHMMSS>Z_<git short commit>`: not a
content hash, but git's own identity, the record `module_ml/config.py` already
names — so it sorts chronologically and points at the code that ran.

**A `process_` key is the stage; a `container_` key is not.** The stage's cost
comes from `wait4` rusage of the process the recorder spawned and reaped — exact,
never sampled. The cgroup counters carry the whole container over the same
window: the resident server, the recorder and the stage together.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| one recorded execution of the chain | `run_id` | `run_id` | run | build, job, a content hash |
| one command of a run, named for the Makefile target that runs it | `stage_of()` | `stage` | stage | step, task |
| the compose service the stage ran in | `docker_service()` | `docker_service` | container | host; a bare `container`, which the Containers tab already uses for up/down |
| CPU the stage process and its reaped descendants used | `rusage.ru_utime + ru_stime` | `process_cpu_seconds` | CPU | cpu, cpu_pct, cpu_time |
| peak resident set of the stage process | `rusage.ru_maxrss` | `process_memory_peak_bytes` | peak RAM | RSS, RAM, mem, max_rss |
| bytes the stage moved through `read()` / `write()`, independent of the page cache | `/proc/<pid>/io` | `process_read_chars`, `process_write_chars` | read / write | io, bytes_in |
| physical blocks the stage caused, cache-dependent and writeback-delayed | `rusage.ru_inblock`, `ru_oublock` | `process_disk_read_bytes`, `process_disk_write_bytes` | — | a headline I/O number |
| the whole container over the stage's window | the cgroup | `container_cpu_seconds_delta`, `container_memory_charged_peak_bytes`, `container_disk_*_bytes_delta`, `container_network_*_bytes_delta` | container | any of these as a stage cost |
| how many 1 s samples the stage window held | `sample_count` | `sample_count` | samples | n_samples |
| wall time between stages: docker exec setup and teardown | — | `orchestration_seconds` | orchestration | overhead, a hidden remainder |
| the stage that took the longest | — | `bottleneck_stage` | bottleneck | slowest, hotspot |
| the readiness check that closes a run | `fetch_dashboard_ready()` | `dashboard_ready` | dashboard | healthcheck, ping |

The four files of a run: `manifest.json` (what ran, where, on what host, and how
it ended), `events.jsonl` (one line per stage, appended by the stage itself),
`resources.jsonl` (the 1 s container-wide samples), `summary.json` (the stage
table and the run totals, plus `measurement_notes`, which states in the payload
what each number is and is not). `logs/<stage>.log` holds that stage's output
verbatim. None of it is committed; `.gitignore` already covers the tree.

The routes: `GET /runs` lists the run ids newest first, `GET /runs/<run_id>`
answers one run's manifest, summary and samples, the samples strided to
`RUN_SAMPLE_POINT_LIMIT` so a long run is thinned and never truncated.

## Developer experience

**Developer experience (DX)** is the repository read as something a person works in rather than as
something that runs: how quickly its shape can be seen, and how little has to be held in the head to
change it. `DX` is used as an abbreviation only after that first spelling, and only for the
sub-module and the control that opens its page.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the tracked tree drawn as one self-contained page | `module_monitoring/sub_module_dx/visualise.py` | `module_monitoring/sub_module_dx/files_and_folders_visualisation.html` | Files and Folders | diagram, chart, map |
| one coloured band the drawing sorts a path into | story, `island` | `island`, `story_map` | `S1` … `S4` | group, cluster, section |
| the node at the centre of a band | `hub` | `hub` | — | anchor, root of the band |
| a folder collapsed to a single node | `aggregate` | `aggregate` | the folder's own name | rollup, summary node |
| the commit the tree was read from, and its date | `load_provenance_stamp()` | the tail of `subtitle` | `tree as of <hash> · <date>` | generated at, build date |
| the control that opens the drawing from the status page | — | — | DX | help, docs, about |

The drawing is redrawn by hand with `make monitoring-dx-update` and by nothing else. It is a derived
artifact under *Derived, never drafted*: a hand edit to it is a violation, and the provenance stamp
is what says how old it is.

