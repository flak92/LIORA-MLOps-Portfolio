# LIORA — 1m Crypto Research Pipeline

**Deterministic multi-venue OHLCV research pipeline with purged walk-forward
validation, a frozen final out-of-sample holdout, and a static results dashboard
— one `make all`.**

*The repository shows the destination, not the road*.

Public market observations → QuantConnect Lean-compatible raw data → one
deterministic canonical series per asset, a partition of a Parquet table family →
the feature catalogue and labels → purged walk-forward XGBoost → research strategy
simulation → monitoring.

The repository demonstrates a mathematically correct evaluation process and the serpentine
algorithm, which searches for better feature configurations under an explicit objective
function. Success is the correctness of the calculations, the comparisons and the algorithm's
decisions. A positive trading result is not a condition of acceptance: a move from a CAGR of
−12% to −8% improves the objective, and a search that accepts no candidate can be a correct
result.

The four modules of the chain sit at the root beside what none of them owns: the
Makefile and the compose file that run them, the recorder, the five stores, one folder each under `store/`, and
the canon of rules that cross them — one workbook every rule is a row of — with the crawler that reads each controlled file against the Skills marked for it. The governing contract — minimalism, minimum requirements,
KISS/YAGNI/DRY/SOLID, UCAS, pipeline-first, and what holds the project
together — is [AGENTS.md](AGENTS.md). Each module carries its own rules in its
`skills/` and its front door in `README_module_<name>.md`; the naming register
and the rules that cross modules are in [module_skills/](module_skills/), indexed
by [module_skills/README.md](module_skills/README.md). The working path through
the project is `AGENTS.md → module names → README_module_<name>.md → the
module's own skills → code`; this README is the general overview.

## Quickstart

```bash
git clone https://github.com/flak92/LIORA-MLOps-Portfolio.git
cd LIORA-MLOps-Portfolio
make all                   # the whole chain from a fresh clone, every stage in a one-off container: build -> data-all -> features-all -> ml-all
make on                    # build the image if needed, start the dashboard, print the page's address and open it
make off                   # stop and remove every container of this project
make help                  # every action target with its one-line purpose
```

Each module's terminal is an entry, not an action, so it carries no line in `make help`:

```bash
make data-terminal         # the data module's stages over each asset's raw days and canonical series
make features-terminal     # the feature module's stages and the serpentine search: draft, read, promote
make ml-terminal           # the ML module's stages and the scoring of a request
make monitoring-terminal   # the four snapshots, then the presentation switch
make skills-terminal       # the canon: the sheet and the crawl's state, then one of the canon's tools
```

`git`, `docker`, `make` and Python 3 — standard library only, for `record.py`, the terminals, the canon's
tools and the opener `make on` prints through — are the whole requirement of the host; `tmux` joins them for the
detached search, gum 2 for the terminals' text-based user interface (TUI), and, for `make skills-crawl` alone, the one
active command line of `module_skills/sub_module_scalability_crawler/vendors_for_crawling.toml`, installed and logged
in.
Everything runs through the Makefile. `on` and `off` are the presentation switch,
the one switch pair the target grammar admits ([AGENTS.md](AGENTS.md) § Canonical
vocabulary): two words for a presenter to remember.

The chain, and the record it leaves:

```bash
make all-record            # the same chain, every stage measured from outside by record.py into store/run_records/<run_id>/ — the Lifecycle tab
```

The serpentine search, outside the chain, one asset at a time:

```bash
make features-serpentine-search ASSET=BTC        # a turn, then ml-score and a turn while the turn leaves a question; resumes where the files stand
make tmux-features-serpentine-search ASSET=BTC   # the same search detached in tmux session features-serpentine-search-btc; it outlives the terminal and ends with the search
tmux attach -t features-serpentine-search-btc     # watch it; Ctrl-C stops it, a rerun resumes
make features-status                             # the search into the snapshot — the page reads nothing else
```

A search is one experiment, and what a change asks of it is one rule,
`SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT` — after a change of anything the chain reads, in
this order:

```bash
make all ASSET=BTC                               # the dependent artifacts, computed again
make features-serpentine-search-reset ASSET=BTC  # the search's own files go — its state, ledger, question, answer and score_trials partition; its inputs and profile stay
make features-serpentine-search ASSET=BTC        # a new search
```

A search proposes one state at most, its champion. A search that finds nothing better than where it
started proposes nothing, and that is a correct result — the promotion then refuses in one line.
When it proposes, a hand promotes the proposal — one asset at a time — and the ML chain tunes the
promoted state again, so the result that counts is the rerun's on the validation folds:

```bash
make features-serpentine-search-promote ASSET=BTC   # the proposal's columns into BTC_feature_set.json and its barrier geometry into BTC_barriers.json, then ml-all for BTC
```

The canon, outside the chain, on the host — every rule a row of one workbook, `module_skills/skills_sheet.xlsx`,
edited with any spreadsheet program:

```bash
make skills-sync           # render every skill_*.md and module_skills/skill_glossary.md from the sheet
make skills-configurables  # the table of every CONFIGURABLES record in the controlled config.py files, on stdout
make skills-crawl          # after the sync, every controlled file of the sheet's files matrix read against the Skills marked for it by the active vendor — up to 30 min a file; Ctrl-C ends it, the reports already written stay
```

The crawl writes one report per file under `store/status/reports_after_crawled_files/`, untracked, and
`store/status/skills_status.json`, which the Scalability tab reads; its vendors and its mission are
`vendors_for_crawling.toml` and `crawlers_mission.md` in `module_skills/sub_module_scalability_crawler/`, kept by hand.

`tmux` is a tool of the host beside `docker` and `git`, never of an image.

One page behind `make on`, for one reader: the status page at `http://127.0.0.1:<port>/`, the address
`make on` prints — *Pipeline*, *Data Quality*, *Features*, *ML Research*, *ML Assets*, *Scalability* and
*Lifecycle*: the results, the serpentine search, the tree counted against its contract and the cost of producing
them (§ Dashboard below).

A single stage runs by name in a one-off container of its module's runner — `make features-catalogue`
is `docker compose run --rm -T features python -m module_features.catalogue --tickers <TICKER>`, one container per asset of the
basket — and `data-all`, `features-all`, `ml-all` and `all` are the chains. The stage order is the
Makefile's `all:`, `data-all:`, `features-all:` and `ml-all:`; every document points there. The host port is measured
at invocation — the port the dashboard already publishes, else the first free port from 8900 upward
(`ASSET-CONTAINERS-THE-HOST-PORT-IS-MEASURED`) — and `PORT=8902 make on` overrides
it; `JOBS=2 make ml-hpo` sets the fan-out width, and every stage is idempotent in what it
derives, so a rerun fetches and rebuilds only what its contract says — the `hpo_trials`
ledger alone grows, one study more per `ml-hpo`, and beside the chain the crawler's reports
are reset and written again by every crawl. The dashboard is
docker-only and reachable on loopback alone; on a remote machine tunnel with
`ssh -N -L 8900:127.0.0.1:<port> <host>`, `<port>` the one `make on` printed there.
Four direct dependencies across
the four modules and nothing else — `duckdb` (the engine that writes and reads the Parquet families: data, features, ml),
`numpy` (mathematics: features, ml), `optuna` (hyper-parameter search: ml) and `xgboost-cpu`
(model: ml); `module_monitoring` is standard library only. The CPU wheel is deliberate, because the research layer trains with `tree_method=hist` and `nthread=1`.

```
                 ┌── market source A ──┐
MARKET DATA ─────┤                     ├──► NORMALISED RAW 1m OHLCV  (Lean ZIPs)
                 └── market source B ──┘              │
                                                      ▼
                                ONE CANONICAL PARTITION PER ASSET
                                       (primary-failover, full grid)
                                                      │
                                    ┌─────────────────┼─────────────────┐
                                    ▼                 ▼                 ▼
                               decision tf        middle tf          top tf
                                    └─────────────────┬─────────────────┘
                                                      ▼
                                                  FEATURES X
                                                      │
                   canonical 1m ───────────────────── ┼──► TRIPLE BARRIER Y
                                                      ▼
                                            PURGED WALK-FORWARD
                                                      ▼
                                                   XGBOOST
                                                      ▼
                                                PROBABILITIES
                                                      ▼
                                               STRATEGY RULES
                                                      ▼
                                            RESEARCH PnL / EQUITY
                                                      ▼
                                                  MONITORING
```

Providers deliver observations; the canonical series defines the research
object. Everything below it describes the method, not the data provider.

## The stores

| store | variable | in a container | tracked |
|---|---|---|---|
| `store/raw_1m/` | `STORE_RAW_1M_DIR` | `/store/raw_1m` | no — the Lean-exact raw ZIPs, one per venue, symbol and UTC day |
| `store/assets_artifacts/` | `STORE_ASSETS_ARTIFACTS_DIR` | `/store/assets_artifacts` | the remnant only, in the asset's folder `ticker=<TICKER>/`: `<TICKER>_README.md`, `<TICKER>_parameters.json`, `<TICKER>_serpentine_search_profile.json` once drafted, the serpentine search's state `<TICKER>_serpentine_search.json` and its ledger `<TICKER>_serpentine_search_trials.jsonl` once a search has run, and `<TICKER>_feature_set.json` and `<TICKER>_barriers.json` once promoted |
| `store/run_records/` | `STORE_RUN_RECORDS_DIR` | `/store/run_records` | no |
| `store/trials/` | `STORE_TRIALS_DIR` | `/store/trials` | no — two ledger families, one JSON object a line, appended and never rewritten |
| `store/status/` | `STORE_STATUS_DIR` | `/store/status` | yes — the four snapshots, so a fresh clone opens on real numbers |

A table is a family of Parquet files partitioned by asset and, where the register decides the values, by
timeframe — `<store>/<family>/ticker=<TICKER>/[timeframe=<timeframe>/]<family>.parquet`, Hive's `key=value` — and every
writer of a family writes the family's `schema.json` beside its partitions. The asset's folder
`ticker=<TICKER>/` holds its non-tabular files, one file per artifact, named for it. DuckDB is the engine, in memory,
and no database file exists. One stage writes each family and each file:

| what | path under its store | written by | tracked |
|---|---|---|---|
| the raw days | `cryptofuture/{binance,bybit}/minute/<symbol>/<YYYYMMDD>_trade.zip` | `data-download` | no |
| the venue families | `ohlcv_1m_{binance,bybit}/ticker=<TICKER>/ohlcv_1m_<venue>.parquet` | `data-ingest` | no |
| the canonical family | `ohlcv_1m_canonical/ticker=<TICKER>/ohlcv_1m_canonical.parquet` | `data-ingest` | no |
| `bars` | `bars/ticker=<TICKER>/timeframe=<timeframe>/bars.parquet`, every timeframe of the register | `features-bars` | no |
| `catalogue` | `catalogue/ticker=<TICKER>/timeframe=<timeframe>/catalogue.parquet`, every timeframe of the register | `features-catalogue` | no |
| `labels` | `labels/ticker=<TICKER>/timeframe=<timeframe>/labels.parquet`, the decision timeframe | `ml-labels` | no |
| `oos_predictions` | `oos_predictions/ticker=<TICKER>/timeframe=<timeframe>/oos_predictions.parquet`, the decision timeframe | `ml-train` | no |
| the contract | `ticker=<TICKER>/<TICKER>_catalogue.json` | `features-catalogue` | no |
| the parameters | `ticker=<TICKER>/<TICKER>_parameters.json` | `ml-hpo` | yes |
| the evaluations | `ticker=<TICKER>/<TICKER>_model_evaluation.json`, `<TICKER>_strategy_evaluation.json` | `ml-train`, `ml-strategy` | no |
| the asset's README | `ticker=<TICKER>/<TICKER>_README.md` | `ml-status` | yes |
| the search's profile | `ticker=<TICKER>/<TICKER>_serpentine_search_profile.json` | a hand, or the feature terminal's draft | yes |
| the search's state and ledger | `ticker=<TICKER>/<TICKER>_serpentine_search.json`, `<TICKER>_serpentine_search_trials.jsonl` | `features-serpentine-turn` | yes |
| the question | `ticker=<TICKER>/<TICKER>_score_request.json` | `features-serpentine-turn` | no |
| the answer | `ticker=<TICKER>/<TICKER>_score_response.json` | `ml-score` | no |
| the promotion | `ticker=<TICKER>/<TICKER>_feature_set.json`, `<TICKER>_barriers.json` | `features-serpentine-search-promote` | yes, once promoted |
| `hpo_trials` | `hpo_trials/ticker=<TICKER>/hpo_trials.jsonl`, every point `ml-hpo` drew | `ml-hpo` alone | no |
| `score_trials` | `score_trials/ticker=<TICKER>/score_trials.jsonl`, every point the studies a question asks for drew | `ml-score` alone | no |
| the snapshots | `{data,features,ml}_status.json` | the status stages | yes |
| the crawl's snapshot | `skills_status.json` | `skills-crawl` | yes |
| the run records | `<run_id>/<stage>.json` | `record.py` | no |

A ledger carries no run id, no timestamp and no host name, so two studies over an empty store leave the same bytes. A
study's place in its ledger is read off the ledger before its lines are appended, so a partition has one writer at a
time; the fan-out needs nothing more, because its processes write different assets' partitions. The search's own
ledger lies beside its state in the asset's folder and is tracked; the two families of `store/trials/` are not, and
only grow until a hand clears them — `make features-serpentine-search-reset` clears the asset's partition of
`score_trials` with the rest of its search.

The store is the boundary between compute and state (`module_skills/skill_glossary.md`
§ Stores). Every stage reads and writes only these five and learns where they
are from its environment — the Makefile exports the host paths, the compose file
sets the container paths — and no module writes into another's tree. The image
carries the pins and nothing else; the code and the state arrive as mounts, and
a container addresses a store only at `/store/<content>`.

## The chain

`data-all → features-all → ml-all`, each `<module>-<stage>` a one-off container of
its module's runner, `docker compose run --rm -T <runner> python -m <module>.<stage> --tickers <TICKER>`
— the `fanout` macro once per asset of `TICKERS`, `JOBS` wide, the `basket` macro
once for the whole basket (the three status stages and the download). `ASSET=<TICKER>`
on the make line narrows every per-asset stage to one asset and never a
basket-wide one; `make all-record` wraps every stage of `RECORDED_STAGES` in
`record.py`, which lists the four pipeline stores — every store but
`store/trials/`, a search's own account of itself — before and after and writes
`store/run_records/<run_id>/<stage>.json` and the run index `store/run_records/index.json`. The one resident
is `liora-dashboard-1`: the compose project is named
`liora` in the file, so two checkouts of the project on one host share the name —
run one at a time, or set `COMPOSE_PROJECT_NAME`, which the detached search hands
to its tmux session and puts before the session's name.

| Stage     | Command                | Input → Output                                              | Property                          |
|-----------|------------------------|-------------------------------------------------------------|-----------------------------------|
| download  | `make data-download`   | both APIs → `store/raw_1m/.../*_trade.zip`        | idempotent; one file per UTC calendar day; post-listing days complete; one process per venue for the whole basket |
| ingest    | `make data-ingest`     | ZIPs → the venue families `ohlcv_1m_binance`, `ohlcv_1m_bybit` → the canonical family `ohlcv_1m_canonical` (failover), the asset's partition of each | idempotent; deterministic rebuild, one asset at a time |
| status    | `make data-status`     | the three families → stdout + `store/status/data_status.json` | read-only; one sequential process over the basket, each venue measured on its own and the canonical series beside them |
| bars      | `make features-bars`   | the canonical family → the `bars` family, one partition per asset and timeframe of the register | deterministic; the research window only |
| catalogue | `make features-catalogue` | the bars → the `catalogue` family, one partition per asset and timeframe, and `<TICKER>_catalogue.json`, the contract the ML layer reads | deterministic |
| features status | `make features-status` | the catalogue's partitions and each asset's serpentine search → `store/status/features_status.json` | read-only; the catalogue's facts, each asset's row counts and its search as it last wrote itself |
| serpentine search | `make features-serpentine-search ASSET=<TICKER>` | the profile, the catalogue, Y and the parameters → `<TICKER>_serpentine_search.json` and its ledger `<TICKER>_serpentine_search_trials.jsonl` | outside the chain: `make features-serpentine-turn` leaves a question, `<TICKER>_score_request.json`, `make ml-score` answers it on the validation folds, and the loop runs while a question stands; resumes where the files stand; promotes nothing; its detached twin `make tmux-features-serpentine-search ASSET=<TICKER>` outlives the terminal and ends with the search |
| reset | `make features-serpentine-search-reset ASSET=<TICKER>` | the search's state, ledger, question, answer and `score_trials` partition → gone | runs no stage; the inputs and the profile stay — a new experiment starts from the files the chain left |
| promotion | `make features-serpentine-search-promote ASSET=<TICKER>` | the proposal's columns → `<TICKER>_feature_set.json` and its barrier geometry → `<TICKER>_barriers.json`, then `ml-all` for that asset, which tunes it again | a hand's choice, one asset at a time; a search that proposes none refused in one line; the same proposal twice changes nothing; the commit history is the record |
| lifecycle | `make all-record` | one recorded run of the whole chain → `store/run_records/<run_id>/` | one record for the whole basket; every stage measured from outside by `record.py` — its time, its exit code and what it wrote to the four pipeline stores |
| dashboard | `make on`              | the snapshots and the run records → the seven-tab page on `127.0.0.1:<port>`, the address `make on` prints, served by `module_monitoring/serve.py` in the `dashboard` container under three prefixes — the page's own files, `status/` and `run_records/` | no external resources; every other path 404, and no directory listed |

## Extending

| to add | change | where |
|---|---|---|
| an asset | one ticker in `TICKERS`; every stage is told its assets by `--tickers` | this repository; nothing changes in any module |
| a stage of a module | the stage in its module and one `<module>-<stage>` target here — a `fanout` or a `basket` line — and, if a run should record it, its name in `RECORDED_STAGES` | `module_<domain>/`, then here |
| a timeframe | one token in `HIERARCHY_TIMEFRAMES` of `module_features/config.py`, carried to ML by `<TICKER>_catalogue.json` — a different experiment: the chain runs again, and a recorded search after its reset (`SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT`) | `module_features/` |
| a feature | one record of `FEATURE_CATALOGUE` in the same file (`module_features/README_module_features.md` § Extending) | `module_features/` |
| a coordinate of the serpentine search | its family in `ROUND_SCHEDULE` of `module_features/sub_module_serpentine_search/config.py`, its moves in `coordinate_barrier.py` or `coordinate_feature_set.py` beside it, and its grid in the profile (`module_features/README_module_features.md`) | `module_features/` |
| a venue | `download_<venue>.py` beside its sibling and the failover order in `ingest.py` (`module_data/README_module_data.md`) | `module_data/` |
| a module | a package `module_<domain>/` with a runner service on the one image | `module_<domain>/` beside the others, then here |

## Working in a module

A module is a directory: its package, its orientation `README_module_<name>.md`
and its own `skills/`. Edit it in place and run the stage it owns — nothing has
to be built first, because the code is mounted into the container it runs in:

```bash
make ml-all ASSET=BTC        # one module's chain, one asset
make data-status             # a single stage, basket-wide
make help                    # every action target with its one-line purpose
```

`git grep "from module_"` inside a package finds only that package: no module
imports another, and what would cross the boundary as an import crosses it as a
file in a store instead (`AGENTS.md` § Architecture shape).

## Skills

`AGENTS.md` and `module_skills/` are the canon: the contract, the name register and the rules that cross
modules. Every rule of the tree is a row of one workbook, `module_skills/skills_sheet.xlsx` — a `rule_id`, its
description, the files it binds, what conforming looks like and its one exception — and `make skills-sync` renders the
rows into the `skill_*.md` beside what each governs, and the register into `module_skills/skill_glossary.md`; a generated
document is never edited by hand, and a document cites a rule by its `rule_id`. The sheet's files matrix marks which
Skills each controlled file is read against: `make skills-crawl` sends every controlled file with its marked Skills to
the one active vendor and keeps one report per file; it gates nothing
(`module_skills/sub_module_scalability_crawler/README_sub_module_scalability_crawler.md`). How any of this tree's
terminals draws a screen is the canon's too, `module_skills/skill_tui_designer.md`: `make <module>-terminal` opens that
module's terminal over its own targets, and `make skills-terminal` the canon's. A module's own rules live under that
module, in `module_<domain>/skills/` and beside its sub-modules, and the index `module_skills/README.md` links to all of
them. Each rule is written exactly once, where it is owned, and no document restates another (`AGENTS.md` § The default
choice).

## Parity

Every number here is reproducible. The proof, repeatable on any host:

1. a fresh `git clone` of this repository, and a frozen copy of the raw store copied into
   `store/raw_1m/` — the downloaders never overwrite an existing ZIP — its manifest taken **before**
   the chain runs, so the manifest names the store the hashes came out of:
   `(cd store/raw_1m && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) | sha256sum`;
2. `make all-record` — the whole chain, the download included. A day the download adds past the
   frozen copy changes the raw tree, the two venue families, the canonical family and
   `data_status.json` and nothing else, because every later stage reads the research window alone,
   which ends at `RESEARCH_END_UTC`;
3. every other file of `store/assets_artifacts/` and `store/trials/` byte-identical to the
   reference manifest — each family's `schema.json` and the asset's partitions of `bars`,
   `catalogue`, `labels` and `oos_predictions`, the contract `<TICKER>_catalogue.json`, the
   parameters, the model and strategy evaluations, the asset's README and the `hpo_trials`
   ledger — and the tracked files of the asset's folder unmoved;
4. the three computational snapshots identical after dropping the `generated_at_utc` line —
   `grep -v '^ "generated_at_utc":'`, anchored because it is one top-level key on its own
   line and not a substring to be hunted — `data_status.json` apart when the download added a
   day: it carries no `window_end`, describes the whole canonical series, including the minutes
   past `RESEARCH_END_UTC`, and moves with every top-up by design.

The files a hand drafts stand outside this proof — `<TICKER>_serpentine_search_profile.json` and, once
promoted, `<TICKER>_feature_set.json` and `<TICKER>_barriers.json`: no stage of the chain derives them, and
the one program that writes each writes the same bytes for the same decisions. The serpentine search's own
files are outside it too, being a hand's stage rather than the chain's: `<TICKER>_serpentine_search.json`,
where the search stands at a round boundary, `<TICKER>_serpentine_search_trials.jsonl`, its ledger of scored
states — one a line, appended and never rewritten — and the asset's partition of `score_trials`. Their proof
is that a search reset and run again over the same inputs gives the same bytes in all three, and that a
search stopped — Ctrl-C in its tmux session — and run again ends on the same state and ledger; its
`score_trials` partition may then hold a study twice, the lines a stop between a study and its answer
left and the rerun appends again (AGENTS.md D11).
`<TICKER>_README.md` lists the two files a promotion writes and measures neither — listed, not measured,
because their size moves with the hand and not with the chain. The search's state and ledger are tracked
even so: `features_status.json` is inside the proof and reads them, so a clone without them could not
reproduce the snapshot that quotes them.

Both sides run in containers from the same pins; `SEED`, `nthread=1`,
`OMP_NUM_THREADS=1`, sequential Optuna and DuckDB's pinned orders are what make
the bytes equal (`module_skills/skill_determinism.md`). The reference manifest
lives outside this repository.

## One canonical series from two venues

Every market feed has missing minutes. Per minute the highest-priority valid
candle is copied verbatim — traded Binance, traded Bybit, a valid no-trade
candle from either in the same order — and only a minute with no valid candle
on both venues is a canonical gap, forward-filled with the previous close and
zero volume. Downstream code reads one continuous `t,O,H,L,C,V` series whose
every printed price existed on a real market. The rule, the provenance and the
schema:
`module_data/skills/skill_candle_canonicalisation.md`;
the endpoints:
`module_data/skills/methodology_data.md`.

## The basket

One uniform market — USDT-margined perpetual futures. The active basket is a
single asset, `BTC`: one reference asset carries the whole path end to end, and the
basket grows by extending `TICKERS` in the `Makefile` — every stage is told its assets by
`--tickers`, and no module changes.

The window starts at **2021-01-01 00:00 UTC** and ends at the most recent UTC
midnight. Every asset is listed on Binance USDS-M before the window start;
where a Bybit listing falls inside the window, the pre-listing minutes are
Binance-only in the canonical series, which covers the identical full minute
grid.

## Architectural direction

LIORA is an academic, local MLOps research system, not an AWS deployment. Its
module, storage and container boundaries are drawn as a Pre-AWS architecture on
purpose: every local implementation is the smallest that works — Parquet table
families partitioned by asset with DuckDB the engine and no database file, JSON in
the asset's folder, one image for the tree, a Makefile — and the responsibilities are cut so that a later move onto standard
cloud primitives (an object store, a container runtime, a stage orchestrator)
would replace the local storage, the local Docker execution and the local stage
order without redrawing the domain pipeline. No cloud infrastructure exists here
and none is planned; the mapping is described, not built. Correctness is shown by
the whole chain running end to end on a small representative basket, `BTC`
today, never by production-scale infrastructure: there is no test suite, no
security layer and no guard beyond the seven the mathematics needs (`AGENTS.md`
§ Values). The rules are
[module_skills/skill_pre_aws_solution.md](module_skills/skill_pre_aws_solution.md); the twelve classes, the
seats, the mapping table and what the shape holds are
[module_skills/README.md](module_skills/README.md) § The Pre-AWS mapping.

That section seats the four things a move would name first — the host and the
volume where every asset's folder and the other `store/<content>/` folders live, the
one-off task and the state machine over the stages, the table families
partitioned by asset, and the strategy host that is absent; `AGENTS.md` § Skills absent here,
described lists the skills those seats imply, each with its owner, what it
would govern and the one condition under which it is written. The local skills'
seats stand there too, one paragraph each, naming the primitive their object answers to.

## Data formats

Raw ZIPs are the Lean `cryptofuture` minute format, one tree per venue,
headerless `offset_ms_from_utc_midnight,open,high,low,close,volume`; timestamps
are bar-open UTC epoch milliseconds on a strict 60 000 ms grid, volume is
base-asset volume. The canonical series lives only in the family
`ohlcv_1m_canonical`, one partition per asset, and its aggregations on the timeframes of
the register only in the family `bars`, one partition per asset and timeframe; the
`catalogue` family's partitions are feature columns, not prices. For Lean backtests use
the raw ZIP trees. Every family carries its columns and their types in its own
`schema.json`, beside its partitions; the canonical series' rule and provenance:
`module_data/skills/skill_candle_canonicalisation.md`.

## Dashboard

- **Pipeline** — canonical rows, real-data share and forward-filled bars per asset,
  its observation lag and measurement age, each warned past the download cadence;
- **Data Quality** — raw-source coverage, gaps, duplicates, OHLC violations and
  zero-volume bars per provider, then canonical construction: source shares,
  switches, the largest 1m move at a switch, cross-source divergence;
- **Features** — the serpentine search of every asset as the feature layer last wrote it, read against the ML
  snapshot's numbers for the asset's own state, then each asset's PROPOSALS and the feature module's
  CONFIGURABLES;
- **ML Research** — the cross-section of every asset's result, the feature
  catalogue — every definition the repository computes, its terms, the history
  each covers on each timeframe, the warm-up it needs and the nesting of the levels —
  and the ML module's CONFIGURABLES;
- **ML Assets** — the cross-section by view — labels and data, classification, strategy, HPO, feature set — then
  one asset at a time in four frames: LABEL, MODEL, STRATEGY, FEATURE SET;
- **Scalability** — every controlled file of the crawler's files matrix, with its state, its vendor, when it
  finished and its current report;
- **Lifecycle** — one recorded run end to end, measured from outside by `record.py`:
  for every stage its start, its time, its exit code and what it added, changed and
  removed in the four pipeline stores, then every file it touched, by store and path. Nothing
  a stage says about itself enters the record.

## ML research layer

`module_features/` builds, per asset and deterministically, the feature
catalogue from the canonical series — twenty-one feature definitions on the
timeframes of the register, sixty-one columns, each named by `feature_id()` off its
terms (`module_features/skills/skill_feature_taxonomy.md`) — and writes the contract,
`<TICKER>_catalogue.json`, that names them to the next layer; `module_ml/` takes the
fifteen columns of the default set as X until a promotion, triple-barrier labels
resolved on the canonical 1-minute path, a purged walk-forward protocol with
average-uniqueness weights and an Optuna search over XGBoost, a final out-of-sample
fold that selects nothing, and a top-down gated strategy with explicit costs, whose
trades leave at their own take-profit and stop while the label they learned from
stays symmetric. The decision is taken at the close of a bar of `DECISION_TIMEFRAME`
and entered at the next minute's open.

Beside the chain, the serpentine search of `module_features/` moves the asset's feature
set, its barrier geometry and its hyper-parameters one family at a time, on the three
validation folds only. It ranks a state by the CAGR of those folds chained into one
walk-forward path, then by its Calmar ratio, then by its profit factor, and keeps a
move only when the child's path CAGR beats its parent's by more than the noise of the
pass and its Calmar ratio beats its parent's on every fold. It proposes its champion
only when the champion beats the state it started from by more than the noise of the
whole search; a search that proposes nothing has still answered. A promotion copies the
proposal and reruns the ML chain, which tunes it again. The gate is a heuristic, not a
guarantee: `module_features/skills/methodology_features.md`.

Every per-asset stage runs `JOBS` assets side by side, one by default, one process
each, thread caps at one. Every asset folder describes itself in `<TICKER>_README.md`.
Full methodology: `module_ml/skills/methodology_ml.md`.
