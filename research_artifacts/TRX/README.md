# TRX — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `experiment_configuration.json` next to this file records the configuration this run was executed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 38,853 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,635 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,340 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities, full windows | 2,334 KB |
| `hyperparameter_search.json` | the winning point of the search | 323 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `experiment_configuration.json` | the configuration this run was executed under | 3 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

194,832 decisions, of which **194,828 supervised** (99.998%) — 0 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 27,455, neutral 143,385, long 23,988 (194,828 total).

## Model

Search: 50 Optuna trials, best log-loss 0.801825. Winner: depth 2, eta 0.0132, 300 rounds, subsample 0.573, colsample 0.759, min_child_weight 27, lambda 0.3764, alpha 0.7618.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.819880 | 0.798189 | +2.65% | 35,024 |
| F3 | 0.822740 | 0.778842 | +5.34% | 35,024 |
| F4 | 0.880119 | 0.828445 | +5.87% | 35,120 |
| **F5 — final holdout** | 0.871183 | 0.835453 | +4.10% | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,822 | 14 | 35,040 | 35,024 |
| F3 | 66,860 | 16 | 35,040 | 35,024 |
| F4 | 101,911 | 5 | 35,136 | 35,120 |
| F5 | 137,036 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.19**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | -1.791 | 39.6% | 126 | 38.9% | 4.22% | 0.6775 |
| F3 | -1.184 | 19.9% | 96 | 43.8% | 2.58% | 0.8654 |
| F4 | +1.595 | 15.1% | 139 | 54.7% | 4.25% | 1.3618 |
| **F5 — final holdout** | -1.707 | 26.9% | 231 | 44.2% | 4.21% | 0.7411 |

Final-holdout exits: upper_barrier 64, lower_barrier 61, vertical 106, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers TRX && python -m ml_module.labels --tickers TRX && python -m ml_module.hpo --tickers TRX && python -m ml_module.train --tickers TRX && python -m ml_module.strategy --tickers TRX && python -m ml_module.status --tickers TRX

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
