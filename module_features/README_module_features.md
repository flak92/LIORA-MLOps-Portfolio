# module_features — the canonical series in, the feature catalogue out

The front door of this module: what it is, where its responsibility stops, and
how to run it. Its rules are `skills/skill_feature_taxonomy.md` — the tokens,
the registers, the names, the catalogue record, the warm-up, the two families
and the contract — and `sub_module_serpentine_search/skill_serpentine_search.md`
for the serpentine search, both rendered by `make skills-sync` from the canon's
sheet and cited by `rule_id`; the definitions, the feature id and the serpentine
search's mathematics are `skills/methodology_features.md`; none is repeated
here. *The repository shows the destination, not the road*.

`module_features` reads one asset's partition of the canonical 1m family and
produces the feature catalogue: exact bars on every timeframe of the register —
the asset's partitions of the `bars` family — and every catalogued feature
definition evaluated on every timeframe it is offered on, aligned to the
decision grid — the asset's partitions of the `catalogue` family, one per
timeframe — each family with its `schema.json` beside its partitions. Outside
the chain it holds the serpentine search: a hand's research over one asset's
feature set, barrier geometry and hyper-parameters, each state it reaches scored
by `module_ml` across a file boundary, and a hand's promotion of the one state
it proposes (§ Its sub-modules).

## Where the responsibility stops

It begins at the asset's partition of `ohlcv_1m_canonical`, read as a file, and
asks nothing about where a minute came from; it ends at the two families, the
contract beside them and one snapshot. The labels, the hyper-parameter search,
the model and the strategy belong to `module_ml`; presentation belongs to
`module_monitoring`. The columns a model sees are the asset's feature set — the
default set until a hand promotes a proposal of the serpentine search — and what
a state of that search is worth is `module_ml`'s to compute: the search asks in
one file and reads the answer in another, and imports nothing of it. The bars
are this module's own family, written by `bars.py` and read by the catalogue and
by `module_ml`'s labels through a registered copy of their descriptor; nothing
this module writes lands in another module's files.

Beyond its partitions this module publishes two things. Per asset,
`<TICKER>_catalogue.json` in the asset's folder `ticker=<TICKER>/` — the
contract the ML layer reads instead of importing this module: the decision
timeframe, the hierarchy with each timeframe's duration, the warm-up,
the columns per timeframe in catalogue order, the default set, and the partition
of the `catalogue` family each timeframe's columns live in, as a path under the
artifacts store. And one snapshot, `store/status/features_status.json`, written
by `status.py`: the register, the catalogue with histories and warm-ups, the
nesting — the facts of `config.py` —, the CONFIGURABLES records of `config.py`
and of the serpentine search's `config.py`, and per asset the row counts of its
catalogue partitions and its serpentine search as it last wrote itself.

## Stages

Run in order; `features-all` is the Makefile's chain, each stage in a one-off
container of the `features` runner, and a single stage is its own
`features-<stage>` target, `ASSET=<TICKER>` narrowing a per-asset stage to that
asset — or `python -m module_features.<stage> --tickers <TICKER>` run by hand in
a shell that exports the two `STORE_*_DIR` it reads (`module_skills/skill_glossary.md`
§ Stores). `make features-terminal ASSET=<TICKER>` opens the terminal over the
module's targets and the serpentine search's own actions (§ Its sub-modules).
The per-asset stages — bars, catalogue and the serpentine turn — fan out one
process per asset with its threads pinned to one, one asset at a time unless the
make line says `JOBS=n`; the promotion runs for the one asset `ASSET` names, and
`status` once over the whole basket, which `ASSET` does not narrow.

| stage | target | writes |
|---|---|---|
| bars | `make features-bars` | `bars/ticker=<TICKER>/timeframe=<timeframe>/bars.parquet`, one partition per entry of the register, and `bars/schema.json` |
| catalogue | `make features-catalogue` | `catalogue/ticker=<TICKER>/timeframe=<timeframe>/catalogue.parquet`, one partition per timeframe, `catalogue/schema.json` from the register, and `<TICKER>_catalogue.json` — the contract the ML layer reads |
| status | `make features-status` | `store/status/features_status.json` |
| serpentine turn — outside the chain, by a hand | `make features-serpentine-turn` | `<TICKER>_serpentine_search.json`, its ledger `<TICKER>_serpentine_search_trials.jsonl` and the next question `<TICKER>_score_request.json`, or a finished search |
| promotion — outside the chain, by a hand | `make features-serpentine-search-promote ASSET=<TICKER>` | `<TICKER>_feature_set.json`, `<TICKER>_barriers.json` and `<TICKER>_hyperparameter_point.json`, then the asset's ML chain |

Every stage runs in a one-off container of the `features` runner: a per-asset
stage one container per asset, `status` once. Each stage takes `--tickers`.

## What it writes

```
store/assets_artifacts/bars/ticker=<TICKER>/timeframe=<timeframe>/bars.parquet            one timeframe's bars: the bar's open, OHLCV, ffill_bars, zero_volume_bars
store/assets_artifacts/bars/schema.json                                                   the family's columns, read off a written partition
store/assets_artifacts/catalogue/ticker=<TICKER>/timeframe=<timeframe>/catalogue.parquet  decision_ts and the definitions offered on that timeframe
store/assets_artifacts/catalogue/schema.json                                              the family's columns, from the register
store/assets_artifacts/ticker=<TICKER>/<TICKER>_catalogue.json                            the contract: grid, hierarchy, warm-up, columns, default set, partition paths
store/status/features_status.json                                                         the snapshot: the catalogue as the register presents it, the CONFIGURABLES records, each asset's row counts and serpentine search
```

Outside the chain, in the asset's folder `store/assets_artifacts/ticker=<TICKER>/`:

```
<TICKER>_serpentine_search.json           where the search stands — a turn writes it at the top of every round
<TICKER>_serpentine_search_trials.jsonl   its ledger: one scored state a line, appended and never rewritten
<TICKER>_score_request.json               the question a turn leaves; ml-score answers it as <TICKER>_score_response.json
<TICKER>_serpentine_search_profile.json   what a hand asks the search to look at — drafted, never derived
<TICKER>_feature_set.json                 the promoted columns — the promotion
<TICKER>_barriers.json                    the promoted barrier geometry — the promotion
<TICKER>_hyperparameter_point.json        the promoted hyper-parameter point — the promotion
```

The manifest and what each file holds are in `module_skills/skill_glossary.md`
§ Artifacts.

## Extending

Every element of the taxonomy is one record in one register
(`FEATURE-TAXONOMY-A-REGISTER-IS-RECORDS-BESIDE-THEIR-KERNELS`), and its name,
its computation, its history and its warm-up are read off that record — so
adding one is a local edit, and what it costs is known before it is made. The
rules each element follows are `skills/skill_feature_taxonomy.md`, cited below
by `rule_id`; this is what each addition touches.

| what you add | where, and how much | what it changes | the gate |
|---|---|---|---|
| a timeframe | one token in `HIERARCHY_TIMEFRAMES` (`config.py`, a CONFIGURABLES record) under `FEATURE-TAXONOMY-A-TIMEFRAME-TOKEN-DIVIDES-THE-DAY` — `<integer><unit>`, the unit one of `m`, `h`, `d` and the integer under 100: `TIMEFRAME_UNIT_MS` and `TIMEFRAME_UNIT_SLOT_FIELD` are the accepted set, and a wider number breaks the fixed-width slot the contract carries; a token finer than `DECISION_TIMEFRAME` is read on the decision grid alone, so a finer grid is a move of that record too, and `LABEL_BARRIER_TRUE_RANGE_TIMEFRAME` of `module_ml/config.py` stays an entry of the hierarchy | a different experiment: both families, the contract and the snapshot, the labels, X and every artifact, the final holdout included; a token above the top also moves the trend gate's timeframe — `trend_gate_timeframe()` of `module_ml/config.py` reads the top of the contract's hierarchy — and `WARMUP_END_MS`, which counts bars of the top timeframe, and leaves `MINIMUM_AGREEING_TREND_TIMEFRAMES` of `module_ml/config.py` at its value over a larger hierarchy — decide it in the same commit; the annualisation reads the decision bar's duration off the contract | nothing stays byte-identical; the whole chain reruns; a drafted profile and a promoted `<TICKER>_feature_set.json` name their columns per timeframe and are drafted again, and a recorded serpentine search is reset and run again (`SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT`); the manifest of `module_skills/skill_glossary.md` § Artifacts follows |
| an indicator | its kernel and one record in `INDICATORS` (`indicators.py`): its `parameter_word`, its `warmup_multiple`, its `warmup_offset_bars` for a window over changes, its fixed `inputs` and bounded `output_range` where it has them, and its `historical_aliases` | nothing, until a catalogue record names it | the existing partitions byte-identical |
| a derived series | one entry in `SERIES_KERNELS` (`indicators.py`) | nothing, until a term names it | the existing partitions byte-identical |
| an operator or a normaliser | one record in `OPERATORS` or `NORMALISERS`, beside its kernel (`catalogue.py`) | nothing, until a catalogue record names it | the existing partitions byte-identical |
| a feature definition | one record appended to `FEATURE_CATALOGUE` (`config.py`), never inserted (`FEATURE-TAXONOMY-A-DEFINITION-IS-APPENDED`): its `terms`, its `operators` (one fewer than its terms) and any `normaliser`, its `range`, the `timeframes` it is offered on, its `tier`, any `historical_aliases`, and `definition_in_default_set: False` — the fields are `FEATURE-TAXONOMY-A-CATALOGUE-RECORD-CARRIES-EVERY-FIELD`, their table `skills/methodology_features.md` § The catalogue; then its equation in that section's catalogue table, and the counts wherever they are quoted — the lede of `skills/methodology_features.md` § The catalogue and `README.md` § ML research layer | every `catalogue` partition of a timeframe it is offered on gains a column, `catalogue/schema.json` a column, `<TICKER>_catalogue.json` a column name, the catalogue frame a row, and the serpentine search's `inputs` change; a definition whose warm-up exceeds `WARMUP_TOP_TIMEFRAME_BARS` raises it, and the first decision of every asset moves with it | while the warm-up stands, the existing columns byte-identical, `ml-labels` … `ml-strategy` untouched and `features-status` republishing the catalogue; a recorded search is reset and run again from trial 1 (`SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT`), and a model sees the column only after a promotion; `catalogue.nesting` in `features_status.json` shows whether each level's longest history stays below the shortest of the level above, a criterion no stage asserts (`FEATURE-TAXONOMY-EFFECTIVE-HISTORIES-ARE-SHOWN-NOT-ASSERTED`) — update the nesting paragraph of `skills/methodology_features.md` § The catalogue in the same commit |
| a second parameter for an indicator | the record and the name grammar, in one commit (`FEATURE-TAXONOMY-A-TERM-IS-ITS-TOKEN-AND-ONE-PARAMETER`) | the derived names of existing terms do not change | the existing partitions byte-identical |

`definition_in_default_set: True` is a different move: it puts the column into
every asset's X where no feature set is promoted, so the ML chain reruns,
today's numbers move and a recorded serpentine search is reset and run again
(`SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT`). The default
set is the frozen experiment's; a set chosen for one asset is the serpentine
search's proposal and a hand's promotion (§ Its sub-modules). A new asset is not
an extension of this module at all: it is one more token in `TICKERS` of the
Makefile (`README.md` § The basket); nothing changes here, every per-asset stage
follows it without an edit, and a serpentine search of it needs a profile a hand
drafts first.

## Design rationale

Why each object of this module sits where it does — the answers the naming review asks for
(`SELF-EXPLAINING-NAMING-A-NEW-OBJECT-PASSES-THE-NAMING-REVIEW`) written down, one row per object, analogous pair
or the module's documents; the mapping row it answers to is a row of the mapping table of `module_skills/README.md`
§ The Pre-AWS mapping, cited by its *responsibility* column and never repeated
(`PRE-AWS-SOLUTION-A-PLACEMENT-ANSWERS-TO-ONE-RESPONSIBILITY`).

| object | why here | why beside these | why this boundary | answers to |
|---|---|---|---|---|
| `config.py` | The module's CONFIGURABLES records — what an operator may set, each value written once — and the one definition every timeframe-shaped and feature-shaped thing derives from: the hierarchy, the frozen research window and its warm-up, the catalogue and its descriptors (`feature_definition_name()`, `feature_id()`, the histories and the warm-ups), the descriptors of the two families and their `schema.json`, the contract `catalogue_contract()` with its descriptor `catalogue_json()`, and the snapshot's path; it carries its own copies of the units, the DuckDB ceiling, the two store reads, the descriptors of the asset folder, a partition and the canonical family, `to_utc_ms()` and the `--tickers` parser — twice by extraction, each copy as its row in `module_skills/skill_glossary.md` § Twice by extraction says — and re-exports the indicator register from `indicators.py`. | Every stage and the serpentine search import it; it imports nothing of another module, `module_ml` imports nothing from it and reads the contract file instead, and nothing outside this module builds the path of a `catalogue` partition — the ML layer reads it off the contract. | A stage reaches a partition by descriptor (`module_skills/skill_pre_aws_solution.md` § Correlatable artifacts, without a version scheme), so the families keep the same paths under `/store` on whatever disk is mounted there. | STORAGE — research artifacts |
| `bars.py` | The writer of the `bars` family: the aggregations of the canonical 1m series inside the research window on every timeframe of the register, one partition per asset and timeframe, the family's `schema.json` beside them — DuckDB the engine in memory, the canonical family read as a file (its docstring). | It imports `config.py` and `dataset.py`, reads the asset's partition of `ohlcv_1m_canonical` that `module_data/ingest.py` wrote, and `catalogue.py` and `module_ml`'s labels read the partitions it writes. | It runs one asset at a time in a one-off container of the `features` runner with `--tickers <TICKER>` (§ Stages) and writes at `bars_parquet()`, opening no other module's file for writing — the same argument and the same paths whatever host runs the container. | COMPUTE — one stage for one asset |
| `indicators.py` | Pure numpy kernels — the recursive operations and the rolling statistics — and the two registers beside them, `SERIES_KERNELS` and `INDICATORS`, one record per token naming the kernel's invariants once (its docstring); a library, not a stage. | `config.py` imports the indicator register and re-exports it, `catalogue.py` imports the kernels and both registers, `module_ml/labels.py` carries its own copies of `recursive_mean()`, `true_range()` and `asof_index()` (twice by extraction), and it imports nothing of the module. | It reads no file and writes none, so nothing in it names a path — the same kernels run in whichever container imports them. | COMPUTE — one stage for one asset |
| `catalogue.py` | FEATURE — the catalogue on the decision grid: every definition of `config.py` evaluated by folding its terms through the operators, every value from the last closed bar of its timeframe (its docstring; `skills/methodology_features.md`). | It imports `config.py`, `dataset.py` and `indicators.py`, reads the partitions of the `bars` family and writes the partitions of the `catalogue` family, its `schema.json` and the contract `<TICKER>_catalogue.json` that `module_ml/dataset.py` reads. | It runs one asset at a time in a one-off container of the `features` runner with `--tickers <TICKER>` (§ Stages) and writes at `catalogue_parquet()` — the same argument and the same paths whatever host runs the container. | COMPUTE — one stage for one asset |
| `dataset.py` | The parquet writer of this layer, `write_parquet()`, the schema read off a written partition, `load_partition_schema()`, its canonical JSON writer, `write_json()`, and the readers and the ledger's batch append the serpentine search reads and writes with, `load_json()`, `load_jsonl()` and `append_jsonl()` — all but `append_jsonl()` twice by extraction, identical in `module_ml/dataset.py` (its docstring). | `bars.py`, `catalogue.py`, `status.py` and the serpentine search import it, and it imports `config.py` alone; nothing outside the module imports it. | It writes to the descriptor it is handed and builds no path of its own, so an artifact lands where a `config.py` says on whatever disk is mounted at `/store`. | STORAGE — research artifacts |
| `status.py` | The stage that measures this module's own facts — the catalogue as the register presents it, the module's CONFIGURABLES records, and each asset's row counts and serpentine search as it last wrote itself — published as `store/status/features_status.json` (its docstring). | It imports `config.py`, `dataset.py` and the serpentine search's `config.py`, `coordinate_feature_set.py` and `serpentine_search.py`; it reads the partitions `catalogue.py` wrote, the contract, the parameters file, the profile, the state file and its ledger, and writes the snapshot `ml.js` fetches for the catalogue frame. | It takes `--tickers` like every stage and runs once in a one-off container of the `features` runner, writing at `FEATURES_STATUS_JSON_PATH` under the `STORE_STATUS_DIR` the launcher names. | COMPUTE — one stage, one one-off process |
| `__init__.py` | The package that makes `python -m module_features.<stage>` a command (§ Stages), its docstring the module's responsibility in one line. | It names the register, the bars, the kernels, the catalogue, the contract, the snapshot and the serpentine search, and imports nothing. | The same `python -m module_features.<stage> --tickers <TICKER>` runs in a one-off container of the `features` runner (§ Stages) — the launcher setting the two `STORE_*_DIR` — the command `docker compose run --rm -T features` carries unchanged whichever host starts it. | COMPUTE — one stage, one one-off process |
| the module's documents — `README_module_features.md` and `skills/` | This orientation, the rules of `skills/skill_feature_taxonomy.md` — rendered from the canon's sheet — and the method `skills/methodology_features.md`, a reference for a human, filed by ownership (`../AGENTS.md` § The default choice); the serpentine search's rules are `sub_module_serpentine_search/skill_serpentine_search.md` and its orientation `sub_module_serpentine_search/README_sub_module_serpentine_search.md`, beside its code, and its method `skills/methodology_features.md` § The serpentine search. | The orientation points at the documents beside it (§ Its normative skills), and every rule about this module sits in `skills/` (`../AGENTS.md` § Canonical vocabulary, the row *a module's own skills*). | Tracked files under `module_features/` that no stage and no route reads, travelling with the code beside them — the same paths beside the code wherever the code is. | no row — a document that travels with the module's code, beside it |
| `sub_module_terminal/` | The module's own terminal — the hand's instrument over this layer: each asset's bars and catalogue partitions, its contract and its serpentine search, then one of the module's targets started through `make`, or the serpentine search's draft, recorded search and promotion (§ Its sub-modules). | It imports the standard library and its own package alone, and nothing of the package above it: `config.py` imports `.indicators`, and numpy with it, and the serpentine search's `config.py` imports that one, so it carries registered copies of the store read, the descriptors and the records it reads. | It runs on the host's `python3` with gum, in no container and no venv, and computes nothing: what it starts, the Makefile names — its orientation is `sub_module_terminal/README_sub_module_terminal.md`, its rules `module_skills/skill_tui_designer.md`. | no row — a hand's instrument, beside the stages it starts |
| `sub_module_serpentine_search/` | The serpentine search, a hand's research outside the chain over one asset's feature set, barrier geometry and hyper-parameters: `serpentine_search.py` one turn, `coordinate_barrier.py` and `coordinate_feature_set.py` the moves of the two coordinates it generates, `promote.py` the promotion, and `config.py` its CONFIGURABLES records, its round, the constants of its gate and the one place it builds a path (its orientation, `sub_module_serpentine_search/README_sub_module_serpentine_search.md`). | It imports this module's `config.py` and `dataset.py` and nothing of another module — the values a state is made of and the files of the evaluation contract are registered copies — and `status.py` imports it to publish each asset's search. | What a state is worth crosses to `module_ml` as two files, the question and the answer, never as an import; a turn and a promotion each run in a one-off container of the `features` runner with `--tickers <TICKER>`, and the loop that alternates a turn with `ml-score` is the Makefile's. | COMPUTE — one stage for one asset |

## Its sub-modules

`sub_module_terminal/` is the hand's instrument over this layer: per asset, how
many timeframes its bars and its catalogue hold a partition for, whether its
contract stands, where its serpentine search profile stands and how many trials
the search's ledger holds; then one action — a target of this module started
through `make` with `ASSET=<TICKER>`, or one of the serpentine search's own:
draft the profile, read the recorded search, promote the proposal — after which it
closes. The Makefile is where a container and the order of the chain are named.
It computes nothing and writes one file, the draft of
`<TICKER>_serpentine_search_profile.json`: it runs on the host's `python3` and
gum, imports the standard library and its own package alone, and cannot import
`config.py`, which imports `.indicators` and numpy with it, so
it carries registered copies of what it reads (`module_skills/skill_glossary.md`
§ Twice by extraction). Its orientation is
`sub_module_terminal/README_sub_module_terminal.md`, and its rules — the
standards of every terminal's screens — `module_skills/skill_tui_designer.md`.

`sub_module_serpentine_search/` is the serpentine search: a hand's research
outside the chain over one asset's state — its feature set, its barrier geometry
and its hyper-parameter point — under a profile a hand drafted. Its orientation
is `sub_module_serpentine_search/README_sub_module_serpentine_search.md` — the
turn, the answer, the loop, the profile, the promotion and the reset — and its
rules `sub_module_serpentine_search/skill_serpentine_search.md`, both beside its
code; its method, its thresholds and their limits are
`skills/methodology_features.md` § The serpentine search.

## Its normative skills

| document | answers |
|---|---|
| `skills/skill_feature_taxonomy.md` | rendered from the canon's sheet: the tokens of the timeframe hierarchy, the registers beside their kernels, the terms and the feature ids, the catalogue record and its order, the default set, the warm-up, the effective histories — published, not asserted — and the two families and the contract |
| `sub_module_serpentine_search/skill_serpentine_search.md` | rendered from the canon's sheet: the question and the answer across the file boundary, resume and reset, the tracked record, the key of a state, the gate, the beam, the convergence, the proposal with its noise margin and its count, and the promotion |
| `skills/methodology_features.md` | hand-written, a reference for a human: every catalogued definition, equation by equation, with its histories and citations; the field table; the feature id; the serpentine search's objective, gate, margin and stopping, and why one search is one experiment |

Project-wide rules are in `module_skills/`, the canon beside the modules, indexed by
[module_skills/README.md](../module_skills/README.md); the market object it reads is
defined by `module_data/skills/skill_candle_canonicalisation.md`, and what the research
layer does with the catalogue is `module_ml/README_module_ml.md`.
