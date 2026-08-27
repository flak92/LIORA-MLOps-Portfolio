# Skill: glossary — one concept, one name

**Names must be self-explanatory before they are project-specific. Prefer
standard domain terminology. A glossary confirms meaning; it must not be
required to decode an obscure name.**

Every concept below has exactly one name in the code, one key in the artifacts
and one label in the interface. A synonym never enters, and a new concept is
registered here in the same commit that introduces it. Names that are standard
in the field (`fold`, `purge`, `embargo`, out-of-sample, Sharpe, MCC) appear as
confirmation; the rest of the concept column states what the name means.

## Validation and folds

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| one chronological segment of the research window | `fold`, `fold_id` | `fold_2` … `fold_4` | `F1` … `F5` | split, period, chunk |
| the segment boundaries | `fold_bounds()`, `FOLD_BOUNDS_MS` | `folds.bounds_utc` | — | split_bounds |
| the folds that choose every parameter | `VALIDATION_FOLD_IDS` = (2, 3, 4) | `validation` | `F2`–`F4` | test folds, CV folds |
| the fold that is only ever evaluated | `FINAL_HOLDOUT_FOLD_ID` = 5 | `final_holdout`, `final_holdout_fold_id` | `F5 — final holdout (out-of-sample)` | test, test set, locked test, final OOS |
| the evaluated block of a fold, and which one a prediction belongs to | `oos`, `oos_fold_id` | `oos_fold_id` (parquet column) | out-of-sample | test block, test period |
| dropping training events that overlap the evaluated block | `purge` — `event_end_ts <= oos_start` | `folds.purge_rule` | purged | gap, buffer |
| a forced wait after the evaluated block — **width zero here**, forward chaining needs none | `embargo` | `folds.embargo` | — | cooldown, post-test embargo |
| bars consumed before the first decision is allowed | `WARMUP_4H_BARS` = 200, `WARMUP_END_MS` | `folds.warmup_4h_bars`, `n_warmup_excluded` | warm-up excluded | burn-in |

## Market object

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the studied series, and the only series below the ingest boundary | `ohlcv_1m_canonical` and its aggregates | `canonical_1m.parquet` | canonical dataset | fused series, index, blended price |
| a data provider, above the ingest boundary only | `binance` / `bybit`, in `data_module` | `venues.*`, `pct_binance` | Raw source | venue or exchange used below ingest |
| which provider a canonical minute came from | `source`, `source_switches` | same | primary / secondary / forward fill | — |
| a minute with no observed trade | `volume = 0`, `zero_volume` | `zero_volume`, `zero_volume_bars` | zero-volume bars | carried-forward price (true only of forward-filled minutes) |
| a synthesized continuity minute | `source = 'ffill'` | `ffill_bars` | forward fill | gap, missing bar |
| quality columns that are never features | `binance_valid`, `bybit_valid`, `rel_divergence` | same | — | signal, feature |

## Event and sample

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the moment a decision may be taken — close of the 15m bar | `decision_ts` | `decision_ts` | — | signal time |
| the first tradable minute after the decision | `entry_ts` | `entry_ts` | — | fill time |
| the canonical open of that minute | `entry_price` | `entry_price` | — | `p0` as an identifier (`P₀` stays in the equations) |
| the take-profit price of a long, the stop of a short | `upper_barrier` | `upper_barrier` | upper_barrier | `upper`, ceiling, band |
| the stop of a long, the take-profit of a short | `lower_barrier` | `lower_barrier` | lower_barrier | `lower`, floor, band |
| the vertical barrier, in minutes (240 = 16 × 15m bars) | `HORIZON_MINUTES`, `HORIZON_MS` | `labels.horizon_minutes` | 240-minute horizon | HORIZON_BARS, W, H |
| the exclusive end of the event | `event_end_ts` | `event_end_ts` | — | exit time |
| the price that closes the event | `exit_reference_price` | `exit_reference_price` | — | exit_ref |
| how the event ended | `event_resolution` | `event_resolution`, `exit_counts.*` | upper_barrier / lower_barrier / vertical / ambiguous | reason, exit_reason |
| the four resolutions | `EVENT_RESOLUTION_{UPPER_BARRIER, LOWER_BARRIER, VERTICAL, AMBIGUOUS}` | `labels.event_resolution_codes` | — | bare 1 / −1 / 0 / 9 |
| the entry minute traded at all — knowable at `entry_ts`, may gate an entry | `entry_observable` | `entry_observable`, `unobservable` | unobservable entry | tradable, valid entry |
| the event can be classified — knowable only afterwards, never gates an entry | `label_valid` | `label_valid`, `ambiguous` | ambiguous | masked, mask_ok |
| the supervised population: both of the above | `sample_valid` | `trainable`, `trainable_pct` | trainable rows | valid rows |
| how little the event overlaps its neighbours | `weight` (average uniqueness) | `weight`, `uniqueness_weight_mean` | mean uniqueness weight | sample weight, class weight |

## Signal and strategy

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the model's directional lean, `p_long − p_short` | `directional_probability_edge` | — | edge | `edge` as a code name |
| how much of that lean a signal must carry to be traded | `entry_edge_threshold` (τ) | `entry_edge_threshold` | τ (entry edge threshold) | `tau` as an identifier |
| the grid searched for it | `ENTRY_EDGE_THRESHOLD_GRID` | `strategy.entry_edge_threshold_grid` | — | TAU_GRID |
| whether any threshold on the grid cleared the trade floor | `entry_edge_threshold_constraint_met` | same | fallback | tau_constraint_met |
| the trade floor — a selection guardrail, not an acceptance gate | `MIN_TRADES_PER_VALIDATION_FOLD` = 30 | `strategy.min_trades_per_validation_fold` | — | TAU_MIN_TRADES, acceptance gate |
| how many levels must agree with the side | `AGREE_MIN`, `n_agree` | `gate_min_agree`, `strategy.hierarchy_min_agree` | at least 2 of 3 levels agree | confirmation, filter |
| replaying the strategy over the canonical price path | `backtest()` | `strategy_evaluation.json` | STRATEGY | live execution, exchange execution |
| the execution cost charged on entry and on exit | `COST_PER_SIDE` = 0.0006 | `cost_per_side` | cost per side | costs_per_side, fees |

The symbol τ may stay in equations and in table headers; its first use in any
document or on any page spells out `entry edge threshold`.

## Metrics

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| log-loss of the weighted training class prior | `prior_logloss` | `prior_logloss` | prior log-loss | baseline |
| log-loss of the model on the evaluated block | `model_logloss` | `model_logloss` | model log-loss | loss |
| information beyond the prior, `1 − model / prior` | `relative_logloss_skill` | `relative_logloss_skill` | skill | accuracy, edge |
| Matthews correlation coefficient | `mcc` | `mcc` | MCC | correlation |
| the HPO objective value at the winner | `best_logloss` | `best_logloss` | best mean F2–F4 log-loss | best_value, score |
| annualised Sharpe of the 15m equity path | `sharpe` | `sharpe`, `selection_score_mean_sharpe` | Sharpe | return/risk |
| maximum drawdown of the 1m equity path | `max_drawdown` | `max_drawdown` | maxDD | DD |
| share of the fold spent in a position | `exposure` | `exposure` | exposure | utilisation |
| equity at the end of the fold, starting from 1.0 | `final_equity` | `final_equity` | final equity | PnL |

## Artifacts

**One file per distinct artifact responsibility; no duplicate representations
of the same result.** One directory per ticker under `research_artifacts/`,
each file named after what it holds.

| file | written by | holds |
|---|---|---|
| `canonical_1m.parquet` | `data_module/export.py` | the published canonical series |
| `features.parquet` | `ml_module/features.py` | X — 15 causal columns |
| `label_events.parquet` | `ml_module/labels.py` | Y — labels, weights and the event prices |
| `hyperparameter_search.json` | `ml_module/hpo.py` | the search space and its winner |
| `oos_predictions.parquet` | `ml_module/train.py` | out-of-fold probabilities |
| `model_evaluation.json` | `ml_module/train.py` | classification metrics per fold |
| `strategy_evaluation.json` | `ml_module/strategy.py` | the entry edge threshold and the PnL |
| `calibration.json` | `ml_module/status.py` | the settings every number in the folder was computed under |
| `README.md` | `ml_module/status.py` | what the folder holds and what came out of it |

## Features

| family | computes | levels |
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
