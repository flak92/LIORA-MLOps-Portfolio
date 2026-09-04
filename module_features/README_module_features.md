# module_features — the canonical series in, the feature catalogue out

The front door of this module: what it is, where its responsibility stops, and
how to run it. The names are `skills/skill_feature_taxonomy.md`, the definitions
`skills/methodology_features.md`, and neither is repeated here. *The repository
shows the destination, not the road*.

`module_features` reads one asset's canonical 1m series and produces the feature
catalogue: exact bars on every timeframe of the register, written into the
asset's own database, and every catalogued feature definition evaluated on
every timeframe it is offered on, aligned to the decision grid — one parquet per
timeframe in the asset's folder.

## Where the responsibility stops

It begins at `ohlcv_1m_canonical` and asks nothing about where a minute came
from; it ends at one parquet per timeframe. Which columns an asset's model sees,
the labels, the search, the model and the strategy belong to `module_ml`;
presentation belongs to `module_monitoring`. The aggregations are the exception
in the other direction: they live in `module_data`'s database file but are
written here, by `bars.py`, the one writer of the feature layer — every stage
downstream opens that database read-only. That line is the storage →
feature-compute boundary, and `bars.py` its one write across it. The direction:
[../module_skills/skill_pre_aws_solution.md](../module_skills/skill_pre_aws_solution.md).

This module publishes no snapshot: it measures no run state. Its structural
facts — the register, the catalogue with histories and warm-ups, the nesting —
ride in `module_monitoring/ml_status.json`, written by `module_ml/status.py`
from the same `config.py`.

## Stages

Run in order; `make features-all` runs the chain. Both stages fan out one process
per asset with its threads pinned to one.

| stage | local | writes |
|---|---|---|
| bars | `make features-bars` | `ohlcv_<timeframe>_canonical`, one table per entry of the register |
| catalogue | `make features-catalogue` | one feature parquet per timeframe |

Every target has a `docker-` twin: a per-asset stage runs inside each asset's own
container. Each stage takes `--tickers`.

## What it writes

```
store_assets_artifacts/<TICKER>/<TICKER>_research_ohlcv.duckdb     the aggregation tables, beside the canonical series
store_assets_artifacts/<TICKER>/<TICKER>_features_<slot>.parquet   decision_ts and the catalogue's columns on that timeframe
```

The manifest and what each file holds are in `../module_skills/glossary.md`
§ Artifacts.

## Design rationale

Why each object of this module sits where it does — the answers of
`../module_skills/skill_self_explaining_naming.md` § The naming review written
down, one row per object, analogous pair or the module's documents; the mapping
row it answers to is `../module_skills/skill_pre_aws_solution.md` § The mapping
table, cited by its *responsibility* column and never repeated.

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The one definition every timeframe-shaped and feature-shaped thing derives from — the register, the frozen research window and its warm-up, the indicator register, the catalogue and its descriptors — and the one descriptor of a feature parquet, re-exporting `TICKERS`, `artifact_dir()` and `research_ohlcv_duckdb()` from `../module_data/config.py`. | Both stages import it, `../module_ml/config.py` re-exports it onward, and nothing else names a feature parquet or a feature. | A stage reaches a parquet by descriptor (`../module_skills/skill_pre_aws_solution.md` § Correlatable artifacts, without a version scheme), so the asset folder keeps the same path under `/app` on whatever disk is mounted there. | STORAGE — research artifacts |
| `bars.py` | The one writer of the feature layer: the aggregations of the canonical 1m series on every timeframe of the register, written into the asset's own database file (§ Where the responsibility stops). | It imports `config.py` alone, reads the `ohlcv_1m_canonical` that `../module_data/ingest.py` wrote, and every later stage reads the tables it writes. | The one write across the storage → feature-compute line — `../module_skills/skill_pre_aws_solution.md` § What stays as it is, and why, the `bars.py` row — into the same file under the same whole-file lock whatever disk holds it. | STORAGE — the canonical market object, one writer at a time |
| `indicators.py` | Pure numpy kernels — the recursive indicators and the rolling statistics, one kernel per token of the register (its docstring) — a library, not a stage. | `catalogue.py` and `../module_ml/labels.py` import it, and it imports nothing of the module. | It reads no file and writes none, so nothing in it names a path — the same kernels run in whichever container imports them. | COMPUTE — one stage for one asset |
| `catalogue.py` | FEATURE — the catalogue on the decision grid: every definition of `config.py` evaluated by folding its terms through the operators, every value from the last closed bar of its timeframe (its docstring; `skills/methodology_features.md`). | It imports `config.py`, `dataset.py` and `indicators.py`, reads the tables `bars.py` wrote and writes the parquets `../module_ml/dataset.py` reads. | It runs one asset at a time in `asset-<ticker>` with `--tickers <TICKER>` (§ Stages) and writes at `features_parquet()` — the same override and the same paths whatever host runs the container. | COMPUTE — one stage for one asset |
| `dataset.py` | The one parquet writer of the pipeline, `write_parquet()` (its docstring): every layer that writes a parquet writes it here, upstream of them all. | `catalogue.py` imports it, `../module_ml/dataset.py` re-exports it for the label and prediction writers, and it imports `config.py` alone. | It writes to the descriptor it is handed and builds no path of its own, so an artifact lands where a `config.py` says on whatever disk is mounted at `/app`. | STORAGE — research artifacts |
| `__init__.py` | The package that makes `python -m module_features.<stage>` a command (§ Stages), its docstring the module's responsibility in one line. | It names the register, the bars, the kernels and the catalogue, and imports nothing. | The same `python -m module_features.<stage> --tickers <TICKER>` runs in the venv and in `asset-<ticker>` (§ Stages), the command `docker compose exec` carries unchanged. | COMPUTE — one stage, one one-off process |
| the module's documents — `README_module_features.md` and `skills/` | This orientation and the normative documents of `skills/`, filed by ownership (`../AGENTS.md` § The default choice). | The orientation points at the documents beside it (§ Its normative skills), and every rule about this module sits in `skills/` (`../AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_features/` that no process reads, travelling with the code beside them — the same paths beside the code wherever the code is. | no row — a document that travels with the task's code, seated beside its module |

## Its normative skills

| document | answers |
|---|---|
| `skills/skill_feature_taxonomy.md` | the timeframe register, the terms, the composition grammar, the scope nesting and the warm-up |
| `skills/methodology_features.md` | every catalogued definition, equation by equation, with its histories and citations |

Repository-wide rules are in `../module_skills/`, indexed by
[../module_skills/README.md](../module_skills/README.md); the market object it
reads is defined by
[../module_data/skills/skill_candle_canonicalisation.md](../module_data/skills/skill_candle_canonicalisation.md);
what the research layer does with the catalogue is
[../module_ml/README_module_ml.md](../module_ml/README_module_ml.md).
