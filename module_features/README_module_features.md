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
from; it ends at one parquet per timeframe, the contract beside them and one
snapshot. Which columns an asset's model sees,
the labels, the search, the model and the strategy belong to `module_ml`;
presentation belongs to `module_monitoring`. The aggregations are the exception
in the other direction: they live in `module_data`'s database file but are
written here, by `bars.py`, the one writer of the feature layer — every stage
downstream opens that database read-only. That line is the storage →
feature-compute boundary, and `bars.py` its one write across it. The direction:
[../module_skills/skill_pre_aws_solution.md](../module_skills/skill_pre_aws_solution.md).

Beyond its parquets this module publishes two things. Per asset,
`<TICKER>_catalogue.json` — the contract the ML layer reads instead of importing
this module: the decision grid, the hierarchy with each timeframe's slot and
duration, the warm-up, the columns per timeframe in catalogue order, the default
set and the parquet each timeframe's columns live in. And one snapshot,
`store_status/features_status.json`, written by `status.py`: the register, the
catalogue with histories and warm-ups, the nesting — the facts of `config.py` —
and each asset's row counts, the one run-state fact this module has.

## Stages

Run in order; `make features-all` runs the chain. The two per-asset stages fan out
one process per asset with its threads pinned to one; `status` runs once over the
assets the launcher names.

| stage | local | writes |
|---|---|---|
| bars | `make features-bars` | `ohlcv_<timeframe>_canonical`, one table per entry of the register |
| catalogue | `make features-catalogue` | one feature parquet per timeframe, and `<TICKER>_catalogue.json` — the contract the ML layer reads |
| status | `make features-status` | `store_status/features_status.json` |

Every target has a `docker-` twin: a per-asset stage runs inside each asset's own
container, `status` inside `pipeline`. Each stage takes `--tickers`.

## What it writes

```
store_assets_artifacts/<TICKER>/<TICKER>_research_ohlcv.duckdb     the aggregation tables, beside the canonical series
store_assets_artifacts/<TICKER>/<TICKER>_features_<slot>.parquet   decision_ts and the catalogue's columns on that timeframe
store_assets_artifacts/<TICKER>/<TICKER>_catalogue.json            the contract: grid, hierarchy, warm-up, columns, default set, parquet names
store_status/features_status.json                                  the snapshot: the catalogue as the register presents it, each asset's row counts
```

The manifest and what each file holds are in `../module_skills/glossary.md`
§ Artifacts.

## Extending

Every element of the taxonomy is one record in one register, and its name, its
computation, its history and its warm-up are read off that record — so adding
one is a local edit, and what it costs is known before it is made. The rules
the names follow are `skills/skill_feature_taxonomy.md`; this is what each
addition touches.

| what you add | where, and how much | what it changes | the gate |
|---|---|---|---|
| a timeframe | one token in `HIERARCHY_TIMEFRAMES` (`config.py`) | a different experiment: the bars, every parquet, the contract and the snapshot, the labels, X and every artifact, the final holdout included | nothing stays byte-identical; the whole chain reruns |
| an indicator | its kernel and one record in `INDICATORS` (`indicators.py`) | nothing, until a catalogue record names it | the existing parquets byte-identical |
| a derived series | one entry in `SERIES_KERNELS` (`catalogue.py`) | nothing, until a term names it | the existing parquets byte-identical |
| an operator or a normaliser | one record in `OPERATORS` or `NORMALISERS`, beside its kernel (`catalogue.py`) | nothing, until a catalogue record names it | the existing parquets byte-identical |
| a feature definition | one record in `FEATURE_CATALOGUE` (`config.py`): its terms, the timeframes it is offered on, and `definition_in_default_set: False` | every parquet it is offered on gains a column, `<TICKER>_catalogue.json` a column name, the catalogue frame a row, and the feature-set search's `inputs` change | the existing columns byte-identical; `ml-labels` … `ml-strategy` untouched and `features-status` republishing the catalogue; the next search starts from trial 1, and a model sees the column only after a promotion |
| a second parameter for an indicator | the record and the name grammar, in one commit (`skills/skill_feature_taxonomy.md` § Series and indicators) | the derived names of existing terms do not change | the existing parquets byte-identical |

`definition_in_default_set: True` is a different move: it puts the column into
every asset's X, so the ML chain reruns and today's numbers move. The default
set is the frozen experiment's; a set chosen for one asset is the feature-set
search's and a hand's promotion
(`../module_ml/skills/methodology_ml.md` § 4). A new asset is not an extension
of this module at all: it is a ticker in the Makefile's `TICKERS` and a block
under the compose anchor (`../README.md` § The basket), and both stages follow
it without an edit.

## Design rationale

Why each object of this module sits where it does — the answers of
`../module_skills/skill_self_explaining_naming.md` § The naming review written
down, one row per object, analogous pair or the module's documents; the mapping
row it answers to is `../module_skills/skill_pre_aws_solution.md` § The mapping
table, cited by its *responsibility* column and never repeated.

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The one definition every timeframe-shaped and feature-shaped thing derives from — the hierarchy, the frozen research window and its warm-up, the catalogue and its descriptors — the descriptor of a feature parquet, the contract `catalogue_contract()` with its descriptor `catalogue_json()`, and the snapshot's path, re-exporting `artifact_dir()` and `research_ohlcv_duckdb()` from `../module_data/config.py` and the indicator register from `indicators.py`. | All three stages import it; `../module_ml` imports nothing from it and reads the contract file instead; `../module_monitoring/record.py` reaches the parquets through `features_parquet()` for its stage → artifact map, and nothing else names a feature parquet or a feature. | A stage reaches a parquet by descriptor (`../module_skills/skill_pre_aws_solution.md` § Correlatable artifacts, without a version scheme), so the asset folder keeps the same path under `/app` on whatever disk is mounted there. | STORAGE — research artifacts |
| `bars.py` | The one writer of the feature layer: the aggregations of the canonical 1m series on every timeframe of the register, written into the asset's own database file (§ Where the responsibility stops). | It imports `config.py` alone, reads the `ohlcv_1m_canonical` that `../module_data/ingest.py` wrote, and every later stage reads the tables it writes. | The one write across the storage → feature-compute line — `../module_skills/skill_pre_aws_solution.md` § What stays as it is, and why, the `bars.py` row — into the same file under the same whole-file lock whatever disk holds it. | STORAGE — the canonical market object, one writer at a time |
| `indicators.py` | Pure numpy kernels — the recursive indicators and the rolling statistics — and the indicator register beside them, one record per token naming the kernel's invariants once (its docstring); a library, not a stage. | `config.py` imports the register and re-exports it, `catalogue.py` and `../module_ml/labels.py` import the kernels, and it imports nothing of the module. | It reads no file and writes none, so nothing in it names a path — the same kernels run in whichever container imports them. | COMPUTE — one stage for one asset |
| `catalogue.py` | FEATURE — the catalogue on the decision grid: every definition of `config.py` evaluated by folding its terms through the operators, every value from the last closed bar of its timeframe (its docstring; `skills/methodology_features.md`). | It imports `config.py`, `dataset.py` and `indicators.py`, reads the tables `bars.py` wrote and writes the parquets and the contract `<TICKER>_catalogue.json` that `../module_ml/dataset.py` reads. | It runs one asset at a time in `asset-<ticker>` with `--tickers <TICKER>` (§ Stages) and writes at `features_parquet()` — the same override and the same paths whatever host runs the container. | COMPUTE — one stage for one asset |
| `dataset.py` | The one parquet writer of the pipeline, `write_parquet()` (its docstring): every layer that writes a parquet writes it here, upstream of them all — and the canonical JSON writer of this module, `write_json()`, twice by extraction (the other in `../module_ml/dataset.py`). | `catalogue.py` and `status.py` import it, `../module_ml/dataset.py` re-exports the parquet writer for the label and prediction writers, and it imports `config.py` alone. | It writes to the descriptor it is handed and builds no path of its own, so an artifact lands where a `config.py` says on whatever disk is mounted at `/app`. | STORAGE — research artifacts |
| `status.py` | The stage that measures this module's own facts — the catalogue as the register presents it and each asset's row counts — published as `store_status/features_status.json` (its docstring). | It imports `config.py` and `dataset.py`, reads the parquets `catalogue.py` wrote, and writes the snapshot `ml.js` fetches for the catalogue frame. | It takes `--tickers` like every stage and runs once in `pipeline`, writing at `FEATURES_STATUS_JSON_PATH` under the `STORE_STATUS_DIR` the launcher names. | COMPUTE — one stage, one one-off process |
| `__init__.py` | The package that makes `python -m module_features.<stage>` a command (§ Stages), its docstring the module's responsibility in one line. | It names the register, the bars, the kernels, the catalogue, the contract and the snapshot, and imports nothing. | The same `python -m module_features.<stage> --tickers <TICKER>` runs in the venv under `make` and in `asset-<ticker>` (§ Stages) — each launcher setting the four `STORE_*_DIR` — the command `docker compose exec` carries unchanged. | COMPUTE — one stage, one one-off process |
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
