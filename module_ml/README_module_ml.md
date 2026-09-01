# module_ml — the canonical series in, a research result out

The front door of this module: what it is, where its responsibility stops, and
how to run it. The method itself — every equation, every fold, every citation —
is `skills/methodology_ml.md` and is not repeated here. *The repository shows
the destination, not the road*.

`module_ml` reads one asset's canonical 1m series and produces a research
result: hierarchical features, triple-barrier labels, a hyper-parameter search,
purged walk-forward XGBoost predictions and a gated strategy simulation, each
persisted as a file in that asset's own folder.

## Where the responsibility stops

It begins at `ohlcv_1m_canonical` and asks nothing about where a minute came
from. Downloading, venue selection, forward fill and provenance belong to
`module_data`; presentation of the results belongs to `module_monitoring`. The
15m/1h/4h aggregations are the exception in the other direction: they live in
`module_data`'s database file but are written here, by `bars.py`, the one
writer of the ML layer — every other ML stage opens that database read-only.

## Stages

Run in order; `make ml-all` runs the chain. The six stages above `status` fan
out one process per asset with its threads pinned to one; `status` runs once and
aggregates the whole basket.

| stage | local | writes |
|---|---|---|
| bars | `make ml-bars` | `ohlcv_15m_canonical`, `ohlcv_1h_canonical`, `ohlcv_4h_canonical` |
| features | `make ml-features` | three per-timeframe feature parquets |
| labels | `make ml-labels` | the triple-barrier label events parquet |
| hyper-parameter search | `make ml-hpo` | `<TICKER>_parameters.json` |
| training | `make ml-train` | `<TICKER>_model_evaluation.json`, the out-of-sample predictions parquet |
| strategy | `make ml-strategy` | `<TICKER>_strategy_evaluation.json` |
| status | `make ml-status` | `module_monitoring/ml_status.json`, `<TICKER>_README.md` |

Every target has a `docker-` twin: a per-asset stage runs inside each asset's
own container, `status` inside `pipeline`. Each per-asset stage takes
`--tickers`; `status` takes it too, but there it scopes only which
`<TICKER>_README.md` files are rewritten — the snapshot always folds the whole
basket.

## What it writes

```
store_assets_artifacts/<TICKER>/
```

One folder per asset, one file per artifact responsibility; the manifest and
what each file holds are in `../module_skills/glossary.md` § Artifacts.
`<TICKER>_README.md` and `<TICKER>_parameters.json` are tracked so a folder
reads without a run — both are derived and never hand-edited.

## Its normative skills

| document | answers |
|---|---|
| `skills/methodology_ml.md` | the research layer equation by equation, with its citations |

Repository-wide rules are in `../module_skills/`, indexed by
[../module_skills/README.md](../module_skills/README.md); the market object it
reads is defined by
[../module_data/skills/skill_candle_canonicalisation.md](../module_data/skills/skill_candle_canonicalisation.md).
