# ADA — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `experiment_configuration.json` next to this file records the configuration this run was executed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 37,865 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,576 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,777 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities, full windows | 2,344 KB |
| `hyperparameter_search.json` | the winning point of the search | 321 B |
| `model_evaluation.json` | classification metrics per fold | 3 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `experiment_configuration.json` | the configuration this run was executed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised subset of each.

## Labels

194,832 decisions, of which **194,818 supervised** (99.993%) — 10 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 25,288, neutral 147,677, long 21,853 (194,818 total). Mean uniqueness weight 0.0734.

## Model

Search: 50 Optuna trials, best log-loss 0.771792. Winner: depth 2, eta 0.0100, 450 rounds, subsample 0.516, colsample 0.710, min_child_weight 8, lambda 0.6921, alpha 0.9854.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.810366 | 0.770984 | +4.86% | 0.0418 | 35,038 |
| F3 | 0.818446 | 0.769932 | +5.93% | 0.0456 | 35,040 |
| F4 | 0.817473 | 0.774462 | +5.26% | 0.0359 | 35,136 |
| **F5 — final holdout** | 0.816381 | 0.770129 | +5.67% | 0.0405 | 57,768 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,038 |
| F3 | 66,867 | 7 | 35,040 | 35,040 |
| F4 | 101,910 | 4 | 35,136 | 35,136 |
| F5 | 137,034 | 16 | 57,776 | 57,768 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated.

## Strategy

Entry edge threshold **0.24**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.059 | 14.9% | 69 | 44.9% | 2.16% | 0.9980 |
| F3 | +0.142 | 14.3% | 102 | 42.2% | 3.24% | 1.0097 |
| F4 | +0.811 | 10.8% | 39 | 53.8% | 1.28% | 1.1182 |
| **F5 — final holdout** | -0.304 | 17.7% | 65 | 52.3% | 1.22% | 0.9070 |

Final-holdout exits: upper_barrier 20, lower_barrier 15, vertical 30, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers ADA && python -m ml_module.labels --tickers ADA && python -m ml_module.hpo --tickers ADA && python -m ml_module.train --tickers ADA && python -m ml_module.strategy --tickers ADA && python -m ml_module.status --tickers ADA

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
