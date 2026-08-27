# DOGE — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `experiment_configuration.json` next to this file records the configuration this run was executed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 44,804 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,856 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 6,029 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities, full windows | 2,378 KB |
| `hyperparameter_search.json` | the winning point of the search | 321 B |
| `model_evaluation.json` | classification metrics per fold | 3 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `experiment_configuration.json` | the configuration this run was executed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised subset of each.

## Labels

194,832 decisions, of which **194,826 supervised** (99.997%) — 0 events resolve ambiguously and 6 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 26,276, neutral 145,293, long 23,257 (194,826 total). Mean uniqueness weight 0.0752.

## Model

Search: 50 Optuna trials, best log-loss 0.789640. Winner: depth 6, eta 0.0116, 400 rounds, subsample 0.546, colsample 0.691, min_child_weight 19, lambda 0.4908, alpha 0.4573.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.846750 | 0.782763 | +7.56% | 0.0979 | 35,038 |
| F3 | 0.853856 | 0.795407 | +6.85% | 0.0879 | 35,040 |
| F4 | 0.844815 | 0.790750 | +6.40% | 0.0773 | 35,136 |
| **F5 — final holdout** | 0.847102 | 0.789644 | +6.78% | 0.0725 | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,821 | 15 | 35,040 | 35,038 |
| F3 | 66,858 | 16 | 35,040 | 35,040 |
| F4 | 101,910 | 4 | 35,136 | 35,136 |
| F5 | 137,034 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.31**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +1.698 | 16.9% | 169 | 50.3% | 5.37% | 1.5777 |
| F3 | -0.588 | 27.3% | 169 | 45.6% | 5.18% | 0.8641 |
| F4 | +1.039 | 16.7% | 92 | 55.4% | 3.13% | 1.3324 |
| **F5 — final holdout** | +0.880 | 20.7% | 113 | 53.1% | 2.21% | 1.2242 |

Final-holdout exits: upper_barrier 21, lower_barrier 33, vertical 59, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers DOGE && python -m ml_module.labels --tickers DOGE && python -m ml_module.hpo --tickers DOGE && python -m ml_module.train --tickers DOGE && python -m ml_module.strategy --tickers DOGE && python -m ml_module.status --tickers DOGE

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
