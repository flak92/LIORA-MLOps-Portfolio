# BTC — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `experiment_configuration.json` next to this file records the configuration this run was executed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 52,999 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 10,165 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,265 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities, full windows | 2,387 KB |
| `hyperparameter_search.json` | the winning point of the search | 321 B |
| `model_evaluation.json` | classification metrics per fold | 3 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `experiment_configuration.json` | the configuration this run was executed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised subset of each.

## Labels

194,832 decisions, of which **194,825 supervised** (99.996%) — 7 events resolve ambiguously and 0 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 26,601, neutral 144,031, long 24,193 (194,825 total).

## Model

Search: 50 Optuna trials, best log-loss 0.811097. Winner: depth 5, eta 0.0124, 550 rounds, subsample 0.525, colsample 0.649, min_child_weight 32, lambda 2.8079, alpha 0.7831.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.873557 | 0.820603 | +6.06% | 0.0474 | 35,039 |
| F3 | 0.919296 | 0.817670 | +11.05% | 0.1030 | 35,034 |
| F4 | 0.877528 | 0.795017 | +9.40% | 0.0894 | 35,136 |
| **F5 — final holdout** | 0.866520 | 0.797182 | +8.00% | 0.0917 | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,824 | 16 | 35,040 | 35,039 |
| F3 | 66,875 | 4 | 35,040 | 35,034 |
| F4 | 101,908 | 5 | 35,136 | 35,136 |
| F5 | 137,033 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.27**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.557 | 7.5% | 66 | 54.5% | 2.12% | 1.0579 |
| F3 | -0.179 | 10.2% | 83 | 44.6% | 2.69% | 0.9838 |
| F4 | -1.265 | 21.8% | 136 | 44.9% | 4.51% | 0.8607 |
| **F5 — final holdout** | -0.775 | 22.0% | 237 | 46.0% | 4.49% | 0.8743 |

Final-holdout exits: upper_barrier 66, lower_barrier 56, vertical 115, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers BTC && python -m ml_module.labels --tickers BTC && python -m ml_module.hpo --tickers BTC && python -m ml_module.train --tickers BTC && python -m ml_module.strategy --tickers BTC && python -m ml_module.status --tickers BTC

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
