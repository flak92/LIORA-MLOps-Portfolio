# ADA — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `ADA_experiment_configuration.json` next to this file records the a-priori experiment configuration, read from the current `module_ml/config.py` when the report is written — it is not artifact provenance.

## Files

| file | holds | size |
| --- | --- | --- |
| `ADA_canonical_ohlcv_ss-01-hh-dd-MM.parquet` | the published canonical 1m series | 37,865 KB |
| `ADA_experiment_configuration.json` | the a-priori experiment configuration, recorded at report time | 3 KB |
| `ADA_features_ss-15-hh-dd-MM.parquet` | X — 15 causal columns on the decision grid | 9,576 KB |
| `ADA_label_events_ss-15-hh-dd-MM.parquet` | Y — triple-barrier outcome and the event prices | 5,284 KB |
| `ADA_model_evaluation.json` | classification metrics per fold | 2 KB |
| `ADA_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-fold class probabilities, full windows | 2,350 KB |
| `ADA_OPTUNAs_XGB_HPOs_best_params.json` | the winning point of the Optuna→XGB search | 318 B |
| `ADA_README.md` | this file | — |
| `ADA_strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |

`ADA_features_ss-15-hh-dd-MM.parquet` carries 16 rows more than `ADA_label_events_ss-15-hh-dd-MM.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `ADA_oos_predictions_ss-15-hh-dd-MM.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

194,832 decisions, of which **194,818 supervised** (99.993%) — 10 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 25,288, neutral 147,677, long 21,853 (194,818 total).

## Model

Search: 50 Optuna trials, best log-loss 0.771437. Winner: depth 2, eta 0.0115, 500 rounds, subsample 0.529, colsample 0.649, min_child_weight 4, lambda 0.9644, alpha 0.9982.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.810046 | 0.771342 | +4.78% | 35,022 |
| F3 | 0.818080 | 0.769232 | +5.97% | 35,024 |
| F4 | 0.817511 | 0.773737 | +5.35% | 35,120 |
| **F5 — final holdout** | 0.816330 | 0.768760 | +5.83% | 57,768 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,022 |
| F3 | 66,867 | 7 | 35,040 | 35,024 |
| F4 | 101,910 | 4 | 35,136 | 35,120 |
| F5 | 137,034 | 16 | 57,776 | 57,768 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.24**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.272 | 13.4% | 88 | 45.5% | 2.88% | 1.0313 |
| F3 | +0.286 | 13.8% | 127 | 42.5% | 3.94% | 1.0362 |
| F4 | +0.219 | 13.5% | 53 | 47.2% | 1.83% | 1.0232 |
| **F5 — final holdout** | -0.305 | 19.6% | 95 | 48.4% | 1.85% | 0.8996 |

Final-holdout exits: upper_barrier 26, lower_barrier 23, vertical 46, ambiguous 0.

## Reproducing the ML artifacts in this folder

    python -m module_ml.features --tickers ADA && python -m module_ml.labels --tickers ADA && python -m module_ml.hpo --tickers ADA && python -m module_ml.train --tickers ADA && python -m module_ml.strategy --tickers ADA && python -m module_ml.status --tickers ADA

`ADA_canonical_ohlcv_ss-01-hh-dd-MM.parquet` is not produced by that chain and not read by it: it is the published per-asset representation of the canonical series (`make export`); the ML stages read the same canonical market object from the DuckDB tables.

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `module_skills/methodology_ml.md`, the field names in `module_skills/glossary.md`.
