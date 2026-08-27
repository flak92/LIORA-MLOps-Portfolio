# TRX — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per stage; `calibration.json` next to this file records the settings every number below was computed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 38,853 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,635 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,875 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities | 2,330 KB |
| `hyperparameter_search.json` | the winning point of the search | 318 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `calibration.json` | the settings all of the above were computed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four scored windows end to end.

## Labels

194,832 decisions, of which **194,828 supervised** (99.998%) — 0 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 27,455, neutral 143,385, long 23,988 (194,828 total). Mean uniqueness weight 0.0744.

## Model

Search: 50 Optuna trials, best objective 0.801648. Winner: depth 2, eta 0.0206, 200 rounds, subsample 0.529, colsample 0.712, min_child_weight 20, lambda 0.3941, alpha 0.3585.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.819911 | 0.798768 | +2.58% | 0.0461 | 35,040 |
| F3 | 0.822916 | 0.778357 | +5.41% | 0.0527 | 35,040 |
| F4 | 0.879912 | 0.827821 | +5.92% | 0.0503 | 35,136 |
| **F5 — final holdout** | 0.871235 | 0.835553 | +4.10% | 0.0410 | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,822 | 14 | 35,040 | 35,040 |
| F3 | 66,860 | 16 | 35,040 | 35,040 |
| F4 | 101,911 | 5 | 35,136 | 35,136 |
| F5 | 137,036 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.21**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 levels agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | -1.528 | 37.9% | 137 | 40.1% | 4.51% | 0.7049 |
| F3 | -0.307 | 17.4% | 95 | 50.5% | 2.45% | 0.9583 |
| F4 | +1.412 | 15.1% | 119 | 53.8% | 3.59% | 1.2384 |
| **F5 — final holdout** | -1.546 | 24.0% | 212 | 44.8% | 3.95% | 0.7703 |

Final-holdout exits: adverse 0, lower 53, upper 62, vertical 97.

## Reproducing this folder

    python -m ml_module.features --tickers TRX && python -m ml_module.labels --tickers TRX && python -m ml_module.hpo --tickers TRX && python -m ml_module.train --tickers TRX && python -m ml_module.strategy --tickers TRX && python -m ml_module.status --tickers TRX

F5 never participates in feature definition, hyper-parameter selection, threshold selection or strategy-rule selection — folds F2, F3, F4 carry every research decision. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
