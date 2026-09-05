# LIORA — 1m Crypto Research Pipeline

**Deterministic multi-venue OHLCV research pipeline with purged walk-forward
validation, a frozen final out-of-sample holdout, and a static results dashboard.**

*The repository shows the destination, not the road*.

Public market observations → QuantConnect Lean-compatible raw data → one
deterministic canonical DuckDB per asset → the feature catalogue and labels →
purged walk-forward XGBoost → research strategy simulation → monitoring.

The governing contract — minimalism, minimum requirements, KISS/YAGNI/DRY/SOLID,
UCAS, pipeline-first — lives in [AGENTS.md](AGENTS.md). Each module carries its
own rules in its `skills/` and its front door in `README_module_<name>.md`; the
naming register and the rules that cross modules are in
[module_skills/](module_skills/), indexed by
[module_skills/README.md](module_skills/README.md).
The working path through the repo is `AGENTS.md → module names →
README_module_<name>.md → the module's own skills → code`; this README is the
general overview.

## Quickstart

Everything runs through the Makefile; `make help` lists every target with its
one-line purpose. On and off — one word each, the presentation switch; from
there everything is a click in the page:

```bash
make on                    # build the image, start the dashboard, the DevOps panel and the asset containers, print the page's address and open it  (= make docker-up)
make off                   # stop and remove every container of this project  (= make docker-down)
```

`on` and `off` are the one alias pair the target grammar admits ([AGENTS.md](AGENTS.md)
§ Canonical vocabulary): two words for a presenter to remember; the targets they
name are the convention.

The chain, and the pictures it leaves:

```bash
make all                   # the whole pipeline on the host from a fresh clone: setup -> data-download -> data-ingest -> data-status -> features-all -> ml-all
make docker-all            # the same chain inside the containers, download to snapshots
make docker-all-record     # the same chain, recorded stage by stage into store_run_records/<run_id>/ — the Lifecycle tab
make monitoring-dx-update  # redraw the developer-experience drawing after the tracked tree changes
```

The feature-set search, outside the chain, one asset at a time:

```bash
make tmux-ml-feature-set-search ASSET=BTC   # the search detached in tmux session feature-set-btc; it outlives the terminal and ends with the search, resumes if rerun
tmux attach -t feature-set-btc              # watch it; Ctrl-C stops it
make ml-status                              # the finished search's proposals into the snapshot — the page reads nothing else
```

Its proposals are the *Feature set* view and the PROPOSALS frame of *ML
Assets*; a hand promotes one — one asset at a time — and the chain reruns:

```bash
make ml-feature-set-promote ASSET=BTC PROPOSAL=1   # copy proposal 1's columns into BTC_feature_set.json, then ml-all for BTC
```

`tmux` is a tool of the host beside `docker` and `git`, never of the image.

Three readers, three doors, all behind `make on`:

- **business** — the status page at `http://127.0.0.1:<port>/`, the address
  `make on` prints: *Pipeline*, *Data
  Quality*, *ML Research*, *ML Assets* and *Lifecycle*, the results and the cost
  of producing them (§ Dashboard below);
- **developer** — the **DX** control in the top right opens the drawing of the
  tracked tree, one self-contained page in two views: the tree as tracked, and
  the same tree seated where each part would live or run under § Architectural
  direction;
- **DevOps** — the **DevOps** control opens the panel: the asset containers as
  they report themselves, every container on the host with its ports, the
  networks, volumes, bind mounts, the image and the engine's events, with
  start / stop / restart offered for this project's own containers alone.

A single stage runs by name, on the host or in its container — `make features-catalogue`,
`make docker-features-catalogue`: every `data-<stage>`, `features-<stage>` and `ml-<stage>` target has its
`docker-` twin, and `docker-features-all`, `docker-ml-all` and `docker-all` are the chains. The stage
order is the Makefile's `all:`, `features-all:` and `ml-all:`; every document points there. The host port is measured
at invocation — the port the dashboard already publishes, else the first free port from 8900 upward
(`module_skills/skill_asset_containers.md` § The topology) — and `PORT=8902 make docker-up` overrides
it; `JOBS=2 make ml-hpo` sets the fan-out width, and every stage is idempotent, so
a rerun fetches and rebuilds only what its contract says. The dashboard is
docker-only and reachable on loopback alone; on a remote machine tunnel with
`ssh -L 8900:127.0.0.1:<port> <host>`, `<port>` the one `make on` printed there.
Locally, every fanned-out per-asset stage runs inside
that asset's own resident container, `asset-<ticker>` — one service of
`docker-compose.yml` per ticker of the basket, one image for all — though no stage
depends on it: each is the one-off `python -m <module>.<stage> --tickers <TICKER>`
the container merely hosts. Four direct dependencies and nothing else — `duckdb`
(storage and query), `numpy` (mathematics), `optuna` (hyper-parameter search) and
`xgboost-cpu` (model); the CPU wheel is deliberate, because the research layer
trains with `tree_method=hist` and `nthread=1`.

```
                 ┌── market source A ──┐
MARKET DATA ─────┤                     ├──► NORMALISED RAW 1m OHLCV  (Lean ZIPs)
                 └── market source B ──┘              │
                                                      ▼
                                          ONE DuckDB PER ASSET
                                       (primary-failover, full grid)
                                                      │
                                    ┌─────────────────┼─────────────────┐
                                    ▼                 ▼                 ▼
                                   15m                1h                4h
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

Providers deliver observations; the canonical database defines the research
object. Everything below it describes the method, not the data provider.

## One canonical series from two venues

Every market feed has missing minutes. Per minute the highest-priority valid
candle is copied verbatim — traded Binance, traded Bybit, a valid no-trade
candle from either in the same order — and only a minute with no valid candle
on both venues is a canonical gap, forward-filled with the previous close and
zero volume. Downstream code reads one continuous `t,O,H,L,C,V` series whose
every printed price existed on a real market. The rule, the provenance and the
schema:
[module_data/skills/skill_candle_canonicalisation.md](module_data/skills/skill_candle_canonicalisation.md);
the endpoints:
[module_data/skills/methodology_data.md](module_data/skills/methodology_data.md).

## The basket

One uniform market — USDT-margined perpetual futures. The active basket is a
single asset, `BTC`: one reference asset carries the whole path end to end, and the
basket grows by extending `TICKERS` in `module_data/config.py` and adding one asset
service per ticker under the compose anchor — the execution path itself does not change.

The window starts at **2021-01-01 00:00 UTC** and ends at the most recent UTC
midnight. Every asset is listed on Binance USDS-M before the window start;
where a Bybit listing falls inside the window, the pre-listing minutes are
Binance-only in the canonical series, which covers the identical full minute
grid.

## Architectural direction

LIORA is an academic, local MLOps research system, not an AWS deployment. Its
module, storage and container boundaries are drawn as a Pre-AWS architecture on
purpose: every local implementation is the smallest that works — one DuckDB file
per asset, Parquet and JSON in the asset's folder, one image, a Makefile — and
the responsibilities are cut so that a later move onto standard cloud primitives
(an object store, a container runtime, a stage orchestrator) would replace the
local storage, the local Docker execution and the local stage order without
redrawing the domain pipeline. No cloud infrastructure exists here and none is
planned; the mapping is described, not built. It is also drawn: the deployment
view of the developer-experience drawing, one control on the **DX** page, draws
the primitives of the mapping table as icons with the flows between them, and
seats every tracked file and folder beside the one its responsibility answers
to, or with the documents that deploy nowhere.
Correctness is shown by the whole chain running end to end on a small
representative basket, `BTC` today, never by production-scale infrastructure:
there is no test suite, no security layer and no guard beyond the seven the
mathematics needs (`AGENTS.md` § Values). The rule, its non-goals and the
mapping table:
[module_skills/skill_pre_aws_solution.md](module_skills/skill_pre_aws_solution.md).

The same skill seats the four things a move would name first — the host and the
volume where every asset's folder and the other `store_*` roots live, the
one-off task and the state machine over the stages, the asset's one database
file, and the strategy host that is absent; `AGENTS.md` § Skills absent here,
described lists the skills those seats imply, each with its owner, what it
would govern and the one condition under which it is written. Four local skills
carry one seat paragraph each, naming the primitive their object answers to and
citing that skill for the rest. Whether each seat is the cheapest that keeps its
boundary — what could be less, and whether it is — is
[REPORT_pre_aws_minimalism.md](REPORT_pre_aws_minimalism.md).

## Stages

| Stage     | Command                | Input → Output                                              | Property                          |
|-----------|------------------------|-------------------------------------------------------------|-----------------------------------|
| download  | `make data-download`   | both APIs → `store_raw_1m/.../*_trade.zip`        | idempotent; one file per UTC calendar day; post-listing days complete |
| ingest    | `make data-ingest`     | ZIPs → raw tables → `ohlcv_1m_canonical` (failover)         | idempotent; deterministic rebuild, one asset at a time |
| status    | `make data-status`     | DuckDB → stdout + `module_monitoring/data_status.json`           | read-only; per asset, five scans of its one database, the venue scan run once per venue |
| feature-set search | `make ml-feature-set-search` | the catalogue parquets, Y and the frozen parameters → `<TICKER>_feature_set_search.json` | stepwise on the validation folds only, selected on the model's validation skill fold by fold; resumes; promotes nothing; `make ml-status` after it puts the proposals on the page; its detached twin `make tmux-ml-feature-set-search ASSET=<TICKER>` outlives the terminal and ends with the search |
| promotion | `make ml-feature-set-promote ASSET=<TICKER> PROPOSAL=<n>` | one proposal's columns → `<TICKER>_feature_set.json`, then `ml-all` for that asset | a hand's choice, one asset at a time; the same proposal twice changes nothing; once the file is admitted and committed, the commit history is the record |
| lifecycle | `make docker-all-record` | one recorded run of the whole chain → `store_run_records/<run_id>/` | one record for the whole basket; every stage wrapped by `module_monitoring/record.py`; exact per-stage CPU and peak resident set from `wait4` rusage |
| dashboard | `make docker-up`       | snapshots → five-tab page on `127.0.0.1:<port>`, the address `make docker-up` prints, plus the DX drawing and the DevOps panel behind its two jumps, served by `module_monitoring/serve.py` in the `dashboard` container with the container, run and `/devops` routes | no external resources; the asset containers are reached only through its proxy |
| drawing   | `make monitoring-dx-update` | `git ls-files` → `module_monitoring/sub_module_dx/files_and_folders_visualisation.html` | the tracked tree as one self-contained page, redrawn by hand and by nothing else; opened by the **DX** control of the status page; two views of one tree, development and deployment, flipped by one control on the page |

## Data formats

Raw ZIPs are the Lean `cryptofuture` minute format, one tree per venue,
headerless `offset_ms_from_utc_midnight,open,high,low,close,volume`; timestamps
are bar-open UTC epoch milliseconds on a strict 60 000 ms grid, volume is
base-asset volume. The canonical series and its 15m/1h/4h aggregations live only
in `store_assets_artifacts/<TICKER>/<TICKER>_research_ohlcv.duckdb`; the
folder's parquets are feature columns, not prices. For Lean backtests use the
raw ZIP trees. Schema:
[module_data/skills/skill_candle_canonicalisation.md](module_data/skills/skill_candle_canonicalisation.md)
§ 11 and § 13.

## Dashboard

- **Pipeline** — canonical rows, real-data share and forward-filled bars per asset;
- **Data Quality** — raw-source coverage, gaps, duplicates, OHLC violations and
  zero-volume bars per provider, then canonical construction: source shares,
  switches, the largest 1m move at a switch, cross-source divergence;
- **ML Research** — the cross-section of every asset's result, and the feature
  catalogue: every definition the repository computes, its terms, the history
  each covers on each timeframe, the warm-up it needs and the nesting of the levels;
- **ML Assets** — one asset at a time in five frames: LABEL, MODEL, STRATEGY, FEATURE SET, PROPOSALS;
- **Lifecycle** — one recorded run end to end: what ran, in which container, as
  which PID, for how long, at what CPU and peak resident set, what bytes it moved
  and what it left on disk; then one shared timeline with a dashed rule at every
  stage boundary. A column marked *container* is the whole container over the
  same window; every unmarked number is the stage's own, and the page says so.

Two controls in the top right leave the page, one per persona beyond the
business reader:

- **DX** — the developer-experience drawing of the tracked tree;
- **DevOps** — the panel: one row per asset container, live through the
  dashboard's proxy (up or down, up since, memory against its ceiling, peak, CPU
  share over the last poll, the observation lag and the measurement age, then one
  container as it reports itself), and beside it every container, network and
  volume the daemon reports, with `start` / `stop` / `restart` offered for this
  project's own containers alone.

## ML research layer

`module_features/` builds, per asset and deterministically, the feature
catalogue from the canonical series — eight feature definitions on the
timeframes of the register, twenty-two columns, each name read off its terms
([module_features/skills/skill_feature_taxonomy.md](module_features/skills/skill_feature_taxonomy.md));
`module_ml/` takes the fifteen columns of the default set as X until a promotion,
triple-barrier labels resolved on the canonical 1-minute path, a purged
walk-forward protocol with average-uniqueness weights and an Optuna search over
XGBoost, a final out-of-sample fold that selects nothing, and a top-down gated
strategy with explicit costs. The decision is taken at a 15m close and filled
one minute later. Every per-asset stage runs `JOBS` assets in parallel, one
process each, thread caps at one. Every asset folder describes itself in
`<TICKER>_README.md`. Full methodology:
[module_ml/skills/methodology_ml.md](module_ml/skills/methodology_ml.md).
