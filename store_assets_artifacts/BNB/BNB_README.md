# BNB — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `BNB_parameters.json` next to this file is the one parameters file: its `experiment_configuration` section is the a-priori configuration and its `hyperparameter_search_result` section is what the search chose, both written when the search runs — it is not artifact provenance.

## Files

| file | holds | size |
| --- | --- | --- |
| `BNB_README.md` | this file | — |
| `BNB_config.json` | the asset's registration, and the engine overrides it takes | 3 B |
| `BNB_features_ss-15-hh-dd-MM.parquet` | X — the five 15m family columns on the decision grid | 7,657 KB |
| `BNB_features_ss-mm-01-dd-MM.parquet` | X — the five 1h family columns on the decision grid | 2,245 KB |
| `BNB_features_ss-mm-04-dd-MM.parquet` | X — the five 4h family columns on the decision grid | 1,242 KB |
| `BNB_label_events_ss-15-hh-dd-MM.parquet` | Y — triple-barrier outcome and the event prices | 5,343 KB |
| `BNB_model_evaluation.json` | classification metrics per fold | 2 KB |
| `BNB_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-sample class probabilities, full windows | 2,350 KB |
| `BNB_parameters.json` | the one parameters file: the a-priori configuration and the search result | 4 KB |
| `BNB_strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |

Each of the three feature parquets carries 16 rows more than `BNB_label_events_ss-15-hh-dd-MM.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `BNB_oos_predictions_ss-15-hh-dd-MM.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

194,832 decisions, of which **194,823 supervised** (99.995%) — 4 events resolve ambiguously and 5 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 27,204, neutral 144,879, long 22,740 (194,823 total).

## Model

Search: 50 Optuna trials, best log-loss 0.791758. Winner: depth 2, eta 0.0195, 350 rounds, subsample 0.663, colsample 0.694, min_child_weight 3, lambda 0.3489, alpha 0.4544.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.830763 | 0.789590 | +4.96% | 35,019 |
| F3 | 0.847439 | 0.788585 | +6.94% | 35,024 |
| F4 | 0.850676 | 0.797097 | +6.30% | 35,120 |
| **F5 — final holdout** | 0.851809 | 0.802036 | +5.84% | 57,776 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,019 |
| F3 | 66,857 | 14 | 35,040 | 35,024 |
| F4 | 101,905 | 6 | 35,136 | 35,120 |
| F5 | 137,031 | 16 | 57,776 | 57,776 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.31**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.692 | 16.7% | 98 | 53.1% | 2.79% | 1.1141 |
| F3 | -0.956 | 10.0% | 42 | 42.9% | 1.25% | 0.9348 |
| F4 | +0.977 | 9.0% | 40 | 50.0% | 0.95% | 1.0820 |
| **F5 — final holdout** | -0.322 | 13.2% | 41 | 41.5% | 0.79% | 0.9510 |

Final-holdout exits: upper_barrier 12, lower_barrier 10, vertical 19, ambiguous 0.

## Reproducing the ML artifacts in this folder

    python -m module_ml.features --tickers BNB && python -m module_ml.labels --tickers BNB && python -m module_ml.hpo --tickers BNB && python -m module_ml.train --tickers BNB && python -m module_ml.strategy --tickers BNB && python -m module_ml.status --tickers BNB

The OHLCV itself lives only in the DuckDB tables — the market object the whole chain reads; the asset folder carries no price series.

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `module_skills/methodology_ml.md`, the field names in `module_skills/glossary.md`.
