# ZEC — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `calibration.json` next to this file records the settings every number below was computed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 39,755 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,678 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,803 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities | 2,348 KB |
| `hyperparameter_search.json` | the winning point of the search | 319 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `calibration.json` | the settings all of the above were computed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four scored windows end to end.

## Labels

194,832 decisions, of which **194,723 supervised** (99.944%) — 0 events resolve ambiguously and 109 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 24,135, neutral 148,163, long 22,425 (194,723 total). Mean uniqueness weight 0.0727.

## Model

Search: 50 Optuna trials, best log-loss 0.771241. Winner: depth 2, eta 0.0184, 400 rounds, subsample 0.540, colsample 0.912, min_child_weight 38, lambda 2.8035, alpha 0.1664.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.812581 | 0.791446 | +2.60% | 0.0075 | 35,038 |
| F3 | 0.790809 | 0.767091 | +3.00% | 0.0239 | 34,953 |
| F4 | 0.792828 | 0.755185 | +4.75% | 0.0258 | 35,124 |
| **F5 — final holdout** | 0.803932 | 0.757809 | +5.74% | 0.0314 | 57,772 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,038 |
| F3 | 66,866 | 8 | 35,040 | 34,953 |
| F4 | 101,823 | 4 | 35,136 | 35,124 |
| F5 | 136,935 | 16 | 57,776 | 57,772 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.0** — **fallback**, no threshold reaches 30 trades in every validation fold. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 levels agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.426 | 7.5% | 18 | 50.0% | 0.72% | 1.0301 |
| F3 | -2.813 | 35.1% | 86 | 37.2% | 2.56% | 0.6529 |
| F4 | -0.688 | 25.2% | 52 | 48.1% | 1.59% | 0.8360 |
| **F5 — final holdout** | -0.319 | 33.8% | 120 | 46.7% | 2.28% | 0.8459 |

Final-holdout exits: upper_barrier 29, lower_barrier 31, vertical 60, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers ZEC && python -m ml_module.labels --tickers ZEC && python -m ml_module.hpo --tickers ZEC && python -m ml_module.train --tickers ZEC && python -m ml_module.strategy --tickers ZEC && python -m ml_module.status --tickers ZEC

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry every research decision. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
