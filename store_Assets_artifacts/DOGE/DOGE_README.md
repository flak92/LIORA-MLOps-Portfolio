# DOGE — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `DOGE_parameters.json` next to this file is the one parameters file: the a-priori experiment configuration plus the winning point of the Optuna→XGB search, written when the search runs — it is not artifact provenance.

## Files

| file | holds | size |
| --- | --- | --- |
| `DOGE_parameters.json` | the one parameters file: a-priori configuration + the Optuna→XGB winner | 4 KB |
| `DOGE_features_ss-15-hh-dd-MM.parquet` | X — the five 15m family columns on the decision grid | 7,458 KB |
| `DOGE_features_ss-mm-01-dd-MM.parquet` | X — the five 1h family columns on the decision grid | 2,240 KB |
| `DOGE_features_ss-mm-04-dd-MM.parquet` | X — the five 4h family columns on the decision grid | 1,241 KB |
| `DOGE_label_events_ss-15-hh-dd-MM.parquet` | Y — triple-barrier outcome and the event prices | 5,554 KB |
| `DOGE_model_evaluation.json` | classification metrics per fold | 2 KB |
| `DOGE_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-fold class probabilities, full windows | 2,371 KB |
| `DOGE_README.md` | this file | — |
| `DOGE_strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |

Each of the three feature parquets carries 16 rows more than `DOGE_label_events_ss-15-hh-dd-MM.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `DOGE_oos_predictions_ss-15-hh-dd-MM.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

194,832 decisions, of which **194,826 supervised** (99.997%) — 0 events resolve ambiguously and 6 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 26,276, neutral 145,293, long 23,257 (194,826 total).

## Model

Search: 50 Optuna trials, best log-loss 0.789115. Winner: depth 5, eta 0.0146, 250 rounds, subsample 0.521, colsample 0.907, min_child_weight 23, lambda 0.3100, alpha 0.0933.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.846671 | 0.782841 | +7.54% | 35,022 |
| F3 | 0.853661 | 0.793673 | +7.03% | 35,024 |
| F4 | 0.844939 | 0.790833 | +6.40% | 35,120 |
| **F5 — final holdout** | 0.847052 | 0.789915 | +6.75% | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,821 | 15 | 35,040 | 35,022 |
| F3 | 66,858 | 16 | 35,040 | 35,024 |
| F4 | 101,910 | 4 | 35,136 | 35,120 |
| F5 | 137,034 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.19**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +1.819 | 28.6% | 289 | 50.9% | 9.02% | 1.9668 |
| F3 | -0.799 | 37.9% | 268 | 44.4% | 7.98% | 0.7746 |
| F4 | +1.842 | 25.9% | 202 | 54.0% | 6.40% | 1.9881 |
| **F5 — final holdout** | -0.388 | 42.9% | 285 | 46.0% | 5.47% | 0.7919 |

Final-holdout exits: upper_barrier 71, lower_barrier 75, vertical 139, ambiguous 0.

## Reproducing the ML artifacts in this folder

    python -m module_ml.features --tickers DOGE && python -m module_ml.labels --tickers DOGE && python -m module_ml.hpo --tickers DOGE && python -m module_ml.train --tickers DOGE && python -m module_ml.strategy --tickers DOGE && python -m module_ml.status --tickers DOGE

The OHLCV itself lives only in the DuckDB tables — the market object the whole chain reads; the asset folder carries no price series.

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `module_skills/methodology_ml.md`, the field names in `module_skills/glossary.md`.
