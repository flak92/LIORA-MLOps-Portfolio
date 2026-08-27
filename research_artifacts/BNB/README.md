# BNB — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `experiment_configuration.json` next to this file records the configuration this run was executed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 45,189 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 10,061 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,343 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities, full windows | 2,350 KB |
| `hyperparameter_search.json` | the winning point of the search | 321 B |
| `model_evaluation.json` | classification metrics per fold | 3 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `experiment_configuration.json` | the configuration this run was executed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised subset of each.

## Labels

194,832 decisions, of which **194,823 supervised** (99.995%) — 4 events resolve ambiguously and 5 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 27,204, neutral 144,879, long 22,740 (194,823 total).

## Model

Search: 50 Optuna trials, best log-loss 0.791818. Winner: depth 2, eta 0.0195, 350 rounds, subsample 0.663, colsample 0.694, min_child_weight 3, lambda 0.3489, alpha 0.4544.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.830751 | 0.789641 | +4.95% | 0.0562 | 35,035 |
| F3 | 0.847689 | 0.788724 | +6.96% | 0.0761 | 35,040 |
| F4 | 0.850631 | 0.797089 | +6.29% | 0.0614 | 35,136 |
| **F5 — final holdout** | 0.851809 | 0.802036 | +5.84% | 0.0597 | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,035 |
| F3 | 66,857 | 14 | 35,040 | 35,040 |
| F4 | 101,905 | 6 | 35,136 | 35,136 |
| F5 | 137,031 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.31**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.692 | 16.7% | 98 | 53.1% | 2.79% | 1.1141 |
| F3 | -0.956 | 10.0% | 42 | 42.9% | 1.25% | 0.9348 |
| F4 | +0.977 | 9.0% | 40 | 50.0% | 0.95% | 1.0820 |
| **F5 — final holdout** | -0.322 | 13.2% | 41 | 41.5% | 0.79% | 0.9510 |

Final-holdout exits: upper_barrier 12, lower_barrier 10, vertical 19, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers BNB && python -m ml_module.labels --tickers BNB && python -m ml_module.hpo --tickers BNB && python -m ml_module.train --tickers BNB && python -m ml_module.strategy --tickers BNB && python -m ml_module.status --tickers BNB

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
