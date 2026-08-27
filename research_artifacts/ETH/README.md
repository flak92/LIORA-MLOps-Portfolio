# ETH — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per stage; `calibration.json` next to this file records the settings every number below was computed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 52,672 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 10,166 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,961 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities | 2,383 KB |
| `hyperparameter_search.json` | the winning point of the search | 316 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `calibration.json` | the settings all of the above were computed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four scored windows end to end.

## Labels

194,832 decisions, of which **194,815 supervised** (99.991%) — 13 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 27,680, neutral 143,281, long 23,854 (194,815 total). Mean uniqueness weight 0.0755.

## Model

Search: 50 Optuna trials, best objective 0.814412. Winner: depth 6, eta 0.0112, 600 rounds, subsample 0.505, colsample 0.889, min_child_weight 22, lambda 0.8186, alpha 0.9971.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.861075 | 0.823970 | +4.31% | 0.0550 | 35,033 |
| F3 | 0.900116 | 0.826704 | +8.16% | 0.0731 | 35,040 |
| F4 | 0.850371 | 0.792561 | +6.80% | 0.0637 | 35,136 |
| **F5 — final holdout** | 0.862750 | 0.797368 | +7.58% | 0.0654 | 57,770 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,033 |
| F3 | 66,862 | 7 | 35,040 | 35,040 |
| F4 | 101,901 | 8 | 35,136 | 35,136 |
| F5 | 137,029 | 16 | 57,776 | 57,770 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.25**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 levels agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.464 | 15.4% | 158 | 48.7% | 4.86% | 1.0772 |
| F3 | -2.224 | 27.1% | 161 | 39.8% | 5.20% | 0.7769 |
| F4 | +0.933 | 13.5% | 110 | 49.1% | 3.45% | 1.1191 |
| **F5 — final holdout** | -0.643 | 29.0% | 194 | 43.3% | 3.76% | 0.8365 |

Final-holdout exits: adverse 0, lower 46, upper 52, vertical 96.

## Reproducing this folder

    python -m ml_module.features --tickers ETH && python -m ml_module.labels --tickers ETH && python -m ml_module.hpo --tickers ETH && python -m ml_module.train --tickers ETH && python -m ml_module.strategy --tickers ETH && python -m ml_module.status --tickers ETH

F5 never participates in feature definition, hyper-parameter selection, threshold selection or strategy-rule selection — folds F2, F3, F4 carry every research decision. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
