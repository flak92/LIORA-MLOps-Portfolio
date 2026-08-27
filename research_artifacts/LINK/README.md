# LINK — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per stage; `calibration.json` next to this file records the settings every number below was computed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 43,312 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,870 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,935 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities | 2,370 KB |
| `hyperparameter_search.json` | the winning point of the search | 317 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `calibration.json` | the settings all of the above were computed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four scored windows end to end.

## Labels

194,832 decisions, of which **194,831 supervised** (99.999%) — 1 events resolve ambiguously and 0 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 25,127, neutral 146,901, long 22,803 (194,831 total). Mean uniqueness weight 0.0729.

## Model

Search: 50 Optuna trials, best objective 0.774413. Winner: depth 6, eta 0.0117, 400 rounds, subsample 0.545, colsample 0.904, min_child_weight 30, lambda 0.2428, alpha 0.1216.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.807240 | 0.782245 | +3.10% | 0.0199 | 35,039 |
| F3 | 0.817418 | 0.776995 | +4.95% | 0.0395 | 35,040 |
| F4 | 0.810195 | 0.764000 | +5.70% | 0.0542 | 35,136 |
| **F5 — final holdout** | 0.815402 | 0.771363 | +5.40% | 0.0431 | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,825 | 15 | 35,040 | 35,039 |
| F3 | 66,863 | 16 | 35,040 | 35,040 |
| F4 | 101,914 | 5 | 35,136 | 35,136 |
| F5 | 137,039 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.23**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 levels agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | -1.540 | 19.0% | 30 | 36.7% | 1.10% | 0.8449 |
| F3 | -0.077 | 13.7% | 99 | 47.5% | 3.38% | 0.9810 |
| F4 | -0.643 | 19.3% | 88 | 40.9% | 2.77% | 0.8916 |
| **F5 — final holdout** | -1.052 | 27.7% | 178 | 44.4% | 3.53% | 0.7425 |

Final-holdout exits: adverse 0, lower 41, upper 48, vertical 89.

## Reproducing this folder

    python -m ml_module.features --tickers LINK && python -m ml_module.labels --tickers LINK && python -m ml_module.hpo --tickers LINK && python -m ml_module.train --tickers LINK && python -m ml_module.strategy --tickers LINK && python -m ml_module.status --tickers LINK

F5 never participates in feature definition, hyper-parameter selection, threshold selection or strategy-rule selection — folds F2, F3, F4 carry every research decision. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
