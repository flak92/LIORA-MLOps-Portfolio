# SOL — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `experiment_configuration.json` next to this file records the a-priori experiment configuration, read from the current `module_ml/config.py` when the report is written — it is not artifact provenance.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 43,691 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,967 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,450 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities, full windows | 2,363 KB |
| `hyperparameter_search.json` | the winning point of the search | 320 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `experiment_configuration.json` | the a-priori experiment configuration, recorded at report time | 3 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

194,832 decisions, of which **194,820 supervised** (99.994%) — 8 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 25,254, neutral 145,753, long 23,813 (194,820 total).

## Model

Search: 50 Optuna trials, best log-loss 0.778915. Winner: depth 3, eta 0.0132, 400 rounds, subsample 0.772, colsample 0.630, min_child_weight 25, lambda 9.4324, alpha 0.1138.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.836293 | 0.792776 | +5.20% | 35,016 |
| F3 | 0.832372 | 0.775238 | +6.86% | 35,024 |
| F4 | 0.804719 | 0.768730 | +4.47% | 35,120 |
| **F5 — final holdout** | 0.834866 | 0.788268 | +5.58% | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,016 |
| F3 | 66,852 | 16 | 35,040 | 35,024 |
| F4 | 101,903 | 5 | 35,136 | 35,120 |
| F5 | 137,033 | 11 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.3**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | -0.925 | 17.6% | 31 | 38.7% | 1.02% | 0.8825 |
| F3 | +1.526 | 15.6% | 43 | 55.8% | 1.16% | 1.2380 |
| F4 | -0.966 | 12.1% | 38 | 36.8% | 1.38% | 0.8995 |
| **F5 — final holdout** | +0.405 | 7.4% | 52 | 53.8% | 0.96% | 1.0535 |

Final-holdout exits: upper_barrier 10, lower_barrier 22, vertical 20, ambiguous 0.

## Reproducing the ML artifacts in this folder

    python -m module_ml.features --tickers SOL && python -m module_ml.labels --tickers SOL && python -m module_ml.hpo --tickers SOL && python -m module_ml.train --tickers SOL && python -m module_ml.strategy --tickers SOL && python -m module_ml.status --tickers SOL

`canonical_1m.parquet` is not produced by that chain and not read by it: it is the published per-asset representation of the canonical series (`make export`); the ML stages read the same canonical market object from the DuckDB tables.

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `module_guidance/methodology_ml.md`, the field names in `module_guidance/glossary.md`.
