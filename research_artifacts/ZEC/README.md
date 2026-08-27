# ZEC — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `experiment_configuration.json` next to this file records the configuration this run was executed under.

## Files

| file | holds | size |
| --- | --- | --- |
| `canonical_1m.parquet` | the published canonical 1m series | 39,755 KB |
| `features.parquet` | X — 15 causal columns on the decision grid | 9,678 KB |
| `label_events.parquet` | Y — triple-barrier outcome and the event prices | 5,304 KB |
| `oos_predictions.parquet` | out-of-fold class probabilities, full windows | 2,348 KB |
| `hyperparameter_search.json` | the winning point of the search | 325 B |
| `model_evaluation.json` | classification metrics per fold | 3 KB |
| `strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |
| `experiment_configuration.json` | the configuration this run was executed under | 4 KB |
| `README.md` | this file | — |

`features.parquet` carries 16 rows more than `label_events.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `oos_predictions.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised subset of each.

## Labels

194,832 decisions, of which **194,723 supervised** (99.944%) — 0 events resolve ambiguously and 109 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 24,135, neutral 148,163, long 22,425 (194,723 total).

## Model

Search: 50 Optuna trials, best log-loss 0.771027. Winner: depth 2, eta 0.0198, 350 rounds, subsample 0.533, colsample 0.763, min_child_weight 48, lambda 0.1238, alpha 0.0145.

| fold | prior log-loss | model log-loss | rel. skill | MCC | scored |
| --- | --- | --- | --- | --- | --- |
| F2 | 0.812426 | 0.791135 | +2.62% | 0.0082 | 35,038 |
| F3 | 0.790699 | 0.767000 | +3.00% | 0.0258 | 34,953 |
| F4 | 0.792683 | 0.754946 | +4.76% | 0.0276 | 35,124 |
| **F5 — final holdout** | 0.803880 | 0.757794 | +5.73% | 0.0339 | 57,772 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,038 |
| F3 | 66,866 | 8 | 35,040 | 34,953 |
| F4 | 101,823 | 4 | 35,136 | 35,124 |
| F5 | 136,935 | 16 | 57,776 | 57,772 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.0** — **fallback**, no threshold reaches 30 trades in every validation fold. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.121 | 4.0% | 4 | 50.0% | 0.13% | 1.0039 |
| F3 | -3.175 | 38.9% | 84 | 35.7% | 2.36% | 0.6142 |
| F4 | -0.016 | 22.6% | 47 | 51.1% | 1.43% | 0.9748 |
| **F5 — final holdout** | +0.242 | 24.5% | 118 | 48.3% | 2.20% | 1.0493 |

Final-holdout exits: upper_barrier 30, lower_barrier 30, vertical 58, ambiguous 0.

## Reproducing this folder

    python -m ml_module.features --tickers ZEC && python -m ml_module.labels --tickers ZEC && python -m ml_module.hpo --tickers ZEC && python -m ml_module.train --tickers ZEC && python -m ml_module.strategy --tickers ZEC && python -m ml_module.status --tickers ZEC

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `Skills_For_The_Project/ML_README.md`, the field names in `Skills_For_The_Project/glossary.md`.
