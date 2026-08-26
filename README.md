# LIORA - MLOps - Portfolio

**A reproducible 1-minute crypto market-data pipeline: Binance USDS-M + Bybit Linear klines → QC Lean raw ZIPs → cross-exchange fusion in DuckDB → continuous canonical per-asset Parquet → static monitoring dashboard.**

> Design rule: deterministic and minimal. No API keys, no hidden state, one
> mathematical rule instead of hand-written exceptions. Anyone who clones this
> repository can rebuild the entire dataset from the public exchange APIs with
> four make targets. Data anomalies are a DATA INGEST problem, not an
> RSI/LSTM/XGBoost problem.

```
Binance USDS-M API ──> raw_downloaded_1m_data/cryptofuture/binance/...  ─┐
(keyless, stdlib)      QC Lean ZIPs, 1 full UTC day = 1 zip              ├─> db/1m_raw_data_db.duckdb
                                                                         │   ohlcv_1m_binance
Bybit Linear API ───> raw_downloaded_1m_data/cryptofuture/bybit/...   ───┘   ohlcv_1m_bybit
(keyless, stdlib)      same Lean ZIP format                                  ohlcv_1m_canonical (fusion)
                                                                                  │
                                              assets/Asset_<TICKER>/ <────────────┤ export
                                              1m_<TICKER>_data.parquet            │
                                              (continuous t,OHLCV)                v
                                                                             dashboard/status.json
                                                                             two-tab HTML dashboard
```

## Cross-exchange fusion (why two venues)

Every single exchange feed has occasional missing minutes. Instead of pushing
gap-handling into every downstream indicator, the pipeline consolidates two
independent venues into one canonical series: per minute, venue OHLC prices are
weighted by their USDT notional (dollar-volume) proxy `q = close x base_volume`,
base volumes are summed, a minute missing on one venue takes the other venue
with unit weight, and only a minute missing on **both** venues is a canonical
gap — deterministically forward-filled with the previous close and zero volume.
Availability, cross-exchange divergence and every other anomaly is recorded by
the monitoring layer and shown on the dashboard. Downstream ML code reads a
continuous `t,O,H,L,C,V` series and needs no exchange-specific logic. Full
methodology, endpoints and schema: [DATA_README.md](DATA_README.md).

## The basket

Ten assets, uniform market — USDT-margined perpetual futures:

`BTC ETH BNB XRP SOL TRX DOGE ZEC LINK ADA`

The window starts at **2021-01-01 00:00 UTC** and ends at the most recent UTC
midnight. Every asset was listed on Binance USDS-M before the window start
(verified by probing each symbol's oldest candle before every download). Bybit
listings partially fall inside the window; pre-listing minutes are simply
Binance-only in the fusion. Every asset's canonical series covers the identical
full minute grid — equal row counts by construction.

## Quickstart

```bash
make setup            # create .venv with pinned DuckDB
make download         # backfill/top-up raw 1m ZIPs from both exchanges
make ingest           # load ZIPs into DuckDB, rebuild the canonical series
make export           # write per-asset Parquet files
make status           # quality monitoring -> stdout + dashboard/status.json
make dashboard        # serve http://127.0.0.1:8900/  (loopback only)
```

The same stages run inside Docker: `make docker-build`, then
`make docker-download / docker-ingest / docker-export / docker-status`,
and `make docker-up` / `make docker-down` for the dashboard container.
Remote machine? Tunnel with `ssh -L 8900:127.0.0.1:8900 <host>`.

## Stages

| Stage     | Command                | Input → Output                                              | Property                          |
|-----------|------------------------|-------------------------------------------------------------|-----------------------------------|
| download  | `make download`        | both APIs → `raw_downloaded_1m_data/.../*_trade.zip`        | idempotent; full UTC days only    |
|           | `make download-binance` / `make download-bybit` | one venue at a time                | independently parallelizable      |
| ingest    | `make ingest`          | ZIPs → venue tables → `ohlcv_1m_canonical` (fusion)         | idempotent; deterministic rebuild |
| export    | `make export`          | canonical → `assets/Asset_<T>/1m_<T>_data.parquet`          | atomic write + read-back count    |
| status    | `make status`          | DuckDB → stdout tables + `dashboard/status.json`            | read-only; 3 full scans           |
| dashboard | `make dashboard`       | `status.json` → two-tab static page on `127.0.0.1:8900`     | no external resources             |

## Data formats

- **Raw ZIPs** are byte-compatible with the QC Lean `cryptofuture` minute
  format (verified byte-identical against an independent production
  downloader), one tree per venue. Headerless CSV rows:
  `offset_ms_from_utc_midnight,open,high,low,close,volume`.
- **Timestamps** are bar OPEN times, UTC epoch milliseconds, strict 60 000 ms
  grid. **Volume** is base-asset volume, never quote turnover.
- **DuckDB** `db/1m_raw_data_db.duckdb`: `ohlcv_1m_binance`, `ohlcv_1m_bybit`
  (raw), `ohlcv_1m_canonical` (fused, with provenance columns `src_count`,
  `is_ffill`, `rel_divergence`, `w_binance`).
- **Parquet** (zstd): pure `timestamp_ms, open, high, low, close, volume` —
  same row count for every asset, continuous, no NULLs, prices rounded to the
  instrument tick (+1 guard digit).
- **Semantics**: `1m_<T>_data.parquet` is a **canonical two-venue index**, not
  "Binance data" — use it for ML and indicators; for Lean backtests use the
  per-venue raw ZIP trees. Step-by-step build description:
  [DATA_README.md](DATA_README.md).

## Monitoring

`make status` reports the full flow (`zips → venue rows → canonical rows →
parquet rows`) and feeds the two-tab dashboard:

- **Pipeline** — canonical rows, real-data share, forward-filled bars and
  Parquet artifacts per asset;
- **Data Quality** — per-venue coverage, gaps, duplicates, OHLC violations and
  zero-volume bars for Binance and Bybit separately, plus fusion provenance
  (both-venue share, single-venue shares, forward-fills, cross-exchange
  divergence mean/p99/max).

## Roadmap

- [x] Reproducible two-venue download → DuckDB fusion → Parquet pipeline
- [x] Canonical continuous series (no downstream gap handling)
- [x] Two-tab static monitoring dashboard
- [ ] Scheduled top-ups (the download stages are already incremental)
- [ ] ML feature layers on top of the canonical Parquet files
- [ ] Dashboard history (trend of completeness over time)
