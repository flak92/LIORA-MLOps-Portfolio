# BTC — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `experiment_configuration.json` next to this file records the configuration this run was executed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 52,999 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 10,165 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,748 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities, full windows | 2,383 KB |
| `hyperparameter_search.json` | the winning point of the search | 323 B |
| `model_evaluation.json` | classification metrics per fold | 3 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `experiment_configuration.json` | the configuration this run was executed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised subset of each.

## Labels

194,832 decisions, of which **194,825 supervised** (99.996%) — 7 events resolve ambiguously and 0 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 26,601, neutral 144,031, long 24,193 (194,825 total). Mean uniqueness weight 0.0763.

## Model

Search: 50 Optuna trials, best log-loss 0.811350. Winner: depth 5, eta 0.0102, 450 rounds, subsample 0.532, colsample 0.785, min_child_weight 21, lambda 0.1025, alpha 0.3184.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.873751 | 0.821631 | +5.97% | 0.0513 | 35,039 |
| F3 | 0.919331 | 0.817142 | +11.12% | 0.1001 | 35,034 |
| F4 | 0.877542 | 0.795278 | +9.37% | 0.0846 | 35,136 |
| **F5 — final holdout** | 0.866569 | 0.797792 | +7.94% | 0.0883 | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,824 | 16 | 35,040 | 35,039 |
| F3 | 66,875 | 4 | 35,040 | 35,034 |
| F4 | 101,908 | 5 | 35,136 | 35,136 |
| F5 | 137,033 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.28**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +1.361 | 8.0% | 58 | 55.2% | 1.78% | 1.1466 |
| F3 | -1.301 | 16.8% | 87 | 40.2% | 2.53% | 0.8965 |
| F4 | -0.609 | 13.2% | 104 | 45.2% | 3.19% | 0.9342 |
| **F5 — final holdout** | -0.938 | 18.4% | 186 | 44.1% | 3.48% | 0.8696 |

Final-holdout exits: upper_barrier 54, lower_barrier 43, vertical 89, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers BTC && python -m ml_module.labels --tickers BTC && python -m ml_module.hpo --tickers BTC && python -m ml_module.train --tickers BTC && python -m ml_module.strategy --tickers BTC && python -m ml_module.status --tickers BTC

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
