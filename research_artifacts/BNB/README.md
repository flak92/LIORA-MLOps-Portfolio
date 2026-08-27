# BNB — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `calibration.json` next to this file records the settings every number below was computed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 45,189 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 10,061 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,855 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities | 2,362 KB |
| `hyperparameter_search.json` | the winning point of the search | 321 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `calibration.json` | the settings all of the above were computed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four scored windows end to end.

## Labels

194,832 decisions, of which **194,823 supervised** (99.995%) — 4 events resolve ambiguously and 5 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 27,204, neutral 144,879, long 22,740 (194,823 total). Mean uniqueness weight 0.0746.

## Model

Search: 50 Optuna trials, best log-loss 0.791576. Winner: depth 3, eta 0.0129, 550 rounds, subsample 0.717, colsample 0.631, min_child_weight 11, lambda 0.2024, alpha 0.0115.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.830917 | 0.790455 | +4.87% | 0.0625 | 35,035 |
| F3 | 0.847742 | 0.787943 | +7.05% | 0.0818 | 35,040 |
| F4 | 0.850638 | 0.796332 | +6.38% | 0.0650 | 35,136 |
| **F5 — final holdout** | 0.851856 | 0.800497 | +6.03% | 0.0690 | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,035 |
| F3 | 66,857 | 14 | 35,040 | 35,040 |
| F4 | 101,905 | 6 | 35,136 | 35,136 |
| F5 | 137,031 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.34**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 levels agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +1.062 | 7.9% | 77 | 50.6% | 2.41% | 1.1360 |
| F3 | -0.012 | 7.7% | 54 | 44.4% | 1.42% | 0.9959 |
| F4 | +0.553 | 7.1% | 39 | 48.7% | 1.02% | 1.0429 |
| **F5 — final holdout** | -1.089 | 20.3% | 52 | 36.5% | 0.97% | 0.8574 |

Final-holdout exits: upper_barrier 17, lower_barrier 12, vertical 23, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers BNB && python -m ml_module.labels --tickers BNB && python -m ml_module.hpo --tickers BNB && python -m ml_module.train --tickers BNB && python -m ml_module.strategy --tickers BNB && python -m ml_module.status --tickers BNB

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry every research decision. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
