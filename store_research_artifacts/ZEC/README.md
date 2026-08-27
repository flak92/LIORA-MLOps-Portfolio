# ZEC — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `experiment_configuration.json` next to this file records the configuration this run was executed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 39,755 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,678 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,304 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities, full windows | 2,339 KB |
| `hyperparameter_search.json` | the winning point of the search | 323 B |
| `model_evaluation.json` | classification metrics per fold | 2 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `experiment_configuration.json` | the configuration this run was executed under | 3 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

194,832 decisions, of which **194,723 supervised** (99.944%) — 0 events resolve ambiguously and 109 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 24,135, neutral 148,163, long 22,425 (194,723 total).

## Model

Search: 50 Optuna trials, best log-loss 0.771464. Winner: depth 3, eta 0.0109, 350 rounds, subsample 0.770, colsample 0.845, min_child_weight 46, lambda 0.1892, alpha 0.1698.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.812190 | 0.791157 | +2.59% | 35,022 |
| F3 | 0.790172 | 0.766952 | +2.94% | 34,937 |
| F4 | 0.792861 | 0.756284 | +4.61% | 35,108 |
| **F5 — final holdout** | 0.803880 | 0.759031 | +5.58% | 57,772 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,022 |
| F3 | 66,866 | 8 | 35,040 | 34,937 |
| F4 | 101,823 | 4 | 35,136 | 35,108 |
| F5 | 136,935 | 16 | 57,776 | 57,772 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.0** — **fallback**, no threshold reaches 30 trades in every validation fold. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.000 | 0.0% | 0 | 0.0% | 0.00% | 1.0000 |
| F3 | -3.199 | 34.2% | 56 | 32.1% | 1.58% | 0.6708 |
| F4 | -0.370 | 18.4% | 35 | 54.3% | 0.98% | 0.9117 |
| **F5 — final holdout** | -0.451 | 31.5% | 73 | 42.5% | 1.43% | 0.8467 |

Final-holdout exits: upper_barrier 16, lower_barrier 18, vertical 39, ambiguous 0.

## Reproducing the ML artifacts in this folder

    python -m module_ml.features --tickers ZEC && python -m module_ml.labels --tickers ZEC && python -m module_ml.hpo --tickers ZEC && python -m module_ml.train --tickers ZEC && python -m module_ml.strategy --tickers ZEC && python -m module_ml.status --tickers ZEC

`canonical_1m.parquet` is not produced by that chain: it is published by the data layer (`make export`) and read as the market object.

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `module_skills_for_the_project/ML_README.md`, the field names in `module_skills_for_the_project/glossary.md`.
