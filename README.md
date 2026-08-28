# LIORA — 1m Crypto Research Pipeline

**Deterministic multi-venue OHLCV research pipeline with purged walk-forward
validation, a frozen final out-of-sample holdout, and a static results dashboard.**

Public market observations → QuantConnect Lean-compatible raw data → one
deterministic canonical DuckDB → features and labels → purged walk-forward
XGBoost → research strategy simulation → monitoring.

The governing contract — minimalism, minimum requirements, KISS/YAGNI/DRY/SOLID,
UCAS, pipeline-first — lives in [AGENTS.md](AGENTS.md); project-specific agent
skills, the naming register and the two methodology documents in
[module_skills/](module_skills/). The working path
through the repo is `AGENTS.md → module names → module_skills → code`;
this README is the general overview.

```
                 ┌── market source A ──┐
MARKET DATA ─────┤                     ├──► NORMALISED RAW 1m OHLCV  (Lean ZIPs)
                 └── market source B ──┘              │
                                                      ▼
                                          ONE CANONICAL DuckDB
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

## Primary-failover canonical series (why two sources)

Every single market feed has occasional missing minutes. Instead of pushing
gap-handling into every downstream indicator, the pipeline consolidates two
independent sources into one canonical series — and **every canonical bar is one
source's candle copied verbatim**, never a blend: per minute the highest-priority
existing tier wins (traded Binance candle, then traded Bybit candle, then a
valid no-trade candle from either source in the same order), and only a minute
with no valid candle on both sources is a canonical gap, forward-filled with the
previous close and zero volume. Source shares, source switches, cross-source
divergence and every other anomaly are recorded by the monitoring layer and
shown on the dashboard. Downstream ML code reads a continuous `t,O,H,L,C,V`
series whose every printed price existed on a real market, and needs no
source-specific logic. Full methodology, endpoints and schema:
[module_skills/methodology_data.md](module_skills/methodology_data.md).

## The basket

Ten assets, uniform market — USDT-margined perpetual futures:

`BTC ETH BNB XRP SOL TRX DOGE ZEC LINK ADA`

The Time window starts at **2021-01-01 00:00 UTC** and ends at the most recent UTC
midnight. Every asset was listed on Binance USDS-M before the window start
(verified by probing each symbol's oldest candle before every download). Bybit
listings partially fall inside the window; pre-listing minutes are simply
Binance-only in the canonical series, which covers the identical
full minute grid — equal row counts by construction.

## Quickstart

Four direct dependencies and nothing else — `duckdb` (storage and query),
`numpy` (mathematics), `optuna` (hyper-parameter search) and `xgboost-cpu`
(model). Anything else in the environment is a transitive dependency of those
four, and the CPU wheel of XGBoost is deliberate: the research layer trains
with `tree_method=hist` and `nthread=1`, so the GPU stack would be weight
without function.

```bash
make all              # venv -> download -> ingest -> status -> full ML chain
make dashboard        # serve http://127.0.0.1:8900/  (loopback only)
```

Every stage also runs on its own (`make setup download ingest status`
for the data half, `make ml-all` for the ML half) — the data stages are in the
table below, the ML chain in *ML research layer*.

The same stages run inside Docker: `make docker-build`, then
`make docker-download / docker-ingest / docker-status` for the
data half and `make docker-ml-all` (or any single `docker-ml-<stage>`) for the
ML half, and `make docker-up` / `make docker-down` for the dashboard container.
Remote machine? Tunnel with `ssh -L 8900:127.0.0.1:8900 <host>`.

## Stages

| Stage     | Command                | Input → Output                                              | Property                          |
|-----------|------------------------|-------------------------------------------------------------|-----------------------------------|
| download  | `make download`        | both APIs → `store_raw_data_ss-01-hh-dd-MM/.../*_trade.zip`        | idempotent; one file per UTC calendar day; post-listing days complete |
|           | `make download-binance` / `make download-bybit` | one source at a time               | independently parallelisable      |
| ingest    | `make ingest`          | ZIPs → raw tables → `ohlcv_1m_canonical` (failover)         | idempotent; deterministic rebuild |
| status    | `make status`          | DuckDB → stdout + `module_monitoring/status.json`           | read-only; 3 full scans           |
| dashboard | `make dashboard`       | snapshots → four-tab static page on `127.0.0.1:8900`       | no external resources             |

## Data formats

- **Raw ZIPs** are byte-compatible with the Lean `cryptofuture` minute
  format (verified byte-identical against an independent production
  downloader), one tree per source. Headerless CSV rows:
  `offset_ms_from_utc_midnight,open,high,low,close,volume`.
- **Timestamps** are bar OPEN times, UTC epoch milliseconds, strict 60 000 ms
  grid. **Volume** is base-asset volume, never quote turnover.
- **DuckDB** `store_db/research_ohlcv.duckdb`: `ohlcv_1m_binance`, `ohlcv_1m_bybit`
  (raw), `ohlcv_1m_canonical` (primary-failover, with provenance columns
  `source`, `zero_volume`, `binance_valid`, `bybit_valid`, `rel_divergence`),
  and the exact aggregations `ohlcv_15m_canonical`, `ohlcv_1h_canonical`,
  `ohlcv_4h_canonical` written by `make ml-bars`.
- **Semantics**: the canonical primary-failover series and its 15m/1h/4h
  aggregations live **only in DuckDB** — the market object every ML stage
  reads. The asset folder carries no price series: its parquets are the
  per-timeframe feature columns. For Lean backtests use the per-source raw
  ZIP trees. Step-by-step build description:
  [module_skills/methodology_data.md](module_skills/methodology_data.md).

## Monitoring

`make status` reports the full flow (`zips → raw rows → canonical rows`) and
feeds the dashboard:

- **Pipeline** — canonical rows, real-data share and forward-filled bars per
  asset;
- **Data Quality** — raw-source coverage, gaps, duplicates, OHLC violations and
  zero-volume bars for each provider separately, then canonical construction:
  primary/secondary/forward-fill shares, source switches, the largest 1m move at
  a switch, cross-source divergence mean/p99/max.

## ML research layer

`module_ml/` builds — per asset, deterministically — a fixed 15-column hierarchical
feature matrix (15m/1h/4h) from the canonical series, triple-barrier
labels resolved on the **canonical** 1-minute path, a purged walk-forward
protocol with average-uniqueness sample weights and Optuna hyper-parameter search
(XGBoost), a final out-of-sample fold that selects nothing, and a top-down gated
strategy evaluation with explicit costs:

Both `X` and `Y` read the canonical series — `X` before the decision, `Y` after
it — so features and target describe the same canonical research object. The
decision is taken at a 15m close and filled one minute later. Stages:
`make ml-bars ml-features ml-labels ml-hpo ml-train ml-strategy ml-status`
(or `make ml-all`) — every per-asset stage runs `JOBS = max(1, min(cores,
available GiB))` assets in parallel, one process each, with the thread caps pinned at one;
results on the dashboard's **ML Research** tab (ten-asset
cross-section) and **ML Assets** tab, where ticker pills open one asset at a
time in four frames: LABEL, MODEL, STRATEGY, FEATURES. Every asset folder also
describes itself: `<TICKER>_parameters.json` records the configuration and the winner
the run used, and its `README.md` says what came out. Full methodology:
[module_skills/methodology_ml.md](module_skills/methodology_ml.md).

