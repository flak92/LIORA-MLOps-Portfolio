# Act: naming conventions — the enacted names of this project

`AGENTS.md` holds the grammars — how a name is derived. This act holds the
decisions — which exact names the project enacted where a grammar left a
choice. One normative source each: a rule lives in the contract, a decision lives
here, and a new decision enters this act in the commit that enacts it. Every
entry names the rejected form, because the rejected form is what stops the
next reader from reinventing it. In the wider vocabulary this file is an
architecture decision record: `enacted | not | why` is that shape, and the
enacted names are the decisions.

## Enacted names

| # | enacted | not | why |
|---|---|---|---|
| 1 | `module_data/`, `module_ml/`, `module_monitoring/`, `module_skills/`, `module_visualisation/` | `src`, `core`, `lib` | category first so siblings sort together; the shortest name whose kind-first files say the rest; "for the project" repeats the scope it lives in |
| 2 | `store_assets_artifacts/` | `assets/`, `artifacts/` | category first, then what the store holds, in the ordinary lowercase snake_case every other store uses — so `STORE_ASSETS_ARTIFACTS_DIR` mirrors the directory exactly and no rule has to explain a capital letter |
| 3 | `store_db/` | `db`, `database` | category first; `db` is unambiguous in this technical context |
| 4 | `store_raw_1m/`, and every future raw store as `store_raw_<timeframe>/` | a store spelling its timeframe in sorting slots, `raw_data` | a store is one object: its name says what it holds, in the compact timeframe token the code and the schema already speak (`ohlcv_1m_canonical`, `SOURCE_CANDLE_INTERVAL`), so the next raw store names itself. Sorting slots are for the file family that has to sort by granularity (§ timeframe slots) |
| 5 | `<TICKER>/` in capitals inside `store_assets_artifacts/` | `btc`, `BTCUSDT` | the ticker is the project's asset identity, spelled the way the basket spells it; the exchange symbol belongs to the adapter boundary |
| 6 | Lean raw tree spelling: `cryptofuture/<venue>/minute/<symbol lowercase>/`, `YYYYMMDD_trade.zip` | project-cased variants | external-format boundary — Lean's vocabulary wins inside the store it defines |
| 7 | guidance files: `act_*`, `check_*`, `skill_*`, `methodology_*`, `glossary.md`; `module_skills/` holds **exactly one executable file**, the self-check | bare topic names, a second script in the law folder | category first inside the folder, same rule as the tree above it. The one `.py` is the act's own enforcement; counting it at one keeps the law folder from becoming a code folder |
| 8 | the asset folder manifest (§ below): every per-asset file carries the `<TICKER>_` prefix, a time series carries its grid in timeframe slots | `features.parquet`, a bare `README.md` — any per-asset file that needs its folder to say which asset it belongs to | the file identifies its asset and its grid on its own, and the folder lists as one contiguous `<TICKER>_*` block |
| 9 | OHLCV lives only in DuckDB; the asset folder publishes no price series | a per-asset OHLCV parquet, an `export` stage | the market object has one home and every stage reads it there; a published copy nothing reads is weight without function |
| 10 | two files per asset, one drafted and one derived — `<TICKER>_config.json` (row 30) and `<TICKER>_parameters.json`, the one parameters file, written by `module_ml/hpo.py`; one shared strategy (`module_ml/strategy.py`) | a parameters file per stage, a strategy file per asset, a hand-edited section inside the derived parameters file | code is common, parameters are per asset; the two sections keep the a-priori configuration and the search result apart inside one file, and the drafted input keeps its own file because the derived one is never hand-edited |
| 11 | every count key is `<what>_count`: `row_count`, `gap_count`, `duplicate_count`, `ohlc_violation_count`, `source_switch_count`, `decision_count`, `ambiguous_event_count`, `unobservable_entry_count`, `trainable_row_count`; a UTC string is `_utc` (`window_start_utc`, `first_observation_utc`); `return` is spelled out (`max_abs_return_1m`) | a bare plural (`rows`, `gaps`), an adjective holding a number (`ambiguous`), `_ts` on a string, `ret` for a return | one grammar for a number: the suffix says it is a count, the word says of what; a bare plural or an adjective made the reader guess, and `_ts` already means epoch milliseconds in the parquets |
| 12 | the asset folder manifest is written in `LC_COLLATE=C` listing order wherever it is written (this act, the register, `FILE_MANIFEST`, the store guide) | reading order, artifact-responsibility order | one order that a byte-comparing `ls` reproduces; three orders made the same ten files look like three manifests |
| 13 | make targets `data-download`, `data-download-binance`, `data-download-bybit`, `data-ingest`, `data-status` and the container twins `docker-data-download`, `docker-data-ingest`, `docker-data-status`; `docker-build`, `docker-up`, `docker-down` are compose lifecycle, not twins, and the single-venue downloads have no twin | bare `download`, `ingest`, `status`; `docker-download` | `<module>-<stage>` beside `ml-<stage>`: `make help` lists one module as one block, and `status` stops being ambiguous next to `ml-status` |
| 14 | `<TICKER>_README.md` with README in capitals | `<TICKER>_readme.md`, a bare `README.md` | README is a convention older than this act; it is the one manifest entry whose position depends on collation (first under `LC_COLLATE=C`, ninth under `en_US.UTF-8`) — the `<TICKER>_*` block stays contiguous under both, and GitHub renders neither spelling as the folder's README |
| 15 | `EXAMPLE_TICKER_README.md` sorts inside the ticker block of `store_assets_artifacts/` | a store-root `README.md` | the guide is found where a reader looks for an asset folder; `ls -1d */` sees only the ten ticker directories |
| 16 | ecosystem-fixed file names keep their spelling: `__init__.py`, `AGENTS.md`, `Dockerfile`, `Makefile`, `README.md`, `docker-compose.yml`, `requirements.txt`, `.github/workflows/*.yml` | project-cased variants | a boundary like Lean's casing (row 6); they are the only names whose sort position depends on collation, so the collation check binds every other directory |
| 17 | the stage order lives in the Makefile (`all:`, `ml-all:`); every document points there | a second copy of the chain in README or a methodology | two copies drift; the per-asset reproduce line of `<TICKER>_README.md` is derived from the same order by `module_ml/status.py` |
| 18 | `module_visualisation/` | `module_visualisation_helpers/`, `module_viz/`, a page generator folded into `module_monitoring/` | one responsibility with a stable boundary: git index in, one HTML page out. It reads no measurement, so `module_monitoring` does not own it; `helpers` is the `utils` family the skills forbid |
| 19 | `visualisation-generate`, `visualisation-check` | bare `galaxy`, `galaxy-check`, `visualisation-galaxy`, bare `visualisation` | a stage carries its module, as `data-ingest` and `ml-hpo` do. A module name is not a stage, and the legal set is closed |
| 20 | `files_and_folders_visualisation_template.html` for the shell, `module_monitoring/files_and_folders_visualisation.html` for the page it renders | `Files_and_Folders_Visualisation.html`, `galaxy_template.html`, a template and a page sharing one basename | the `_template` suffix separates shell from output. Lowercase retires the collation exemption this row carried: `module_visualisation/` now differs between collations only by the row-16 names |
| 21 | one stem for the picture: `module_visualisation/generate.py`, `visualisation_config.json`, `module_monitoring/files_and_folders_visualisation.html`, `.github/workflows/visualisation.yml`, `VisualisationError`, `visualisation_html()`, `VISUALISATION:STRUCTURE:*`, page title `Files and Folders` | the whole `galaxy` family: `generate_galaxy.py`, `galaxy_config.json`, `repo_galaxy.html`, `galaxy.yml`, `GalaxyError`, `galaxy_html()`, `GALAXY:STRUCTURE:*`, `Repo Silk Galaxy` | one thing, one vocabulary. The stem named the drawing's appearance, not its subject; banned outright, so it cannot return by halves |
| 22 | make target `monitoring-dashboard`; the compose **service** stays `dashboard` | a bare `dashboard` target | the last non-lifecycle target without its module; row 13's reason applies unchanged. A compose service is a different namespace and keeps its own name |
| 23 | the rule-derived-structure rule lives in `AGENTS.md` § Canonical vocabulary; `module_skills/skill_agent_first_development.md` points at it | a second copy of the rule in a skill | a rule lives in one place and every other document points at it. It forbids no specific name, so the block records it as a preference, not a grammar |
| 24 | no debt marker in a tracked file: `TODO`, `FIXME`, `XXX`, `HACK`, and no code left inside a comment | a marker standing in for a decision | `main` is clean working logic. A marker is a postponed decision; a commented-out line is a version git already holds |
| 25 | established terminology over local coinages; the rule lives in `AGENTS.md` § Canonical vocabulary | a local synonym for a concept that has a recognised name | a coinage costs every reader a translation step. It forbids no specific name, so the block records it as a preference, not a grammar — and where it meets a rule that can be checked, the checkable rule wins: `category-prefixed naming` fell to a third sense of `prefix` (row 26), `single source of truth` to a referent already taken (row 27) |
| 26 | `taxonomic ordering` for the rule that the category token leads a name | `kind-first` | `kind` is unqualified English and reads as a synonym for `type`; `prefix` already carries two other senses here (`<TICKER>_`, make-target stages), so a third would collide |
| 27 | `normative source` for the one document that holds a rule | `One authority`, `one canonical owner`, `single source of truth` | `normative` against `informative` is the ISO/IETF distinction between binding and explanatory text. `single source of truth` is already taken in `module_data/config.py` with a different referent |
| 28 | `closed list` for the enumerable set of allowed words; `closed grammar` stays, and names the formation rule that draws from it | `closed vocabulary` | two names for the set was the defect; the grammar is a different concept and keeps its own name |
| 29 | the desktop viewport is the only target for the front end | a mobile or tablet layout, a width breakpoint, a touch-only gesture, a viewport meta | one viewport is one layout to reason about. Pointer events and `prefers-reduced-motion` are not mobile and stay |
| 30 | `<TICKER>_config.json` — the asset's hand-written input: its registration in the folder, and the engine overrides it takes; the basket stays `TICKERS` in `module_data/config.py`, and `ticker_registry` settles that the list and the registered folders agree | `<TICKER>_indicators.json`, a basket read from the working tree, a schema with no reader, `ASSET` as the default of `ticker_parser` | the registration cannot live in `<TICKER>_parameters.json`, which `module_ml/hpo.py` writes and *derived, never drafted* forbids editing; a key enters on the day a stage reads it and an asset sets it, so every file is `{}` until then; the list stays the one local definition every path derives from, and the working tree is not the index — a folder git does not track must not move the basket |

## External vocabularies

Row 6 is the first instance of a rule that holds at every boundary: inside the
call that speaks an external format or library, the external spelling wins, and
the project's names begin at the return value. An unnamed boundary is the class of
names a mechanical rename walks into by accident — to a regular expression an
SVG attribute like `viewBox` is an identifier, to the browser it is a contract —
so every one is listed here with the file that owns it.

| boundary | owning file | words that stay external |
|---|---|---|
| QuantConnect Lean minute-trade format | `module_data/lean.py` (names, writer, full-day predicate); the tree above the file name comes from `module_data/config.py` | `cryptofuture/<venue>/minute/<symbol>/`, `YYYYMMDD_trade.zip`, `YYYYMMDD_<symbol>_minute_trade_perp.csv` |
| Binance REST | `module_data/download_binance.py` | `symbol`, `interval`, `startTime`, `endTime`, `limit` |
| Bybit REST v5 | `module_data/download_bybit.py` | `category`, `interval="1"`, `start`, `end`, `limit`, `retCode`, `retMsg`, `result.list` |
| xgboost, and the sklearn pair it borrows | `module_ml/model.py` | `DMatrix`, `train`, `num_boost_round`, `predict`, `get_score`, `fit`, `predict_proba`, the hyper-parameter names in `best_params` |
| optuna | `module_ml/model.py`, `module_ml/hpo.py` | `trial.suggest_int/float`, `create_study`, `TPESampler`, `n_trials`, `n_jobs`, `best_trial` — and the borrowed verb `suggest_params`, legal because the closed I/O verb list binds I/O functions only |
| argparse | `module_data/config.py` (`ticker_parser`) | `ArgumentParser`, `add_argument`, `parse_args` |
| SVG / DOM | `module_monitoring/*.js` | `setAttribute`, `viewBox`, `preserveAspectRatio`, `x1`, `y1`, `points`, `insertRow`, `createTHead`, `textContent` |
| DuckDB SQL | `module_data/ingest.py`, `module_data/status.py`, `module_ml/bars.py`, `module_ml/dataset.py`, `module_ml/features.py`, `module_ml/labels.py`, `module_ml/strategy.py` | `read_csv`, `read_parquet`, `arg_min`, `arg_max`, `FILTER`, `quantile_cont`, `last_value … IGNORE NULLS`, `fetchnumpy` |
| docker compose | `Makefile` (`docker-up`, `docker-down`), `docker-compose.yml` | `up`, `down`, `run --rm`, `${PORT:-8900}` |
| git plumbing | `module_visualisation/generate.py` | `ls-files -z`, `rev-parse`, `rev-list --parents`, `show --first-parent --name-only`, `%h`, `%cI`, `:(exclude)` |
| GitHub Actions | `.github/workflows/visualisation.yml` | `on`, `push`, `paths-ignore`, `concurrency`, `cancel-in-progress`, `permissions`, `runs-on`, `steps`, `uses`, `github.actor`, `github-actions[bot]`, `[skip ci]` |

The browser is a boundary of its own: it has no config module, so `data.js` and
`ml.js` fetch the two snapshots by literal name. Before any mechanical rename,
run the pre-sweep grep and confirm that every hit sits inside an owning file
above: `git grep -n 'setAttribute("\|suggest_\|retCode\|startTime\|DMatrix\|read_csv\|read_parquet' -- '*.py' '*.js'`.

## The asset folder manifest

`store_assets_artifacts/<TICKER>/` holds exactly these ten files. No OHLCV:
the canonical series and its aggregations live only in DuckDB — the asset
folder carries the asset's features, parameters, evaluations and guide. Every
file is prefixed with its ticker, every time series carries its grid in
timeframe slots, and paths are built only by the descriptors in the modules'
`config.py`:

The table is in `LC_COLLATE=C` listing order — the register and the generated
README use the same one, so the three can be checked against each other by eye:

| file | holds | written by |
|---|---|---|
| `<TICKER>_README.md` | what the folder holds and what came out of it | `module_ml/status.py` |
| `<TICKER>_config.json` | the asset's registration in its folder, and the engine overrides it takes — `{}` while it takes none | hand-written |
| `<TICKER>_features_ss-15-hh-dd-MM.parquet` | the five 15m family columns on the decision grid | `module_ml/features.py` |
| `<TICKER>_features_ss-mm-01-dd-MM.parquet` | the five 1h family columns on the decision grid | `module_ml/features.py` |
| `<TICKER>_features_ss-mm-04-dd-MM.parquet` | the five 4h family columns on the decision grid | `module_ml/features.py` |
| `<TICKER>_label_events_ss-15-hh-dd-MM.parquet` | Y — triple-barrier events (regenerable work product) | `module_ml/labels.py` |
| `<TICKER>_model_evaluation.json` | classification results per fold, gain importance, populations | `module_ml/train.py` |
| `<TICKER>_oos_predictions_ss-15-hh-dd-MM.parquet` | out-of-sample probabilities (regenerable work product) | `module_ml/train.py` |
| `<TICKER>_parameters.json` | the one parameters file: sections `experiment_configuration` (a-priori) and `hyperparameter_search_result` (the chosen point, its log-loss, the trial count) | `module_ml/hpo.py` |
| `<TICKER>_strategy_evaluation.json` | the entry edge threshold, PnL per fold, the equity curve | `module_ml/strategy.py` |

The `.gitignore` whitelist is the manifest's fifth site: it names the three
tracked files, `<TICKER>_README.md`, `<TICKER>_config.json` and
`<TICKER>_parameters.json`; the other seven are regenerable and stay out.

The columns inside a per-timeframe features file carry only their family
names — the filename already says the timeframe, and a name repeats nothing
its scope states. The strategy itself is one shared file for the whole
project, `module_ml/strategy.py`: code is common, parameters are per asset.
A file copied out of its folder still says which asset it belongs to and
which grid it lives on. The store root carries one committed guide,
`store_assets_artifacts/EXAMPLE_TICKER_README.md`, describing every manifest
file and its contents for a placeholder ticker.

## The timeframe slot standard

A file that belongs to a timeframe family writes its granularity as five fixed slots,
finest to coarsest: `ss-mm-hh-dd-MM` (seconds, minutes, hours, days, months).
The active granularity is a zero-padded number in its slot; every inactive
slot keeps its unit letters as a placeholder.

| timeframe | slots |
|---|---|
| 1 second | `01-mm-hh-dd-MM` |
| 1 minute | `ss-01-hh-dd-MM` |
| 15 minutes | `ss-15-hh-dd-MM` |
| 1 hour | `ss-mm-01-dd-MM` |
| 4 hours | `ss-mm-04-dd-MM` |
| 1 day | `ss-mm-hh-01-MM` |
| 1 month | `ss-mm-hh-dd-01` |

Why it sorts: ASCII digits precede letters, so a filled slot beats a
placeholder at the same position and finer granularity always lists first —
verified identical under `LC_COLLATE=C` and `en_US.UTF-8`. Zero-padding keeps
numeric order inside a slot; the fixed slot count keeps listings
column-aligned. The mechanics are the subject of
`skill_sorting_files_naming_standard.md`.

Two patterns, two jobs — a name follows the one that fits its object:

```
STORE, one object, an identity:     store_raw_<timeframe>/
                                    store_raw_1m/   store_raw_5m/   store_raw_1h/

FILES, a family that must sort by   <asset>_<artifact>_<timeframe-slot>.<ext>
granularity inside one listing:     BTC_features_ss-15-hh-dd-MM.parquet
                                    BTC_features_ss-mm-01-dd-MM.parquet
                                    BTC_features_ss-mm-04-dd-MM.parquet
```

A store has no siblings to order, so it takes the token the rest of the project
speaks; the three feature files of one asset are read as one block, so they take
the slots that put the finest first.

## The serialized-schema boundary

The slot standard governs filesystem names. Serialized schema — DuckDB tables
(`ohlcv_1m_canonical`, `ohlcv_15m_canonical`…), parquet columns, feature names
(`centered_rsi14_15m`) and artifact keys — keeps the compact `1m/15m/1h/4h`
tokens: those names are contracts with the files on disk, and a schema
migration is not a naming cleanup. They adopt the standard only at the next
schema-breaking change, recorded here when it happens.

The same deferral covers two more names the schema already carries: the
epoch-millisecond columns `decision_ts`, `entry_ts`, `event_end_ts` of the
parquets (the key grammar says `_ms`; no new `_ts` is minted), the DuckDB column
`rel_divergence` (published only as `relative_divergence_*`). A compact timeframe
token inside an identifier or a key (`WARMUP_4H_BARS`, `folds.warmup_4h_bars`,
`equity_15m`) is not a deferral at all: it is the timeframe vocabulary of code
and schema, and the slots are for the file family that sorts by granularity.

## Machine-checkable form

The prose above is the law a human reads. The block below is the same law in the
form a script can settle, and `module_skills/check_conventions.py` reads nothing
else — no list lives in that file, which is why its own checks can scan it
without an exemption. One law, two audiences, and no third copy to drift.

A rejected form is rejected **in a role**, not everywhere: `core` is a directory
this act refused and a live key of the picture's config; `BTCUSDT` is a folder
name it refused and the venue's own symbol, published four times in
`data_status.json`. The `mode` cell says which role, and that is what keeps the
exemption list short instead of keeping the check quiet.

Some rejected forms are prose — "project-cased variants" is not a token — and
some are already settled by another check here or by a one-liner in
`skill_self_explaining_naming.md`. Both sets stay in the block with their reason,
and the verifier prints their count on every run, so it never looks more complete
than it is.

```conventions-data
# One rule per line: <key> <cell> | <cell> | ... — cells are trimmed, # is a comment.
# mode: path_segment = not a component of any tracked path; path_exact = not a
# tracked path; owned = settled by the check or one-liner named in the fix.

rejected_name  src | path_segment | 1 | a top-level responsibility is module_<domain>
rejected_name  core | path_segment | 1 | a top-level responsibility is module_<domain>
rejected_name  lib | path_segment | 1 | a top-level responsibility is module_<domain>
rejected_name  assets | path_segment | 2 | the store is store_assets_artifacts/
rejected_name  artifacts | path_segment | 2 | the store is store_assets_artifacts/
rejected_name  store_assets | path_segment | 2 | the store is store_assets_artifacts/
rejected_name  db | path_segment | 3 | the store is store_db/; db_bytes is a key, not a directory
rejected_name  database | path_segment | 3 | the store is store_db/
rejected_name  raw_data | path_segment | 4 | a raw store is store_raw_<timeframe>/
rejected_name  btc | path_segment | 5 | an asset folder is the ticker in capitals
rejected_name  BTCUSDT | path_segment | 5 | the venue symbol stays at the adapter boundary
rejected_name  data | path_segment | 8 | a per-asset file carries the <TICKER>_ prefix; the folder is flat
rejected_name  common | path_segment | 18 | the responsibility already has an owner
rejected_name  store_assets_artifacts/README.md | path_exact | 15 | the store guide is EXAMPLE_TICKER_README.md
rejected_name  features.parquet | owned | 8 | ticker_manifest requires the <TICKER>_ prefix
rejected_name  download | owned | 13 | target_prefixes rejects a bare stage
rejected_name  ingest | owned | 13 | target_prefixes rejects a bare stage
rejected_name  status | owned | 13 | target_prefixes rejects a bare stage
rejected_name  docker-download | owned | 13 | target_prefixes rejects a twin named after the tool
rejected_name  dashboard | owned | 22 | target_prefixes rejects it as a make target; the compose service keeps it
rejected_name  galaxy-check | owned | 21 | single_vocabulary bans the stem outright
rejected_name  galaxy_template.html | owned | 21 | single_vocabulary bans the stem outright
rejected_name  module_viz | owned | 18 | single_vocabulary bans the viz stem
rejected_name  module_visualisation_helpers | owned | 18 | single_vocabulary bans the helpers stem
rejected_name  rows | owned | 11 | the `count keys` one-liner of skill_self_explaining_naming.md
rejected_name  gaps | owned | 11 | the `count keys` one-liner of skill_self_explaining_naming.md
rejected_name  ambiguous | owned | 11 | the `count keys` one-liner of skill_self_explaining_naming.md
rejected_name  ret | owned | 11 | the `abbreviation ret` one-liner of skill_self_explaining_naming.md

banned_stem  galaxy | 21 | the module, its targets, its page and its title all say visualisation
banned_stem  authority | 27 | the term is normative source
banned_stem  generative | 23 | the term is rule-derived structure
banned_stem  kind-first | 26 | the category token leads the name; the term is taxonomic ordering
banned_stem  mobile | 29 | the desktop viewport is the only target
banned_stem  responsive | 29 | the desktop viewport is the only target
banned_stem  tablet | 29 | the desktop viewport is the only target
banned_stem  tablets | 29 | the desktop viewport is the only target
banned_stem  phone | 29 | the desktop viewport is the only target
banned_stem  phones | 29 | the desktop viewport is the only target
banned_stem  breakpoint | 29 | the desktop viewport is the only target
banned_stem  breakpoints | 29 | the desktop viewport is the only target
banned_stem  viz | 18 | module_visualisation is spelled out
banned_stem  utils | 18 | the responsibility already has an owner
banned_stem  helpers | 18 | helpers names the author's convenience, not the responsibility
banned_stem  manager | 18 | the responsibility already has an owner

collation_exempt  __init__.py | 16 | ecosystem-fixed
collation_exempt  AGENTS.md | 16 | ecosystem-fixed
collation_exempt  Dockerfile | 16 | ecosystem-fixed
collation_exempt  Makefile | 16 | ecosystem-fixed
collation_exempt  README.md | 16 | ecosystem-fixed
collation_exempt  docker-compose.yml | 16 | ecosystem-fixed
collation_exempt  requirements.txt | 16 | ecosystem-fixed
collation_exempt  .github | 16 | ecosystem-fixed; the collation key drops a leading dot
collation_exempt  .gitignore | 16 | ecosystem-fixed; the collation key drops a leading dot
collation_exempt  .dockerignore | 16 | ecosystem-fixed; the collation key drops a leading dot
collation_exempt  <TICKER>_README.md | 14 | README in capitals, by decision

content_scan_exempt  module_skills/act_naming_conventions.md | its rejected-forms column and this block are the normative source for those tokens
content_scan_exempt  AGENTS.md | the `what it forbids` column of the grammar table, and its prose bans
content_scan_exempt  module_skills/glossary.md | every `never` column
content_scan_exempt  module_skills/skill_agent_first_development.md | the utils/common/core/manager/service ban
content_scan_exempt  module_skills/skill_self_explaining_naming.md | its Checks block embeds the forbidden patterns
content_scan_exempt  module_skills/skill_sorting_files_naming_standard.md | it names the collation exemptions
content_scan_exempt  module_skills/skill_dashboard_conventions.md | it names the generated page and its exceptions
content_scan_exempt  module_skills/methodology_data.md | the venue symbol at the ingest boundary
content_scan_exempt  module_data/download_binance.py | the Lean tree diagram in its docstring
content_scan_exempt  module_data/download_bybit.py | the Lean tree diagram in its docstring

top_level_category  module_ | 1 | a top-level responsibility
top_level_category  store_ | 2 | persisted or generated state

enacted_path  module_data | 1 | the runtime ingest module
enacted_path  module_ml | 1 | the runtime research module
enacted_path  module_monitoring | 1 | the presentation module
enacted_path  module_skills | 1 | the contract's companions
enacted_path  module_visualisation | 18 | git index in, one HTML page out
enacted_path  store_assets_artifacts | 2 | category first, then what the store holds
enacted_path  module_data/lean.py | 6 | the Lean adapter owns the external spelling
enacted_path  module_ml/strategy.py | 10 | one shared strategy for the whole project
enacted_path  module_skills/act_naming_conventions.md | 7 | this act
enacted_path  module_skills/check_conventions.py | 7 | the one executable module_skills owns
enacted_path  module_skills/glossary.md | 7 | the naming register
enacted_path  module_visualisation/generate.py | 21 | the generator
enacted_path  module_visualisation/visualisation_config.json | 21 | the whole configuration surface
enacted_path  module_visualisation/files_and_folders_visualisation_template.html | 20 | the rendering shell
enacted_path  module_monitoring/files_and_folders_visualisation.html | 20 | the generated page
enacted_path  module_monitoring/data_status.json | 13 | the data module's snapshot
enacted_path  module_monitoring/ml_status.json | 13 | the ml module's snapshot
enacted_path  module_monitoring/data.js | 13 | the data half of the dashboard
enacted_path  module_monitoring/ml.js | 13 | the ml half of the dashboard
enacted_path  .github/workflows/visualisation.yml | 16 | the one workflow
enacted_path  store_assets_artifacts/EXAMPLE_TICKER_README.md | 15 | the store guide sorts inside the ticker block
enacted_path  <TICKER>_README.md | 14 | every asset folder describes itself
enacted_path  <TICKER>_parameters.json | 10 | one parameters file per asset
enacted_path  <TICKER>_config.json | 30 | the asset's registration in its folder

enacted_family  module_skills/ | .md | act_ methodology_ skill_ glossary.md | 7 | guidance files carry their category first

ticker_store  store_assets_artifacts/ | 8 | every per-asset file carries the <TICKER>_ prefix
ticker_tracked_file  <TICKER>_README.md | 14 | whitelisted by .gitignore
ticker_tracked_file  <TICKER>_parameters.json | 10 | whitelisted by .gitignore
ticker_tracked_file  <TICKER>_config.json | 30 | whitelisted by .gitignore
ticker_registry_file  <TICKER>_config.json | 30 | the basket list and the registered folders must agree, both ways

make_lifecycle_target  all | 13 | lifecycle
make_lifecycle_target  help | 13 | lifecycle
make_lifecycle_target  setup | 13 | lifecycle
make_lifecycle_target  conventions-check | 7 | repo-wide, not a module stage
make_lifecycle_target  docker-build | 13 | compose lifecycle
make_lifecycle_target  docker-up | 13 | compose lifecycle
make_lifecycle_target  docker-down | 13 | compose lifecycle
make_stage_prefix  data- | 13 | a stage carries its module
make_stage_prefix  ml- | 13 | a stage carries its module
make_stage_prefix  monitoring- | 22 | a stage carries its module
make_stage_prefix  visualisation- | 19 | a stage carries its module
make_stage_prefix  docker-data- | 13 | the container twin carries its module
make_stage_prefix  docker-ml- | 13 | the container twin carries its module

debt_marker  TODO | 24 | main is clean working logic; a marker is a decision postponed in public
debt_marker  FIXME | 24 | main is clean working logic
debt_marker  XXX | 24 | main is clean working logic
debt_marker  HACK | 24 | main is clean working logic

generated_path  module_monitoring/files_and_folders_visualisation.html | 20 | it embeds every tracked path, so counting it as a source would make reachability vacuous

reachability_rule  python_import | 1 | a module is named by its import path, not by its file name
reachability_rule  ticker_placeholder | 14 | a per-asset file is named by the <TICKER> placeholder, never ten times over
reachability_glob  skill_*.md | 7 | AGENTS.md names the guidance family by its glob, which is that family's own grammar
reachability_ecosystem_owned  .dockerignore | 16 | docker build finds it by the fixed name; no tracked file has to mention it
reachability_ignored_region  module_visualisation/visualisation_config.json | exclude | 20 | naming a path in `exclude` keeps it OUT of the picture, which is the opposite of a reference

# Rejected forms this act states in prose. Nothing here is checked; it is listed
# so the gap is visible, and counted on every run.
unenforceable  project-cased variants | 6 | a casing family is not a token list; the `Lean names` one-liner binds the tree spelling instead
unenforceable  project-cased variants | 16 | same, for the ecosystem-fixed names
unenforceable  bare topic names | 7 | enacted_family checks the positive rule instead
unenforceable  a store spelling its timeframe in sorting slots | 4 | the rejected form is a shape, not a token
unenforceable  any per-asset file that needs its folder to say which asset it belongs to | 8 | ticker_manifest checks the positive prefix rule instead
unenforceable  a per-asset OHLCV parquet | 9 | every candidate is gitignored, so no tracked name can carry it
unenforceable  a parameters file per stage | 10 | ticker_manifest bounds the folder instead
unenforceable  a strategy file per asset | 10 | ticker_manifest bounds the folder instead
unenforceable  a bare plural, an adjective holding a number | 11 | the `count keys` one-liner covers the published keys; identifiers are unbounded
unenforceable  reading order, artifact-responsibility order | 12 | an ordering claim about four documents, not a name
unenforceable  a second copy of the chain in README or a methodology | 17 | prose duplication is not a token
unenforceable  a page generator folded into module_monitoring/ | 18 | a placement judgement, not a name
unenforceable  a width breakpoint or a touch-only gesture | 29 | the ban covers the vocabulary, not the CSS pattern: `@media (max-width:...)` contains none of the banned words
unenforceable  established terminology over local coinages | 25 | no closed list of coinages exists, so no grep can settle it
unenforceable  a schema with no reader | 30 | no grep can tell an unread key from a read one; a key enters with the stage that reads it
unenforceable  rule-derived structure over repeated project knowledge | 23 | the rule forbids no specific name, so no grep can settle it; it is a preference this repository states, not a grammar it checks
```
