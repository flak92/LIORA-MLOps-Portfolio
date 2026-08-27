# XRP — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `calibration.json` next to this file records the settings every number below was computed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 39,915 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,670 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,749 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities | 2,359 KB |
| `hyperparameter_search.json` | the winning point of the search | 319 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `calibration.json` | the settings all of the above were computed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four scored windows end to end.

## Labels

194,832 decisions, of which **194,828 supervised** (99.998%) — 0 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 26,240, neutral 146,600, long 21,988 (194,828 total). Mean uniqueness weight 0.0747.

## Model

Search: 50 Optuna trials, best log-loss 0.774484. Winner: depth 5, eta 0.0236, 150 rounds, subsample 0.621, colsample 0.825, min_child_weight 46, lambda 1.4754, alpha 0.0144.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.810407 | 0.776041 | +4.24% | 0.0639 | 35,040 |
| F3 | 0.829181 | 0.763212 | +7.96% | 0.0807 | 35,040 |
| F4 | 0.853124 | 0.784200 | +8.08% | 0.0687 | 35,136 |
| **F5 — final holdout** | 0.840814 | 0.776275 | +7.68% | 0.0796 | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,825 | 11 | 35,040 | 35,040 |
| F3 | 66,869 | 7 | 35,040 | 35,040 |
| F4 | 101,912 | 4 | 35,136 | 35,136 |
| F5 | 137,036 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.0**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 levels agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | -0.683 | 42.7% | 238 | 45.4% | 7.88% | 0.7877 |
| F3 | -1.016 | 28.6% | 261 | 42.9% | 6.69% | 0.7277 |
| F4 | +0.091 | 34.1% | 228 | 44.3% | 6.34% | 0.9698 |
| **F5 — final holdout** | +0.195 | 34.5% | 347 | 47.0% | 6.35% | 1.0234 |

Final-holdout exits: upper_barrier 103, lower_barrier 97, vertical 147, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers XRP && python -m ml_module.labels --tickers XRP && python -m ml_module.hpo --tickers XRP && python -m ml_module.train --tickers XRP && python -m ml_module.strategy --tickers XRP && python -m ml_module.status --tickers XRP

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry every research decision. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
