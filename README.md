# LIORA — 1m Crypto Research Pipeline

**Deterministic multi-venue OHLCV research pipeline with purged walk-forward
validation, a frozen final out-of-sample holdout, and a static results dashboard.**

*The repository shows the destination, not the road*.

Public market observations → QuantConnect Lean-compatible raw data → one
deterministic canonical DuckDB per asset → features and labels → purged walk-forward
XGBoost → research strategy simulation → monitoring.

The governing contract — minimalism, minimum requirements, KISS/YAGNI/DRY/SOLID,
UCAS, pipeline-first — lives in [AGENTS.md](AGENTS.md); the naming register, the
two methodology documents and the skills in [module_skills/](module_skills/).
The working path through the repo is `AGENTS.md → module names → module_skills →
code`; this README is the general overview.

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
every printed price existed on a real market. Method, endpoints and schema:
[module_skills/methodology_data.md](module_skills/methodology_data.md).

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

## Quickstart

Four direct dependencies and nothing else — `duckdb` (storage and query),
`numpy` (mathematics), `optuna` (hyper-parameter search) and `xgboost-cpu`
(model); the CPU wheel is deliberate, because the research layer trains with
`tree_method=hist` and `nthread=1`.

```bash
make all          # venv -> data-download -> data-ingest -> data-status -> full ML chain
make docker-up    # build the image, start the dashboard and the asset containers, open http://127.0.0.1:8900/
make docker-all   # the whole chain inside the containers, download to snapshots
make docker-btc-lifecycle  # the same chain, recorded stage by stage into a run directory
```

The dashboard is docker-only: `make docker-up` / `make docker-down`. The stages
run inside Docker too: `docker-data-download`, `docker-data-ingest` and
`docker-data-status` and `docker-ml-<stage>` (or `docker-ml-all`), and `docker-all` runs
the whole chain. Every per-asset stage runs inside that asset's own resident
container, `asset-<ticker>` — one service of `docker-compose.yml` per ticker of the
basket, under the anchor it shares with the dashboard, one image for all; `make docker-up` starts
the dashboard and the residents, each answering the dashboard's proxy with its
data, its artifacts and its own memory and CPU. The stage order is the Makefile's `all:`
and `ml-all:`; every document points there. Remote machine? Tunnel with
`ssh -L 8900:127.0.0.1:8900 <host>`.

## Stages

| Stage     | Command                | Input → Output                                              | Property                          |
|-----------|------------------------|-------------------------------------------------------------|-----------------------------------|
| download  | `make data-download`   | both APIs → `store_raw_1m/.../*_trade.zip`        | idempotent; one file per UTC calendar day; post-listing days complete |
| ingest    | `make data-ingest`     | ZIPs → raw tables → `ohlcv_1m_canonical` (failover)         | idempotent; deterministic rebuild, one asset at a time |
| status    | `make data-status`     | DuckDB → stdout + `module_monitoring/data_status.json`           | read-only; per asset, three scans + three per-symbol passes |
| lifecycle | `make docker-btc-lifecycle` | one recorded run of the whole chain → `store_run_records/<run_id>/` | one record for the whole basket; every stage wrapped by `module_monitoring/record.py`; exact per-stage CPU and peak RSS from `wait4` rusage |
| dashboard | `make docker-up`       | snapshots → five-tab page on `127.0.0.1:8900`, served by `module_monitoring/serve.py` in the `dashboard` container with the container routes | no external resources; the asset containers are reached only through its proxy |

## Data formats

Raw ZIPs are the Lean `cryptofuture` minute format, one tree per venue,
headerless `offset_ms_from_utc_midnight,open,high,low,close,volume`; timestamps
are bar-open UTC epoch milliseconds on a strict 60 000 ms grid, volume is
base-asset volume. The canonical series and its 15m/1h/4h aggregations live only
in `store_assets_artifacts/<TICKER>/<TICKER>_research_ohlcv.duckdb`; the
folder's parquets are feature columns, not prices. For Lean backtests use the
raw ZIP trees. Schema: [module_skills/methodology_data.md](module_skills/methodology_data.md) § 5.

## Dashboard

- **Pipeline** — canonical rows, real-data share and forward-filled bars per asset;
- **Data Quality** — raw-source coverage, gaps, duplicates, OHLC violations and
  zero-volume bars per provider, then canonical construction: source shares,
  switches, the largest 1m move at a switch, cross-source divergence;
- **ML Research** — the cross-section of every asset's result;
- **ML Assets** — one asset at a time in four frames: LABEL, MODEL, STRATEGY, FEATURES;
- **Lifecycle** — one recorded run end to end: what ran, in which container, as
  which PID, for how long, at what CPU and peak resident set, what bytes it moved
  and what it left on disk; then one shared timeline with a dashed rule at every
  stage boundary. A `process_` column is the stage; a `container_` column is the
  whole container over the same window, and the page says so;
- **Containers** — one row per asset container, live through the dashboard's
  proxy: up or down, up since, memory against its ceiling, peak, CPU share over
  the last poll, the observation lag and the measurement age; then one
  container as it reports itself.

## ML research layer

`module_ml/` builds, per asset and deterministically, a fixed 15-column
hierarchical feature matrix (15m/1h/4h) from the canonical series,
triple-barrier labels resolved on the canonical 1-minute path, a purged
walk-forward protocol with average-uniqueness weights and an Optuna search over
XGBoost, a final out-of-sample fold that selects nothing, and a top-down gated
strategy with explicit costs. The decision is taken at a 15m close and filled
one minute later. Every per-asset stage runs `JOBS` assets in parallel, one
process each, thread caps at one. Every asset folder describes itself in
`<TICKER>_README.md`. Full methodology:
[module_skills/methodology_ml.md](module_skills/methodology_ml.md).
