# SOL — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per stage; `calibration.json` next to this file records the settings every number below was computed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 43,691 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,967 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,956 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities | 2,368 KB |
| `hyperparameter_search.json` | the winning point of the search | 318 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `calibration.json` | the settings all of the above were computed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four scored windows end to end.

## Labels

194,832 decisions, of which **194,820 supervised** (99.994%) — 8 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 25,254, neutral 145,753, long 23,813 (194,820 total). Mean uniqueness weight 0.0737.

## Model

Search: 50 Optuna trials, best objective 0.779188. Winner: depth 3, eta 0.0111, 550 rounds, subsample 0.871, colsample 0.668, min_child_weight 25, lambda 0.1750, alpha 0.3189.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.836280 | 0.792463 | +5.24% | 0.0551 | 35,032 |
| F3 | 0.832907 | 0.776211 | +6.81% | 0.0693 | 35,040 |
| F4 | 0.804853 | 0.768888 | +4.47% | 0.0409 | 35,136 |
| **F5 — final holdout** | 0.834917 | 0.787791 | +5.64% | 0.0580 | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,032 |
| F3 | 66,852 | 16 | 35,040 | 35,040 |
| F4 | 101,903 | 5 | 35,136 | 35,136 |
| F5 | 137,033 | 11 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.31**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 levels agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | -0.960 | 26.5% | 59 | 42.4% | 1.96% | 0.8484 |
| F3 | +0.538 | 13.3% | 76 | 48.7% | 2.27% | 1.0816 |
| F4 | +0.041 | 11.4% | 50 | 42.0% | 1.72% | 0.9986 |
| **F5 — final holdout** | +0.585 | 13.5% | 89 | 53.9% | 1.63% | 1.1024 |

Final-holdout exits: adverse 0, lower 35, upper 17, vertical 37.

## Reproducing this folder

    python -m ml_module.features --tickers SOL && python -m ml_module.labels --tickers SOL && python -m ml_module.hpo --tickers SOL && python -m ml_module.train --tickers SOL && python -m ml_module.strategy --tickers SOL && python -m ml_module.status --tickers SOL

F5 never participates in feature definition, hyper-parameter selection, threshold selection or strategy-rule selection — folds F2, F3, F4 carry every research decision. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
