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
| the studied series, and the only series below the ingest boundary | `ohlcv_1m_canonical` and its aggregates | `canonical_ss-01-hh-dd-MM.parquet` | canonical dataset | fused series, index, blended price |
| the three timeframes the hierarchy reads | `HIERARCHY_TIMEFRAMES` = ("15m", "1h", "4h") | `features.hierarchy_timeframes` | 15m / 1h / 4h | levels, LEVELS |
| the timeframe a decision is taken on | `DECISION_TIMEFRAME` = "15m" | `features.decision_timeframe` | — | DECISION_TF |
| how long one bar of a timeframe lasts | `TIMEFRAME_DURATION_MS` | — | — | TF_MS |
| a data provider, above the ingest boundary only | `binance` / `bybit`, in `module_data` | `venues.*`, `pct_binance` | Raw source | venue or exchange used below ingest |
| which provider a canonical minute came from | `source`, `source_switches` | same | primary / secondary / ffill | — |
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
| the entry minute traded at all — knowable at `entry_ts`, may gate an entry | `entry_observable` | `entry_observable`, `unobservable` | unobservable entry | tradable, valid entry |
| the event can be classified — knowable only afterwards, never gates an entry | `label_valid` | `label_valid`, `ambiguous` | ambiguous | masked, mask_ok |
| the supervised population: both of the above | `sample_valid` | `trainable`, `trainable_pct` | trainable rows | valid rows |
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
| replaying the strategy over the canonical price path | `backtest()` | `strategy_evaluation.json` | STRATEGY | live execution, exchange execution |
| the execution cost charged on entry and on exit | `EXECUTION_COST_RATE_PER_TRADE_SIDE` = 0.0006 | `execution_cost_rate_per_trade_side` | cost per side | costs_per_side, cost_per_side, fees |

The symbol τ may stay in equations and in table headers; its first use in any
document or on any page spells out `entry edge threshold`.

## Counts

Every count says what it counts; a bare `n` names nothing.

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| rows a fold's metrics were computed on | `scored_row_count` | `scored_row_count` | scored | `n` |
| rows the model was fitted on, and the events purged before them | `training_row_count`, `purged_event_count` | same | trained on / purged | n_train, n_purged |
| rows in a prediction window | `window_row_count` | `window_row_count` | window | n_window |
| trades a fold produced | `trade_count` | `trade_count` | trades | n_trades |
| trials the search ran | `trial_count` | `trial_count` | trials | n_trials |

## Metrics

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| log-loss of the weighted training class prior | `prior_logloss` | `prior_logloss` | prior log-loss | baseline |
| log-loss of the model on the evaluated block | `model_logloss` | `model_logloss` | model log-loss | loss |
| information beyond the prior, `1 − model / prior` | `relative_logloss_skill` | `relative_logloss_skill` | skill | accuracy, edge |
| the HPO objective value at the winner | `best_logloss` | `best_logloss` | best mean F2–F4 log-loss | best_value, score |
| annualised Sharpe of the 15m equity path | `sharpe` | `sharpe`, `selection_score_mean_sharpe` | Sharpe | return/risk |
| maximum drawdown of the 1m equity path | `max_drawdown` | `max_drawdown` | maxDD | DD |
| share of the fold spent in a position | `exposure` | `exposure` | exposure | utilisation |
| share of a fold's trades that ended positive | `hit_rate` | `hit_rate` | hit | win rate |
| mean cost-adjusted return of a trade | `average_trade_return` | `average_trade_return` | avg trade | expectancy, `avg_trade_ret` |
| equity at the end of the fold, starting from 1.0 | `final_equity` | `final_equity` | final equity | PnL |

## Artifacts

**One file per distinct artifact responsibility; no duplicate representations
of the same result.** One directory per ticker under `store_Assets_artifacts/`,
each file named after what it holds.

| file | written by | holds |
|---|---|---|
| `canonical_ss-01-hh-dd-MM.parquet` | `module_data/export.py` | the published canonical series |
| `features.parquet` | `module_ml/features.py` | X — 15 causal columns |
| `label_events.parquet` | `module_ml/labels.py` | Y — labels, the event flags and the event prices |
| `hyperparameter_search.json` | `module_ml/hpo.py` | the winning point of the search and the trial count |
| `oos_predictions.parquet` | `module_ml/train.py` | out-of-fold probabilities for the full windows; metrics score only the supervised subset |
| `model_evaluation.json` | `module_ml/train.py` | classification metrics per fold |
| `strategy_evaluation.json` | `module_ml/strategy.py` | the entry edge threshold and the PnL |
| `experiment_configuration.json` | `module_ml/status.py` | the a-priori experiment configuration, recorded at report time |
| `README.md` | `module_ml/status.py` | what the folder holds and what came out of it |

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
