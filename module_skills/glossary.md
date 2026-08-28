# Glossary — one concept, one name

**Names must be self-explanatory before they are project-specific. Prefer
standard domain terminology. A glossary confirms meaning; it must not be
required to decode an obscure name.**

Every concept below has exactly one name in the code, one key in the artifacts
and one label in the interface. A synonym never enters, and a new concept is
registered here in the same commit that introduces it. Names that are standard
in the field (`fold`, `purge`, `embargo`, out-of-sample, Sharpe) appear as
confirmation; the rest of the concept column states what the name means.

## Validation and folds

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| one chronological segment of the research window | `fold`, `fold_id` | `fold_2` … `fold_5` | `F1` … `F5` | split, period, chunk |
| the segment boundaries | `fold_bounds()`, `FOLD_BOUNDS_MS` | `folds.bounds_utc` | — | split_bounds |
| the folds used for the data-driven selection of model hyper-parameters and the entry edge threshold | `VALIDATION_FOLD_IDS` = (2, 3, 4) | `validation` | `F2`–`F4` | test folds, CV folds, "the folds that choose every parameter" |
| the fold that is only ever evaluated | `FINAL_HOLDOUT_FOLD_ID` = 5 | `final_holdout`, `final_holdout_fold_id` | `F5 — final holdout (out-of-sample)` | test, test set, locked test, final OOS |
| the evaluated block of a fold, and which one a prediction belongs to | `oos`, `oos_fold_id` | `oos_fold_id` (parquet column) | out-of-sample | test block, test period |
| dropping training events that overlap the evaluated block | `purge` — `event_end_ts <= oos_start` | `folds.purge_rule` | purged | gap, buffer |
| a forced wait after the evaluated block — **width zero here**, forward chaining needs none | `embargo` | `folds.embargo` | — | cooldown, post-test embargo |
| bars consumed before the first decision is allowed | `WARMUP_4H_BARS` = 200, `WARMUP_END_MS` | `folds.warmup_4h_bars`, `warmup_excluded_decision_count` | warm-up excluded | burn-in |

## Market object

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the studied series, and the only series below the ingest boundary | `ohlcv_1m_canonical` and its aggregates | — (DuckDB tables only; no OHLCV file is published) | canonical dataset | fused series, index, blended price |
| the three timeframes the hierarchy reads | `HIERARCHY_TIMEFRAMES` = ("15m", "1h", "4h") | `features.hierarchy_timeframes` | 15m / 1h / 4h | levels, LEVELS |
| the timeframe a decision is taken on | `DECISION_TIMEFRAME` = "15m" | `features.decision_timeframe` | — | DECISION_TF |
| how long one bar of a timeframe lasts | `TIMEFRAME_DURATION_MS` | — | — | TF_MS |
| a data provider, above the ingest boundary only | `binance` / `bybit`, in `module_data` | `venues.*`, `binance_pct` / `bybit_pct` | Raw source | venue or exchange used below ingest |
| which provider a canonical minute came from | `source`, `source_switch_count` | same | primary / secondary / ffill | — |
| a minute with no observed trade | `volume = 0`, `zero_volume` | `zero_volume`, `zero_volume_bars` | zero-volume bars | carried-forward price (true only of forward-filled minutes) |
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
| the vertical barrier, in minutes (240 = 16 × 15m bars) | `LABEL_HORIZON_MINUTES`, `LABEL_HORIZON_MS` | `labels.label_horizon_minutes` | 240-minute horizon | HORIZON_BARS, W, H |
| the exclusive end of the event | `event_end_ts` | `event_end_ts` | — | exit time |
| the price that closes the event | `exit_reference_price` | `exit_reference_price` | — | exit_ref |
| how the event ended | `event_resolution` | `event_resolution`, `exit_counts.*` | upper_barrier / lower_barrier / vertical / ambiguous | reason, exit_reason |
| the four resolutions | `EVENT_RESOLUTION_{UPPER_BARRIER, LOWER_BARRIER, VERTICAL, AMBIGUOUS}` | `labels.event_resolution_codes` | — | bare 1 / −1 / 0 / 9 |
| the entry minute traded at all — knowable at `entry_ts`, may gate an entry | `entry_observable` | `entry_observable`; its complement is counted as `unobservable_entry_count` | unobservable entry | tradable, valid entry |
| the event can be classified — knowable only afterwards, never gates an entry | `label_valid` | `label_valid`; its complement is counted as `ambiguous_event_count` | ambiguous | masked, mask_ok |
| the supervised population: both of the above | `sample_valid` | `trainable_row_count`, `trainable_row_pct` | trainable rows | valid rows |
| how little an event overlaps its neighbours **within one population** — measured after the purge, never stored in Y | `average_uniqueness_weight()`, `train_weight` / `scoring_weight` | — | — | `weight` as a Y column, uniqueness_weight_mean, class weight |

## Signal and strategy

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the model's directional lean, `p_long − p_short` | `directional_probability_edge` | — | edge | `edge` as a code name |
| how much of that lean a signal must carry to be traded | `entry_edge_threshold` (τ) | `entry_edge_threshold` | τ (entry edge threshold) | `tau` as an identifier |
| the grid searched for it | `ENTRY_EDGE_THRESHOLD_GRID` | `strategy.entry_edge_threshold_grid` | — | TAU_GRID |
| whether any threshold on the grid cleared the trade floor | `entry_edge_threshold_constraint_met` | same | fallback | tau_constraint_met |
| the trade floor — a selection guardrail, not an acceptance gate | `MINIMUM_TRADES_PER_VALIDATION_FOLD` = 30 | `strategy.minimum_trades_per_validation_fold` | — | TAU_MIN_TRADES, MIN_TRADES, acceptance gate |
| how many timeframes must agree with the side | `MINIMUM_AGREEING_TREND_TIMEFRAMES`, `agreeing_trend_timeframe_count` | `minimum_agreeing_trend_timeframes` | at least 2 of 3 timeframes agree | AGREE_MIN, gate_min_agree, hierarchy_min_agree, n_agree, level |
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
| rows a fold's metrics were computed on | `scored_row_count` | `scored_row_count` | scored | `n` |
| rows the model was fitted on, and the events purged before them | `training_row_count`, `purged_event_count` | same | trained on / purged | n_train, n_purged |
| rows in a prediction window | `window_row_count` | `window_row_count` | window | n_window |
| trades a fold produced | `trade_count` | `trade_count` | trades | n_trades |
| trials the search ran | `trial_count` | `trial_count` | trials | n_trials |

## Data quality (status.json)

Written by `module_data/status.py`; every SQL alias in its scans is the key it becomes.

| concept | artifact key | UI label | never |
|---|---|---|---|
| minutes a venue printed / the canonical grid holds | `row_count` | rows | rows, n |
| grid minutes a venue did not print (whole window / since its first observation) | `gap_count`, `gap_count_after_first_observation` | gaps | gaps |
| minutes printed more than once | `duplicate_count` | dups | duplicates |
| candles whose OHLC ordering is broken | `ohlc_violation_count` | ohlc bad | ohlc_violations |
| minutes whose source differs from the previous minute | `source_switch_count` | switches | source_switches |
| the largest 1m move at a switch / anywhere on the canonical series | `max_abs_return_at_switch`, `max_abs_return_1m` | max \|ret\| | `*_ret_*` |
| a venue's first and last printed minute | `first_observation_utc`, `last_observation_utc` | first / last | `first_ts` (a `_ts` is epoch ms) |
| the data window | `window_start_utc`, `window_end_utc` | window | `window_start` |
| totals across the flow | `binance_zip_count`, `bybit_zip_count`, `binance_row_count`, `bybit_row_count`, `canonical_row_count` | flow | `zips_binance`, `rows_canonical` |
| bars of a kind inside a bar or a series (a unit, not a bare count) | `ffill_bars`, `zero_volume_bars`, `flat_bars` | ffill / zero-vol / flat | `n_ffill` |
| shares | `coverage_pct`, `binance_pct`, `bybit_pct`, `ffill_pct`, `real_data_pct` | % | ratio without `_pct` |

## Metrics

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| log-loss of the weighted training class prior | `prior_logloss` | `prior_logloss` | prior log-loss | baseline |
| log-loss of the model on the evaluated block | `model_logloss` | `model_logloss` | model log-loss | loss |
| information beyond the prior, `1 − model / prior` | `relative_logloss_skill` | `relative_logloss_skill` | skill | accuracy, edge |
| the HPO objective value at the chosen point | `best_logloss` | `best_logloss` | best mean F2–F4 log-loss | best_value, score |
| what the search chose: the point, its objective value and the trial count | `hyperparameter_search_result` | `hyperparameter_search_result` (a section of the parameters file, a block of ml_status.json) | search | a second name for the same block |
| annualised Sharpe of the 15m equity path | `sharpe` | `sharpe`, `selection_score_mean_sharpe` | Sharpe | return/risk |
| maximum drawdown of the 1m equity path | `max_drawdown` | `max_drawdown` | maxDD | DD |
| share of the fold spent in a position | `exposure` | `exposure` | exposure | utilisation |
| share of a fold's trades that ended positive | `hit_rate` | `hit_rate` | hit | win rate |
| mean cost-adjusted return of a trade | `average_trade_return` | `average_trade_return` | avg trade | expectancy, `avg_trade_ret` |
| equity at the end of the fold, starting from 1.0 | `final_equity` | `final_equity` | final equity | PnL |
| total gain per feature column of the final-holdout booster (fitted on F1–F4) | `gain_importance()` | `gain_importance` | FEATURES — total gain | importance, weight, a validation booster's gain |

## Payload structure

The container and envelope keys of the two snapshots, so that every published
key is in this register.

| concept | artifact key | holds |
|---|---|---|
| when the snapshot was written | `generated_at_utc` | the one timestamp of a payload |
| the frozen experiment, once, globally | `research_window` with `start_utc`, `end_utc`, `seed` | the same three values `<TICKER>_parameters.json` carries per asset |
| the per-asset reports of ml_status.json | `assets` (a list) with `ticker`, `sample`, `hyperparameter_search` (`best_params`, `best_logloss`, `trial_count`), `validation`, `final_holdout`, `gain_importance`, `strategy` | the experiment flow, sample → search → validation → holdout → attribution → strategy |
| the classes of the supervised population | `class_counts` with `short`, `neutral`, `long` | counts, named by class |
| how the trades of a fold ended | `exit_counts` with `upper_barrier`, `lower_barrier`, `vertical`, `ambiguous` | counts, named by `event_resolution` |
| the final-holdout equity path | `equity_curve` with `equity` | weekly-sampled values only; the last value is `final_equity` |
| the three tables of status.json | `symbols`, `venues` (one list per venue), `canonical_source` — lists whose rows are keyed by `symbol` | the pipeline, raw-source and canonical-construction tables |
| the flow totals | `flow` | one `<venue>_zip_count` and `<venue>_row_count` per venue, plus `canonical_row_count` |
| the database envelope | `db_bytes`, `duckdb_version` | size on disk and the engine that wrote it |
| day files a venue's tree holds | `zip_count` | one per UTC calendar day |
| the longest run of flat no-trade minutes | `longest_flat_run_minutes` | a duration, in minutes |

## Artifacts

**One file per distinct artifact responsibility; no duplicate representations
of the same result.** One directory per ticker under `store_Assets_artifacts/`,
each file named after what it holds.

In `LC_COLLATE=C` listing order — the one order the act, this register and the
generated README share:

| file | written by | holds |
|---|---|---|
| `<TICKER>_README.md` | `module_ml/status.py` | what the folder holds and what came out of it |
| `<TICKER>_features_<timeframe slots>.parquet` ×3 | `module_ml/features.py` | X — one file per timeframe: that timeframe's five family columns on the decision grid |
| `<TICKER>_label_events_ss-15-hh-dd-MM.parquet` | `module_ml/labels.py` | Y — labels, the event flags and the event prices |
| `<TICKER>_model_evaluation.json` | `module_ml/train.py` | classification metrics per fold |
| `<TICKER>_oos_predictions_ss-15-hh-dd-MM.parquet` | `module_ml/train.py` | out-of-sample probabilities for the full windows; metrics score only the supervised subset |
| `<TICKER>_parameters.json` | `module_ml/hpo.py` | the one parameters file: sections `experiment_configuration` (a-priori) and `hyperparameter_search_result` (what the search chose) |
| `<TICKER>_strategy_evaluation.json` | `module_ml/strategy.py` | the entry edge threshold and the PnL |

## Features

| family | computes | timeframes |
|---|---|---|
| `ema20_minus_ema50_over_atr14` | `(EMA20 − EMA50) / ATR14` | `_15m`, `_1h`, `_4h` |
| `centered_rsi14` | `(RSI14 − 50) / 50` | `_15m`, `_1h`, `_4h` |
| `atr14_over_close` | `ATR14 / close` | `_15m`, `_1h`, `_4h` |
| `range_position_20` | `(close − min(low, 20)) / (max(high, 20) − min(low, 20))` | `_15m`, `_1h`, `_4h` |
| `log_volume_zscore_50` | z-score of `log1p(volume)` over 50 bars | `_15m`, `_1h`, `_4h` |

Never `trend`, `momentum`, `volatility`, `structure` or `activity` as a column
name — those name a category, not a computation. The strategy hierarchy reads
the first family through `config.TREND_FAMILY`, so the name appears once in the
code rather than in three string literals.
