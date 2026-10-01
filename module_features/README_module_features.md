# module_features — the canonical series in, the feature catalogue out

The orientation of this module: what it is, where its responsibility stops and how to run it. Its rules are
`skills/skill_feature_taxonomy.md` and, for the serpentine search, `sub_module_serpentine_search/skill_serpentine_search.md`;
the definitions, the feature id and the serpentine search's mathematics are `skills/methodology_features.md`.

`module_features` reads one asset's partition of the canonical 1m family and produces the feature catalogue: exact
bars on every timeframe of the register — the asset's partitions of the `bars` family — and every catalogued feature
definition evaluated on every timeframe it is offered on, aligned to the decision grid — the asset's partitions of the
`catalogue` family, one per timeframe — each family with its `schema.json` beside its partitions. Outside the chain it
holds the serpentine search: a hand's research over one asset's feature set, barrier geometry and hyper-parameter
point, each search state it reaches scored by `module_ml` across a file boundary, and a hand's promotion of the one search state it
proposes (§ Its sub-modules).

## Where the responsibility stops

It begins at the asset's partition of `ohlcv_1m_canonical`, read as a file, and asks nothing about where a minute came
from; it ends at the two families, the contract beside them and one snapshot. The labels, the hyper-parameter search,
the model and the strategy belong to `module_ml`; presentation belongs to `module_monitoring`. The columns a model
sees are the asset's feature set — the default set until a hand promotes a proposal of the serpentine search — and
what a search state is worth is `module_ml`'s to compute: the search asks in one file and reads the answer in
another. The bars are this module's own family, read by the catalogue and by `module_ml`'s labels through a registered
copy of their descriptor.

Beyond its partitions this module publishes, per asset, `<TICKER>_catalogue.json`, the contract the ML layer reads
instead of importing this module (`FEATURE-TAXONOMY-THE-CONTRACT-IS-ONE-FILE`), and one snapshot,
`store/status/features_status.json`: the catalogue as the register presents it, the CONFIGURABLES records of this
module and of the serpentine search, and per asset the row counts of its catalogue partitions and its serpentine search
as it last wrote itself.

## Stages

Run in order; `features-all` is the Makefile's chain, each stage in a one-off container of the `features` runner, and a
single stage is its own `features-<stage>` target, `ASSET=<TICKER>` narrowing a per-asset stage to that asset — or
`python -m module_features.<stage> --tickers <TICKER>` by hand in a shell that exports `STORE_ASSETS_ARTIFACTS_DIR` and
`STORE_STATUS_DIR`. The per-asset stages fan out one process per asset, `JOBS` of them side by side; the promotion runs
for the one asset `ASSET` names, and `status` once over the whole basket.

| stage | target | writes |
|---|---|---|
| bars | `make features-bars` | `bars/ticker=<TICKER>/timeframe=<timeframe>/bars.parquet`, one partition per entry of the register, and `bars/schema.json` |
| catalogue | `make features-catalogue` | `catalogue/ticker=<TICKER>/timeframe=<timeframe>/catalogue.parquet`, one partition per timeframe, `catalogue/schema.json` from the register, and `<TICKER>_catalogue.json` — the contract the ML layer reads |
| status | `make features-status` | `store/status/features_status.json` |

Outside the chain, a hand's actions on the serpentine search:

| action | target | writes |
|---|---|---|
| a turn | `make features-serpentine-turn` | `<TICKER>_serpentine_search.json`, its ledger `<TICKER>_serpentine_search_state_evaluations.jsonl` and the next question `<TICKER>_score_request.json`, or an ended search |
| the promotion | `make features-serpentine-search-promote ASSET=<TICKER>` | `<TICKER>_feature_set.json`, `<TICKER>_barriers.json` and `<TICKER>_hyperparameter_point.json`, then the asset's ML chain |

## What it writes

```
store/assets_artifacts/bars/ticker=<TICKER>/timeframe=<timeframe>/bars.parquet            one timeframe's bars: timestamp_ms, OHLCV, ffill_bars, zero_volume_bars
store/assets_artifacts/bars/schema.json                                                   the family's columns, read off a written partition
store/assets_artifacts/catalogue/ticker=<TICKER>/timeframe=<timeframe>/catalogue.parquet  decision_ts and the definitions offered on that timeframe
store/assets_artifacts/catalogue/schema.json                                              the family's columns, from the register
store/assets_artifacts/ticker=<TICKER>/<TICKER>_catalogue.json                            the contract: grid, hierarchy, warm-up, columns, default set, partition paths
store/status/features_status.json                                                         the snapshot
```

The serpentine search's own files lie in the asset's folder, named in
`sub_module_serpentine_search/README_sub_module_serpentine_search.md`; what each file holds is the register's
§ Artifacts.

## Extending

Every element of the taxonomy is one record in one register (`FEATURE-TAXONOMY-A-REGISTER-IS-RECORDS-BESIDE-THEIR-KERNELS`),
and its name, its computation, its history and its warm-up are read off that record — so adding one is a local edit,
and what it costs is known before it is made.

| what you add | where, and how much | what it changes | the gate |
|---|---|---|---|
| a timeframe | one token in `HIERARCHY_TIMEFRAMES` (`config.py`, a CONFIGURABLES record) under `FEATURE-TAXONOMY-A-TIMEFRAME-TOKEN-DIVIDES-THE-DAY`; a token finer than `DECISION_TIMEFRAME` is read on the decision grid alone, and `LABEL_BARRIER_TRUE_RANGE_TIMEFRAME` of `module_ml/config.py` stays an entry of the hierarchy | a different experiment: both families, the contract and the snapshot, the labels, X and every artifact, the final holdout included; a token above the top also moves the trend gate's timeframe and `WARMUP_END_MS`, and leaves `MINIMUM_AGREEING_TREND_TIMEFRAMES` of `module_ml/config.py` at its value over a larger hierarchy — decide it in the same commit | nothing stays byte-identical; the whole chain reruns; a drafted profile and a promoted `<TICKER>_feature_set.json` are drafted again, and a recorded serpentine search is reset and run again (`SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT`) |
| an indicator | its kernel and one record in `INDICATORS` (`indicators.py`): its `parameter_word`, its `warmup_multiple`, its `warmup_offset_bars` for a window over changes, its fixed `inputs` and bounded `output_range` where it has them, and its `historical_aliases` | nothing, until a catalogue record names it | the existing partitions byte-identical |
| a derived series | one entry in `SERIES_KERNELS` (`indicators.py`) | nothing, until a term names it | the existing partitions byte-identical |
| an operator or a normaliser | one record in `OPERATORS` or `NORMALISERS`, beside its kernel (`catalogue.py`) | nothing, until a catalogue record names it | the existing partitions byte-identical |
| a feature definition | one record appended to `FEATURE_CATALOGUE` (`config.py`), never inserted (`FEATURE-TAXONOMY-A-DEFINITION-IS-APPENDED`), carrying every field (`FEATURE-TAXONOMY-A-CATALOGUE-RECORD-CARRIES-EVERY-FIELD`) and `definition_in_default_set: False`; then its equation in the catalogue table of `skills/methodology_features.md` § The catalogue | every `catalogue` partition of a timeframe it is offered on gains a column, `catalogue/schema.json` a column, `<TICKER>_catalogue.json` a column name, the catalogue frame a row, and the serpentine search's `inputs` change; a definition whose warm-up exceeds `WARMUP_TOP_TIMEFRAME_BARS` raises it, and the first decision of every asset moves with it | while the warm-up stands, the existing columns byte-identical and `ml-labels` … `ml-strategy` untouched; a recorded search is reset and run again (`SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT`), and a model sees the column only after a promotion; `catalogue.nesting` in `features_status.json` shows whether each timeframe's longest effective history stays below the shortest of the timeframe above (`FEATURE-TAXONOMY-EFFECTIVE-HISTORIES-ARE-SHOWN-NOT-ASSERTED`) |
| a second parameter for an indicator | the record and the name grammar, in one commit (`FEATURE-TAXONOMY-A-TERM-IS-ITS-TOKEN-AND-ONE-PARAMETER`) | the derived names of existing terms do not change | the existing partitions byte-identical |

`definition_in_default_set: True` is a different move: it puts the column into every asset's X where no feature set is
promoted, so the ML chain reruns, its numbers move and a recorded serpentine search is reset and run again. A new asset
is not an extension of this module: it is one more token in `TICKERS` of the Makefile (`README.md` § The basket), and a
serpentine search of it needs a profile a hand drafts first.

## Design rationale

Why each object of this module sits where it does, one row per object or analogous pair; the last column is the
responsibility of the mapping table in `module_skills/README.md` § The Pre-AWS mapping it answers to
(`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The module's CONFIGURABLES records and the one definition every timeframe-shaped and feature-shaped thing derives from: the hierarchy, the research window and its warm-up, the catalogue and its descriptors, the two families, the contract `catalogue_contract()` and the snapshot's path. | Every stage and the serpentine search import it; no other module does — `module_ml` reads the contract file instead. | A stage reaches a partition by descriptor (`PRE-AWS-SOLUTION-A-PATH-IS-BUILT-BY-ONE-DESCRIPTOR`). | STORAGE — research artifacts |
| `bars.py` | The writer of the `bars` family: the aggregations of the canonical 1m series inside the research window on every timeframe of the register. | It reads the canonical partition `module_data/ingest.py` wrote; `catalogue.py` and `module_ml`'s labels read what it writes. | One asset at a time, at `bars_parquet()`. | COMPUTE — one stage for one asset |
| `indicators.py` | Pure numpy kernels and the two registers beside them, `SERIES_KERNELS` and `INDICATORS`, one record per token; a library, not a stage. | `config.py` re-exports the indicator register and `catalogue.py` imports the kernels. | It reads no file and writes none. | COMPUTE — one stage for one asset |
| `catalogue.py` | FEATURE — every definition of `config.py` evaluated on the decision grid, every value from the last closed bar of its timeframe. | It reads the `bars` partitions and writes the `catalogue` partitions, its `schema.json` and the contract `module_ml/dataset.py` reads. | One asset at a time, at `catalogue_parquet()`. | COMPUTE — one stage for one asset |
| `dataset.py` | The layer's parquet writer, the schema read off a written partition, the canonical JSON writer and the readers and the ledger's append the serpentine search uses. | `bars.py`, `catalogue.py`, `status.py` and the serpentine search import it. | It writes to the descriptor it is handed and builds no path of its own. | STORAGE — research artifacts |
| `status.py` | The stage that measures this module's own facts — the catalogue as the register presents it, the CONFIGURABLES records, each asset's row counts and serpentine search. | It reads the catalogue partitions, the contract and the search's files, and writes the snapshot the page fetches. | Once for the whole basket, at `FEATURES_STATUS_JSON_PATH`. | COMPUTE — one stage, one one-off process |
| `__init__.py` | The package that makes `python -m module_features.<stage>` a command, its docstring the module's responsibility in one line. | It imports nothing. | The same command runs in a one-off container of the `features` runner. | COMPUTE — one stage, one one-off process |
| the module's documents — `README_module_features.md` and `skills/` | This orientation, the rendered Skill and the methodology, filed by ownership (`AGENTS.md` § The default choice); the serpentine search's rules and orientation lie beside its code. | Every rule about this module sits in `skills/` (`AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_features/` that no stage and no route reads. | no row — a document that travels with the module's code, beside it |
| `sub_module_terminal/` | The module's own terminal, the hand's instrument over this layer and over the serpentine search's own actions. | It imports the standard library and its own package alone — this module's `config.py` imports numpy — so it carries registered copies of what it reads. | It runs on the host's `python3` with gum and starts every stage through `make` (`TUI-DESIGNER-ONE-TERMINAL-PER-MODULE`). | no row — a hand's instrument, beside the stages it starts |
| `sub_module_serpentine_search/` | The serpentine search, a hand's research outside the chain: `serpentine_search.py` one turn, `axis_barrier.py` and `axis_feature_set.py` the moves of two search axes, `promote.py` the promotion, `config.py` its records, its round and its paths. | It imports this module's `config.py` and `dataset.py` and nothing of another module; `status.py` imports it to publish each asset's search. | What a search state is worth crosses to `module_ml` as two files, the question and the answer, never as an import (`SERPENTINE-SEARCH-THE-EVALUATOR-IS-A-FILE-AWAY`). | COMPUTE — one stage for one asset |

## Its sub-modules

`sub_module_terminal/` is the hand's instrument over this layer: per asset its partitions, its contract and its
serpentine search, then one action — a target of this module started through `make`, or one of the serpentine search's
own: draft the profile, read the recorded search, promote the proposal. It writes one file, the draft of
`<TICKER>_serpentine_search_profile.json`. Its orientation is `sub_module_terminal/README_sub_module_terminal.md`.

`sub_module_serpentine_search/` is the serpentine search: a hand's research outside the chain over one asset's search state —
its feature set, its barrier geometry and its hyper-parameter point — under a profile a hand drafted. Its orientation is
`sub_module_serpentine_search/README_sub_module_serpentine_search.md`, its rules
`sub_module_serpentine_search/skill_serpentine_search.md`, and its method `skills/methodology_features.md` § The
serpentine search.
