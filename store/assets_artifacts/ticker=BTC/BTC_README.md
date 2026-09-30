# BTC — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One folder per asset, `ticker=BTC/`, one file per distinct artifact responsibility, and beside the folder the asset's partition of every family the chain writes; `BTC_parameters.json` next to this file is the one parameters file: its `hyperparameter_search_result` section is what the search chose, written when the search runs — the a-priori configuration is `module_ml/config.py` at the commit that ran it, not a copy in the folder.

## Files

| file | holds | size |
| --- | --- | --- |
| `catalogue/ticker=BTC/timeframe=1h/catalogue.parquet` | the catalogue on 1h — every definition offered on it, on the decision grid | 6,653 KB |
| `catalogue/ticker=BTC/timeframe=8h/catalogue.parquet` | the catalogue on 8h — every definition offered on it, on the decision grid | 1,332 KB |
| `catalogue/ticker=BTC/timeframe=1d/catalogue.parquet` | the catalogue on 1d — every definition offered on it, on the decision grid | 574 KB |
| `labels/ticker=BTC/timeframe=1h/labels.parquet` | Y — triple-barrier outcome and the event prices | 1,172 KB |
| `oos_predictions/ticker=BTC/timeframe=1h/oos_predictions.parquet` | out-of-sample class probabilities, full windows | 603 KB |
| `ticker=BTC/BTC_README.md` | this file | — |
| `ticker=BTC/BTC_barriers.json` | the promoted barrier geometry: the two multipliers of a trade, the label's own and the horizon token — a hand's choice; absent, the frozen constants are the asset's | — |
| `ticker=BTC/BTC_catalogue.json` | the feature layer's contract: the timeframes and their durations, the warm-up, the columns offered per timeframe and the default set — read once per stage | 5 KB |
| `ticker=BTC/BTC_feature_set.json` | the promoted feature set: its columns per timeframe, a hand's choice — absent, the default set is the asset's | — |
| `ticker=BTC/BTC_hyperparameter_point.json` | the promoted hyper-parameter point: the first trial of the search, a hand's choice — absent, the search draws every point | — |
| `ticker=BTC/BTC_model_evaluation.json` | classification metrics per fold | 9 KB |
| `ticker=BTC/BTC_parameters.json` | the one parameters file: what the search chose | 386 B |
| `ticker=BTC/BTC_strategy_evaluation.json` | threshold, PnL and the equity curve | 11 KB |

Each of the 3 catalogue partitions carries 4 rows more than `labels/ticker=BTC/timeframe=1h/labels.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions/ticker=BTC/timeframe=1h/oos_predictions.parquet` holds the 4 out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Feature set

The default set of the catalogue — no promoted file. The asset's feature set by timeframe — the set every fit reads; the feature id is the column with the timeframe appended:

| timeframe | columns |
| --- | --- |
| 1h | `exponential_smoothing20_minus_exponential_smoothing50_over_true_range_recursive_mean14`, `centered_recursive_mean_gain_share14`, `true_range_recursive_mean14_over_close`, `rolling_range_position20`, `logarithmic_volume_rolling_standard_score50` |
| 8h | `exponential_smoothing20_minus_exponential_smoothing50_over_true_range_recursive_mean14`, `centered_recursive_mean_gain_share14`, `true_range_recursive_mean14_over_close`, `rolling_range_position20`, `logarithmic_volume_rolling_standard_score50` |
| 1d | `exponential_smoothing20_minus_exponential_smoothing50_over_true_range_recursive_mean14`, `centered_recursive_mean_gain_share14`, `true_range_recursive_mean14_over_close`, `rolling_range_position20`, `logarithmic_volume_rolling_standard_score50` |

## Labels

44,228 decisions, of which **44,227 supervised** (99.998%) — 1 events resolve ambiguously and 0 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 6,025, neutral 32,631, long 5,571 (44,227 total).

## Model

Search: 8 Optuna trials, best best_cagr_validation_path -0.067349. Winner: depth 5, eta 0.1111, 150 rounds, subsample 0.985, colsample 0.916, min_child_weight 2, lambda 0.2659, alpha 0.0231.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.822111 | 1.054633 | -28.28% | 8,756 |
| F3 | 0.851337 | 0.915151 | -7.50% | 8,755 |
| F4 | 0.839082 | 0.811663 | +3.27% | 8,780 |
| **F5 — final holdout** | 0.826613 | 0.798614 | +3.39% | 14,444 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 3,476 | 4 | 8,760 | 8,756 |
| F3 | 12,239 | 1 | 8,760 | 8,755 |
| F4 | 20,998 | 1 | 8,784 | 8,780 |
| F5 | 29,779 | 4 | 14,444 | 14,444 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.3**. Cost 0.06% per side; the hierarchy gate requires the side to match the 1d trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | -1.076 | 22.2% | 304 | 43.4% | 11.67% | 0.8514 |
| F3 | -1.939 | 5.7% | 30 | 33.3% | 1.00% | 0.9583 |
| F4 | -0.088 | 5.5% | 36 | 50.0% | 1.20% | 0.9941 |
| **F5 — final holdout** | -0.602 | 11.8% | 85 | 45.9% | 1.77% | 0.9461 |

Final-holdout exits: upper_barrier 24, lower_barrier 16, vertical 45, ambiguous 0.

## Reproducing the ML artifacts in this folder

    python -m module_features.bars --tickers BTC && python -m module_features.catalogue --tickers BTC && python -m module_ml.labels --tickers BTC && python -m module_ml.hpo --tickers BTC && python -m module_ml.train --tickers BTC && python -m module_ml.strategy --tickers BTC && python -m module_ml.status --tickers BTC

The OHLCV is the asset's partition of the family `ohlcv_1m_canonical` — the market object the whole chain reads, outside the manifest above because its size moves with every top-up and this file is promised byte-reproducible.

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters, the entry edge threshold and, once a state is promoted, the feature set and the barrier geometry. The method is in `module_ml/skills/skill_methodology_ml.md`, the field names in `module_skills/skill_glossary.md`.
