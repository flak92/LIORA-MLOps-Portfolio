# LIORA - MLOps - Portfolio

**A reproducible based on 1-minute Time Frame as the raw crypto market-data pipeline: Binance + Bybit klines → QC Lean raw ZIPs → primary-failover consolidation in DuckDB → continuous canonical per-asset Parquet → static monitoring dashboard.**

The governing contract — minimalism, minimum requirements, KISS/YAGNI/DRY/SOLID,
UCAS, pipeline-first — lives in [AGENTS.md](AGENTS.md); project-specific agent
skills in [Skills_For_The_Project/](Skills_For_The_Project/). The working path
through the repo is `AGENTS.md → module names → Skills_For_The_Project → code`;
this README is the general overview.

```
Binance API ──> raw_downloaded_1m_data/cryptofuture/binance/...         ─┐
(keyless, stdlib)      QC Lean ZIPs, 1 full UTC day = 1 zip              ├─> db/1m_raw_data_db.duckdb
                                                                         │   ohlcv_1m_binance
Bybit API ───> raw_downloaded_1m_data/cryptofuture/bybit/...            ─┘   ohlcv_1m_bybit
(keyless, stdlib)      same Lean ZIP format                                  ohlcv_1m_canonical (failover)
                                                                                  │
                                              assets/Asset_<TICKER>/ <────────────┤ export
                                              1m_<TICKER>_data.parquet            │
                                              (continuous t,OHLCV)                v
                                                                    monitoring_module/status.json
                                                                             multiple tabs simple HTML, CSS, JS dashboard
```

## Primary-failover canonical series (why two venues)

Every single exchange feed has occasional missing minutes. Instead of pushing
gap-handling into every downstream indicator, the pipeline consolidates two
independent venues into one canonical series — and **every canonical bar is one
venue's candle copied verbatim**, never a blend: per minute the highest-priority
existing tier wins (traded Binance candle, then traded Bybit candle, then a
valid no-trade candle from either venue in the same order), and only a minute
with no valid candle on both venues is a canonical gap, forward-filled with the
previous close and zero volume. Source shares, source switches, cross-exchange
divergence and every other anomaly are recorded by the monitoring layer and
shown on the dashboard. Downstream ML code reads a continuous `t,O,H,L,C,V`
series whose every printed price existed on a real exchange, and needs no
exchange-specific logic. Full methodology, endpoints and schema:
[DATA_README.md](DATA_README.md).

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
make all              # venv -> download -> ingest -> export -> status -> full ML chain
make dashboard        # serve http://127.0.0.1:8900/  (loopback only)
```

Every stage also runs on its own (`make setup download ingest export status`
for the data half, `make ml-all` for the ML half) — see the stage table below.

The same stages run inside Docker: `make docker-build`, then
`make docker-download / docker-ingest / docker-export / docker-status`,
and `make docker-up` / `make docker-down` for the dashboard container.
Remote machine? Tunnel with `ssh -L 8900:127.0.0.1:8900 <host>`.

## Stages

| Stage     | Command                | Input → Output                                              | Property                          |
|-----------|------------------------|-------------------------------------------------------------|-----------------------------------|
| download  | `make download`        | both APIs → `raw_downloaded_1m_data/.../*_trade.zip`        | idempotent; full UTC days only    |
|           | `make download-binance` / `make download-bybit` | one venue at a time                | independently parallelizable      |
| ingest    | `make ingest`          | ZIPs → venue tables → `ohlcv_1m_canonical` (failover)       | idempotent; deterministic rebuild |
| export    | `make export`          | canonical → `assets/Asset_<T>/1m_<T>_data.parquet`          | atomic write + read-back count    |
| status    | `make status`          | DuckDB → stdout + `monitoring_module/status.json`           | read-only; 3 full scans           |
| dashboard | `make dashboard`       | snapshots → four-tab static page on `127.0.0.1:8900`       | no external resources             |

## Data formats

- **Raw ZIPs** are byte-compatible with the QC Lean `cryptofuture` minute
  format (verified byte-identical against an independent production
  downloader), one tree per venue. Headerless CSV rows:
  `offset_ms_from_utc_midnight,open,high,low,close,volume`.
- **Timestamps** are bar OPEN times, UTC epoch milliseconds, strict 60 000 ms
  grid. **Volume** is base-asset volume, never quote turnover.
- **DuckDB** `db/1m_raw_data_db.duckdb`: `ohlcv_1m_binance`, `ohlcv_1m_bybit`
  (raw), `ohlcv_1m_canonical` (primary-failover, with provenance columns
  `source`, `zero_volume`, `binance_valid`, `bybit_valid`, `rel_divergence`).
- **Parquet** (zstd): pure `timestamp_ms, open, high, low, close, volume` —
  same row count for every asset, continuous, no NULLs, values exactly as the
  winning venue printed them (no rounding at any layer).
- **Semantics**: `1m_<T>_data.parquet` is a **canonical primary-failover
  series**, not the raw feed of a single venue — use it for ML and indicators;
  for Lean backtests use the per-venue raw ZIP trees. Step-by-step build
  description: [DATA_README.md](DATA_README.md).

## Monitoring

`make status` reports the full flow (`zips → venue rows → canonical rows →
parquet rows`) and feeds the dashboard:

- **Pipeline** — canonical rows, real-data share, forward-filled bars and
  Parquet artifacts per asset;
- **Data Quality** — per-venue coverage, gaps, duplicates, OHLC violations and
  zero-volume bars for Binance and Bybit separately, plus canonical-source
  provenance (per-venue shares, forward fills, source switches, the largest 1m
  move at a switch, cross-exchange divergence mean/p99/max).

## ML research layer

`ml_module/` builds — per asset, deterministically — a fixed 15-column hierarchical
feature matrix (15m/1h/4h) **from the canonical series**, triple-barrier
labels resolved on the **Binance** 1-minute path with uniqueness sample
weights, a purged walk-forward protocol with Optuna hyper-parameter search
(XGBoost), a final out-of-sample fold read exactly once, and a top-down gated
strategy evaluation with explicit costs:

```
canonical OHLCV ──► 15m/1h/4h bars ──► X    (market observation)
Kline_1m      ──► triple barrier  ──► Y    (execution)
X + Y ──► purged walk-forward ──► XGBoost ──► probabilities
      ──► fixed strategy rules ──► execution path ──► equity / PnL
```

Observation may use the failover series; execution may not — a position cannot
change exchange because the canonical source switched for one minute. The
decision is taken at a 15m close and filled one minute later. Stages:
`make ml-bars ml-features ml-labels ml-hpo ml-train ml-strategy ml-status`
(or `make ml-all`) — every per-asset stage runs `JOBS = min(cores, available
GiB)` assets in parallel, one process each, with the thread caps pinned at one;
results on the dashboard's **ML Research** tab (ten-asset
cross-section) and **ML Assets** tab, where ticker pills open one asset at a
time in four frames: LABEL, MODEL, STRATEGY, FEATURES. Full methodology:
[ML_README.md](ML_README.md).

