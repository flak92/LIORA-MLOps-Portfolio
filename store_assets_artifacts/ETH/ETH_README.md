# ETH — research artifacts

Research window 2021-01-01 → 2026-08-26, seed 42. One directory per ticker, one file per distinct artifact responsibility; `ETH_parameters.json` next to this file is the one parameters file: its `experiment_configuration` section is the a-priori configuration and its `hyperparameter_search_result` section is what the search chose, both written when the search runs — it is not artifact provenance.

## Files

| file | holds | size |
| --- | --- | --- |
| `ETH_README.md` | this file | — |
| `ETH_features_ss-15-hh-dd-MM.parquet` | X — the five 15m family columns on the decision grid | 7,761 KB |
| `ETH_features_ss-mm-01-dd-MM.parquet` | X — the five 1h family columns on the decision grid | 2,245 KB |
| `ETH_features_ss-mm-04-dd-MM.parquet` | X — the five 4h family columns on the decision grid | 1,242 KB |
| `ETH_label_events_ss-15-hh-dd-MM.parquet` | Y — triple-barrier outcome and the event prices | 5,471 KB |
| `ETH_model_evaluation.json` | classification metrics per fold | 2 KB |
| `ETH_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-sample class probabilities, full windows | 2,382 KB |
| `ETH_parameters.json` | the one parameters file: the a-priori configuration and the search result | 4 KB |
| `ETH_strategy_evaluation.json` | threshold, PnL and the equity curve | 21 KB |

Each of the three feature parquets carries 16 rows more than `ETH_label_events_ss-15-hh-dd-MM.parquet`: the tail decisions whose full 240-minute horizon does not fit inside the research window have features but no label. `ETH_oos_predictions_ss-15-hh-dd-MM.parquet` holds the four out-of-sample prediction windows end to end; the metrics score only the supervised, horizon-fitting subset of each.

## Labels

194,832 decisions, of which **194,815 supervised** (99.991%) — 13 events resolve ambiguously and 4 entry minutes printed no trade, so neither trains anything. Classes over the supervised population: short 27,680, neutral 143,281, long 23,854 (194,815 total).

## Model

Search: 50 Optuna trials, best log-loss 0.814319. Winner: depth 6, eta 0.0112, 600 rounds, subsample 0.505, colsample 0.887, min_child_weight 23, lambda 1.2725, alpha 0.9971.

| fold | prior log-loss | model log-loss | rel. skill | scored |
| --- | --- | --- | --- | --- |
| F2 | 0.860953 | 0.823478 | +4.35% | 35,017 |
| F3 | 0.900062 | 0.826745 | +8.15% | 35,024 |
| F4 | 0.850444 | 0.792734 | +6.79% | 35,120 |
| **F5 — final holdout** | 0.862701 | 0.797269 | +7.58% | 57,770 |

## Fold geometry

| fold | trained on | purged | window | scored |
| --- | --- | --- | --- | --- |
| F2 | 31,820 | 16 | 35,040 | 35,017 |
| F3 | 66,862 | 7 | 35,040 | 35,024 |
| F4 | 101,901 | 8 | 35,136 | 35,120 |
| F5 | 137,029 | 16 | 57,776 | 57,770 |

`purged` counts the training events that had not finished before the fold opened; they are dropped, never truncated. Average-uniqueness weights are measured on each of these populations separately, after the purge.

## Strategy

Entry edge threshold **0.26**. Cost 0.06% per side; the hierarchy gate requires the side to match the 4h trend sign with at least 2 of 3 timeframes agreeing.

| fold | Sharpe | maxDD | trades | hit rate | exposure | final equity |
| --- | --- | --- | --- | --- | --- | --- |
| F2 | +0.422 | 15.8% | 140 | 48.6% | 4.32% | 1.0651 |
| F3 | -2.376 | 28.0% | 151 | 41.7% | 4.84% | 0.7670 |
| F4 | +0.367 | 12.3% | 100 | 46.0% | 3.24% | 1.0381 |
| **F5 — final holdout** | -0.179 | 21.0% | 170 | 45.9% | 3.29% | 0.9421 |

Final-holdout exits: upper_barrier 43, lower_barrier 43, vertical 84, ambiguous 0.

## Reproducing the ML artifacts in this folder

    python -m module_ml.features --tickers ETH && python -m module_ml.labels --tickers ETH && python -m module_ml.hpo --tickers ETH && python -m module_ml.train --tickers ETH && python -m module_ml.strategy --tickers ETH && python -m module_ml.status --tickers ETH

The OHLCV itself lives only in the DuckDB tables — the market object the whole chain reads; the asset folder carries no price series.

F5 never participates in feature definition, hyper-parameter selection, entry-edge-threshold selection or strategy-rule selection — folds F2, F3, F4 carry the data-driven selection of the hyper-parameters and the entry edge threshold. The method is in `module_skills/methodology_ml.md`, the field names in `module_skills/glossary.md`.
