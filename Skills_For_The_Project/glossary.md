# Skill: glossary — one concept, one name

Every concept in this repository has **exactly one name in the code, one key in
the artifacts and one label in the interface**. A synonym never enters. A new
concept is added to this table in the same commit that introduces it.

Why this is a rule and not a preference: several names for one thing multiply
the context anyone has to load before they can act, and force the reader to
decide whether `test`, `test_fold` and `F5` are one thing or three. One name is
one vector — see `agent-first-development.md`.

## Validation

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| chronological data segment | `fold` | `fold_<n>` | `F1`…`F5` | split, period, chunk |
| folds that choose parameters | `VALIDATION_FOLD_IDS` | `validation` | `F2–F4` | test folds, CV folds |
| fold used only to evaluate | `FINAL_HOLDOUT_FOLD_ID` | `final_holdout`, `final_holdout_fold_id` | `F5 — final holdout (out-of-sample)` | test, test set, locked test, holdout set |
| fold boundaries | `fold_bounds()` | — | — | split_bounds |
| which fold a prediction belongs to | `oos_fold_id` (parquet column) | `oos_fold_id` | — | split |
| removing overlapping training events | `purge` (`event_end_ts <= oos_start`) | — | — | gap, buffer |
| forced wait after a fold | `embargo` — **width zero here**, forward chaining does not need one | — | — | cooldown |
| warm-up before any decision | `WARMUP_END_MS` (200 × 4h bars) | `n_warmup_excluded` | warm-up excl | burn-in |

## Market object

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| the studied series | `ohlcv_1m_canonical` and its bars | — | canonical dataset | fused series, index, blended price |
| a data provider | `binance` / `bybit` in `data_module` only | `venues.*`, `pct_binance` | Raw source: … | venue (below ingest), exchange (below ingest) |
| where a minute came from | `source`, `source_switches` | same | primary / secondary / forward fill | — |
| quality columns that are not features | `binance_valid`, `bybit_valid`, `rel_divergence`, `zero_volume` | same | — | signal, feature |

## Event and sample

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| decision time | `decision_ts` | `decision_ts` | — | signal time |
| entry time (a 1-minute bucket) | `entry_ts` | `entry_ts` | — | fill time |
| entry price | `entry_price` | `entry_price` | — | p0 |
| exclusive end of the event | `event_end_ts` | `event_end_ts` | — | exit time |
| price closing the event | `exit_reference_price` | `exit_reference_price` | — | exit_ref |
| how the event ended | `event_resolution` | `event_resolution` | upper / lower / vertical / adverse | reason, exit_reason |
| the four resolutions | `EVENT_RESOLUTION_{UPPER_BARRIER,LOWER_BARRIER,VERTICAL,AMBIGUOUS}` | — | — | bare 1 / −1 / 0 / 9 |
| entry minute traded | `entry_observable` | `entry_observable` | — | tradable, valid entry |
| event can be classified | `label_valid` | `label_valid` | ambiguous | masked, mask_ok |
| the supervised population | `sample_valid` | `trainable` | trainable | valid rows |
| horizon in minutes | `HORIZON_MINUTES` | — | — | W |

## Signal and strategy

| concept | code | artifact key | UI label | never |
|---|---|---|---|---|
| model's directional lean | `directional_probability_edge` (`p_long − p_short`) | — | edge | edge (as a bare name) |
| entry threshold | `entry_edge_threshold` (τ) | `entry_edge_threshold` | τ | tau (as a bare name) |
| grid searched for it | `ENTRY_EDGE_THRESHOLD_GRID` | — | — | TAU_GRID |
| selection guardrail | `MIN_TRADES_PER_VALIDATION_FOLD` | — | — | TAU_MIN_TRADES, acceptance gate |
| information beyond the prior | `relative_logloss_skill` | `relative_logloss_skill` | skill | accuracy, edge |

The symbol `τ` may stay in equations; its first use in any document spells out
`entry_edge_threshold`.

## Artifacts

One directory per ticker under `research_artifacts/`, one file per stage, the
stage name and nothing else:

| file | written by | holds |
|---|---|---|
| `canonical_1m.parquet` | `data_module/export.py` | the published canonical series |
| `features.parquet` | `ml_module/features.py` | X, 15 causal columns |
| `label_events.parquet` | `ml_module/labels.py` | Y and the event prices |
| `hyperparameter_search.json` | `ml_module/hpo.py` | winner and trial count |
| `oos_predictions.parquet` | `ml_module/train.py` | out-of-fold probabilities |
| `model_evaluation.json` | `ml_module/train.py` | classification metrics |
| `strategy_evaluation.json` | `ml_module/strategy.py` | τ and PnL |

## Features

Five families × three levels, each named after what it computes:

`ema20_minus_ema50_over_atr14` · `centered_rsi14` · `atr14_over_close` ·
`range_position_20` · `log_volume_zscore_50`, suffixed `_15m`, `_1h`, `_4h`.
Never `trend`, `momentum`, `volatility`, `structure`, `activity` — those name a
category, not a computation.
