# LINK — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `LINK_parameters.json` next to this file is the one parameters file: the a-priori experiment configuration plus the winning point of the Optuna→XGB search, written when the search runs — it is not artifact provenance.

## Files

| file | holds | size |
| --- | --- | --- |
| `LINK_canonical_ohlcv_ss-01-hh-dd-MM.parquet` | the published canonical 1m series | 43,312 KB |
| `LINK_parameters.json` | the one parameters file: a-priori configuration + the Optuna→XGB winner | 4 KB |
| `LINK_features_ss-15-hh-dd-MM.parquet` | X — the five 15m family columns on the decision grid | 7,472 KB |
| `LINK_features_ss-mm-01-dd-MM.parquet` | X — the five 1h family columns on the decision grid | 2,240 KB |
| `LINK_features_ss-mm-04-dd-MM.parquet` | X — the five 4h family columns on the decision grid | 1,241 KB |
| `LINK_label_events_ss-15-hh-dd-MM.parquet` | Y — triple-barrier outcome and the event prices | 5,420 KB |
| `LINK_model_evaluation.json` | classification metrics per fold | 2 KB |
| `LINK_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-fold class probabilities, full windows | 2,359 KB |
| `LINK_README.md` | this file | — |
| `LINK_strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |

Each of the three feature parquets carries 16 rows more than `LINK_label_events_ss-15-hh-dd-MM.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `LINK_oos_predictions_ss-15-hh-dd-MM.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

194,832 decisions, of which **194,831 supervised** (99.999%) — 1 events resolve ambiguously and 0 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 25,127, neutral 146,901, long 22,803 (194,831 total).

## Model

Search: 50 Optuna trials, best log-loss 0.774440. Winner: depth 6, eta 0.0122, 300 rounds, subsample 0.526, colsample 0.923, min_child_weight 26, lambda 1.1355, alpha 0.9519.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.807417 | 0.781177 | +3.25% | 35,023 |
| F3 | 0.817230 | 0.777720 | +4.83% | 35,024 |
| F4 | 0.810247 | 0.764423 | +5.66% | 35,120 |
| **F5 — final holdout** | 0.815351 | 0.772357 | +5.27% | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,825 | 15 | 35,040 | 35,023 |
| F3 | 66,863 | 16 | 35,040 | 35,024 |
| F4 | 101,914 | 5 | 35,136 | 35,120 |
| F5 | 137,039 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.0** — **fallback**, no threshold reaches 30 trades in every validation fold. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | -1.044 | 11.9% | 16 | 37.5% | 0.51% | 0.9214 |
| F3 | -0.122 | 11.9% | 72 | 48.6% | 2.23% | 0.9786 |
| F4 | -1.328 | 30.1% | 105 | 41.0% | 3.22% | 0.7267 |
| **F5 — final holdout** | -0.426 | 24.6% | 183 | 44.3% | 3.57% | 0.8489 |

Final-holdout exits: upper_barrier 48, lower_barrier 46, vertical 89, ambiguous 0.

## Reproducing the ML artifacts in this folder

    python -m module_ml.features --tickers LINK && python -m module_ml.labels --tickers LINK && python -m module_ml.hpo --tickers LINK && python -m module_ml.train --tickers LINK && python -m module_ml.strategy --tickers LINK && python -m module_ml.status --tickers LINK

`LINK_canonical_ohlcv_ss-01-hh-dd-MM.parquet` is not produced by that chain and not read by it: it is the published per-asset representation of the canonical series (`make export`); the ML stages read the same canonical market object from the DuckDB tables.

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `module_skills/methodology_ml.md`, the field names in `module_skills/glossary.md`.
