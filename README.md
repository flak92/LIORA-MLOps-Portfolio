# LIORA — 1m Crypto Research Pipeline

**Deterministic multi-venue OHLCV research pipeline with purged walk-forward
validation, a frozen final out-of-sample holdout, and a static results dashboard
— one `make all`.**

Public market observations → QuantConnect Lean-compatible raw data → one
deterministic canonical series per asset, a partition of a Parquet table family →
the feature catalogue and labels → purged walk-forward XGBoost → research strategy
simulation → monitoring.

The repository demonstrates a mathematically correct evaluation process and the serpentine
search, which looks for a better search state of an asset — its feature set, its barrier geometry and its
hyper-parameters — under an explicit objective. Success is the correctness of the calculations, the
comparisons and the search's decisions; a positive trading result is not a condition of acceptance, and
a search that accepts no candidate can be a correct result.

The contract every change answers to is [AGENTS.md](AGENTS.md). Each module carries its orientation in
`README_module_<name>.md` and its rules in its `skills/`; the rules that cross modules and the name register
are [module_skills/](module_skills/), indexed by [module_skills/README.md](module_skills/README.md). This
README is the general overview.

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

The host needs `git`, `docker`, `make` and Python 3 — standard library only, for `record.py`, the terminals and
the canon's tools; `tmux` for the detached search, gum 2 for the terminals, and, for `make skills-crawl` alone, the
one active command line of `module_skills/sub_module_scalability_crawler/vendors_for_crawling.toml`, installed and
logged in. The one image carries four direct dependencies — `duckdb`, `numpy`, `optuna` and `xgboost-cpu` — and
`module_monitoring` is standard library only.

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

A search is one experiment (`SERPENTINE-SEARCH-ONE-SEARCH-IS-ONE-EXPERIMENT`): after a change of anything the
chain reads, in this order:

```bash
make all ASSET=BTC                               # the dependent artifacts, computed again
make features-serpentine-search-reset ASSET=BTC  # the search's own files go; its inputs and profile stay
make features-serpentine-search ASSET=BTC        # a new search
```

A search proposes one search state at most, its champion, or nothing, which is a correct result. A hand promotes a
proposal, one asset at a time, and the ML chain tunes the promoted search state again, its study starting from the
proposal's point (`SERPENTINE-SEARCH-PROMOTION-IS-A-HAND`):

```bash
make features-serpentine-search-promote ASSET=BTC   # the proposal's search state into BTC_feature_set.json, BTC_barriers.json and BTC_hyperparameter_point.json, then ml-all for BTC
```

The canon, outside the chain, on the host — every rule a row of one workbook, `module_skills/skills_sheet.xlsx`,
edited with any spreadsheet program:

```bash
make skills-sync           # render every skill_*.md and module_skills/skill_glossary.md from the sheet
make skills-configurables  # the table of every CONFIGURABLES record in the controlled config.py files, on stdout
make skills-crawl          # after the sync, every controlled file of the sheet's files matrix read against the Skills marked for it by the active vendor — up to 30 min a file; Ctrl-C ends it, the reports already written stay
```

One page behind `make on`, for one reader: the status page at `http://127.0.0.1:<port>/`, the address
`make on` prints — *Pipeline*, *Data Quality*, *Features*, *ML Research*, *ML Assets*, *Scalability* and
*Lifecycle* (§ Dashboard below). It is reachable on loopback alone; on a remote machine tunnel with
`ssh -N -L 8900:127.0.0.1:<port> <host>`, `<port>` the one `make on` printed there.

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
                           decision timeframe middle timeframe    top timeframe
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

Providers deliver observations; the canonical series defines the research object. Everything below it describes
the method, not the data provider.

## The chain

`data-all → features-all → ml-all`, each stage a one-off container of its module's runner, once per asset of
`TICKERS` for a per-asset stage and once for the whole basket for the download and the three status stages;
`ASSET=<TICKER>` narrows a per-asset stage to one asset, and `JOBS=n` runs n assets side by side. The stage order
is the Makefile's `all:`, `data-all:`, `features-all:` and `ml-all:`, and `make help` names every target. The
stores, their variables and what each family and file holds are the register's, `module_skills/skill_glossary.md`
§ Stores and § Artifacts.

## Extending

| to add | change | where |
|---|---|---|
| an asset | one ticker in `TICKERS`; every stage is told its assets by `--tickers` | the `Makefile`; nothing changes in any module |
| a stage of a module | the stage in its module and one `<module>-<stage>` target — a `fanout` or a `basket` line — and its name in `RECORDED_STAGES` if a run should record it | `module_<domain>/`, then the `Makefile` |
| a timeframe | one token in `HIERARCHY_TIMEFRAMES` of `module_features/config.py` — another experiment: the chain runs again, and a recorded search after its reset | `module_features/` |
| a feature | one record of `FEATURE_CATALOGUE` (`module_features/README_module_features.md` § Extending) | `module_features/` |
| a search axis of the serpentine search | its search families in `ROUND_SCHEDULE`, its moves in an `axis_<search_axis>.py` like `axis_barrier.py` and `axis_feature_set.py`, its grid in the profile | `module_features/sub_module_serpentine_search/` |
| a venue | `download_<venue>.py` beside its sibling and the failover order in `ingest.py` (`module_data/README_module_data.md`) | `module_data/` |
| a module | a package `module_<domain>/` with a runner service on the one image | `module_<domain>/` beside the others |

## Parity

Every number here is reproducible. The proof, repeatable on any host (`AGENTS.md` D11):

1. a fresh `git clone` of this repository, and a frozen copy of the raw store copied into `store/raw_1m/` — the
   downloaders never overwrite an existing ZIP — its manifest taken **before** the chain runs:
   `(cd store/raw_1m && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) | sha256sum`;
2. `make all-record` — the whole chain, the download included;
3. every other file of `store/assets_artifacts/` and `store/trials/` byte-identical to the reference manifest, and
   the tracked files of the asset's folder unmoved;
4. the three computational snapshots identical after dropping the `generated_at_utc` line —
   `grep -v '^ "generated_at_utc":'` — `data_status.json` apart when the download added a day, since it describes
   the whole canonical series.

Both sides run in containers from the same pins; the seeds, the thread caps at one, sequential Optuna and DuckDB's
pinned orders make the bytes equal (`module_skills/skill_determinism.md`). The reference manifest lives outside this
repository.

## The basket

One uniform market — USDT-margined perpetual futures. The active basket is a single asset, `BTC`, which carries
the whole path end to end; the basket grows by extending `TICKERS` in the `Makefile`, and no module changes. The
data window starts at **2021-01-01 00:00 UTC** and ends at the most recent UTC midnight; every asset is listed on
Binance USDS-M before the data window's start, and where a Bybit listing falls inside it the pre-listing minutes
are Binance-only in the canonical series, which covers the same full minute grid
(`module_data/skills/skill_candle_canonicalisation.md`).

## Architectural direction

LIORA is an academic, local MLOps research system, not an AWS deployment. Its module, storage and container
boundaries are drawn as a Pre-AWS architecture on purpose: every local implementation is the smallest that works —
Parquet table families partitioned by asset with DuckDB the engine and no database file, JSON in the asset's
folder, one image, a Makefile — and the responsibilities are cut so that a later move onto standard cloud
primitives (an object store, a container runtime, a stage orchestrator) would replace the local storage, the local
Docker execution and the local stage order without redrawing the domain pipeline. No cloud infrastructure exists
here and none is planned. The rules are
[module_skills/skill_pre_aws_solution.md](module_skills/skill_pre_aws_solution.md); the classes, the seats, the
mapping table and what the shape holds are [module_skills/README.md](module_skills/README.md) § The Pre-AWS
mapping, and the skills its seats imply are `AGENTS.md` § Skills absent here, described.

## Dashboard

- **Pipeline** — canonical rows, real-data share and forward-filled bars per asset, its observation lag and
  measurement age, each warned past the download cadence;
- **Data Quality** — raw-source coverage, gaps, duplicates, OHLC violations and zero-volume bars per provider,
  then canonical construction: source shares, switches, the largest 1m move at a switch, cross-source divergence;
- **Features** — the serpentine search of every asset as the feature layer last wrote it, read against the ML
  snapshot's numbers for the asset's own search state, then each asset's PROPOSALS and the feature module's
  CONFIGURABLES;
- **ML Research** — the cross-section of every asset's result, the feature catalogue — every definition the
  repository computes, its terms, the history each covers on each timeframe, the warm-up it needs and the nesting
  of the timeframes — and the ML module's CONFIGURABLES;
- **ML Assets** — the cross-section by view — labels and data, classification, strategy, HPO, feature set — then
  one asset at a time in four frames: LABEL, MODEL, STRATEGY, FEATURE SET;
- **Scalability** — every controlled file of the crawler's files matrix, with its state, its vendor, when it
  finished and its current report;
- **Lifecycle** — one recorded run end to end, measured from outside by `record.py`: for every stage its start,
  its time, its exit code and what it added, changed and removed in the three pipeline stores, then every file it
  touched, by store and path.

## ML research layer

`module_features/` builds, per asset and deterministically, the feature catalogue from the canonical series —
every definition on the timeframes of the register, each column named by `feature_id()` off its terms
(`module_features/skills/skill_feature_taxonomy.md`) — and writes the contract, `<TICKER>_catalogue.json`, that
names them to the next layer. `module_ml/` takes the asset's feature set as X, triple-barrier labels resolved on
the canonical 1-minute path, a purged walk-forward protocol with average-uniqueness weights and an Optuna search
over XGBoost, a final out-of-sample fold that selects nothing, and a top-down gated strategy with explicit costs,
whose trades leave at their own take-profit and stop while the label they learned from stays symmetric.

Beside the chain, the serpentine search moves the asset's feature set, its barrier geometry and its
hyper-parameters one family at a time, on the three validation folds alone: a move is kept only where its CAGR
beats its parent's on every fold, the beam is ranked by the CAGR of the folds chained into one walk-forward path,
and the champion is proposed only when it beats the start by more than the noise of the whole search — a
heuristic, not a guarantee. The method is `module_features/skills/methodology_features.md` § The serpentine search
and `module_ml/skills/methodology_ml.md`.
