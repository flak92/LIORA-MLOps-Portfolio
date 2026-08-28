# XRP — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `XRP_parameters.json` next to this file is the one parameters file: the a-priori experiment configuration plus the winning point of the Optuna→XGB search, written when the search runs — it is not artifact provenance.

## Files

| file | holds | size |
| --- | --- | --- |
| `XRP_canonical_ohlcv_ss-01-hh-dd-MM.parquet` | the published canonical 1m series | 39,915 KB |
| `XRP_parameters.json` | the one parameters file: a-priori configuration + the Optuna→XGB winner | 4 KB |
| `XRP_features_ss-15-hh-dd-MM.parquet` | X — the five 15m family columns on the decision grid | 7,286 KB |
| `XRP_features_ss-mm-01-dd-MM.parquet` | X — the five 1h family columns on the decision grid | 2,228 KB |
| `XRP_features_ss-mm-04-dd-MM.parquet` | X — the five 4h family columns on the decision grid | 1,238 KB |
| `XRP_label_events_ss-15-hh-dd-MM.parquet` | Y — triple-barrier outcome and the event prices | 5,278 KB |
| `XRP_model_evaluation.json` | classification metrics per fold | 2 KB |
| `XRP_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-fold class probabilities, full windows | 2,366 KB |
| `XRP_README.md` | this file | — |
| `XRP_strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |

Each of the three feature parquets carries 16 rows more than `XRP_label_events_ss-15-hh-dd-MM.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `XRP_oos_predictions_ss-15-hh-dd-MM.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

194,832 decisions, of which **194,828 supervised** (99.998%) — 0 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 26,240, neutral 146,600, long 21,988 (194,828 total).

## Model

Search: 50 Optuna trials, best log-loss 0.774423. Winner: depth 5, eta 0.0147, 300 rounds, subsample 0.602, colsample 0.948, min_child_weight 45, lambda 2.4097, alpha 0.0518.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.810194 | 0.777801 | +4.00% | 35,024 |
| F3 | 0.828916 | 0.762078 | +8.06% | 35,024 |
| F4 | 0.853204 | 0.783390 | +8.18% | 35,120 |
| **F5 — final holdout** | 0.840764 | 0.774922 | +7.83% | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,825 | 11 | 35,040 | 35,024 |
| F3 | 66,869 | 7 | 35,040 | 35,024 |
| F4 | 101,912 | 4 | 35,136 | 35,120 |
| F5 | 137,036 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.21**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | -0.621 | 31.6% | 221 | 43.4% | 7.53% | 0.8342 |
| F3 | -1.090 | 29.7% | 228 | 41.7% | 6.37% | 0.7689 |
| F4 | +0.890 | 25.3% | 178 | 43.3% | 5.27% | 1.2476 |
| **F5 — final holdout** | +0.139 | 31.9% | 273 | 47.3% | 5.12% | 1.0017 |

Final-holdout exits: upper_barrier 78, lower_barrier 73, vertical 122, ambiguous 0.

## Reproducing the ML artifacts in this folder

    python -m module_ml.features --tickers XRP && python -m module_ml.labels --tickers XRP && python -m module_ml.hpo --tickers XRP && python -m module_ml.train --tickers XRP && python -m module_ml.strategy --tickers XRP && python -m module_ml.status --tickers XRP

`XRP_canonical_ohlcv_ss-01-hh-dd-MM.parquet` is not produced by that chain and not read by it: it is the published per-asset representation of the canonical series (`make export`); the ML stages read the same canonical market object from the DuckDB tables.

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `module_skills/methodology_ml.md`, the field names in `module_skills/glossary.md`.
